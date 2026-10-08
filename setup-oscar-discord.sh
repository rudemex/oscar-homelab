#!/usr/bin/env bash

set -euo pipefail

# ============================================================
# O.S.C.A.R. Discord Bootstrap
# ============================================================
#
# Required:
#   DISCORD_BOT_TOKEN
#   DISCORD_GUILD_ID
#
# Usage:
#   export DISCORD_BOT_TOKEN="..."
#   export DISCORD_GUILD_ID="..."
#   ./setup-oscar-discord.sh               # crea lo que falte, nunca borra nada
#   ./setup-oscar-discord.sh --dry-run     # igual, pero solo muestra CREATE/KEEP, sin tocar Discord
#   ./setup-oscar-discord.sh --cleanup             # además borra categorías/canales no declarados en discord-channels.json
#   ./setup-oscar-discord.sh --cleanup --dry-run   # muestra CREATE/KEEP/DELETE sin tocar Discord
#
# La estructura declarativa vive en discord-channels.json (mismo
# directorio que este script). Ver docs/servicios/discord.md para
# la documentación completa.
#
# Dependencies:
#   curl
#   jq
#
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/discord-channels.json"
API="https://discord.com/api/v10"
MAX_RETRIES=5

DRY_RUN=false
CLEANUP=false

usage() {
  cat <<'EOF'
Uso: ./setup-oscar-discord.sh [--dry-run] [--cleanup]

  (sin flags)       crea las categorías/canales declarados que falten. Nunca borra nada.
  --dry-run         muestra qué se crearía (y qué se borraría si --cleanup también está
                     presente) sin modificar el servidor.
  --cleanup         además de crear lo que falte, borra categorías/canales de texto o voz
                     que existan en el servidor pero no estén declarados en
                     discord-channels.json. Requiere este flag explícito: sin él, el
                     script nunca borra nada.
  -h, --help        muestra esta ayuda.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --cleanup) CLEANUP=true ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "ERROR: argumento desconocido: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

: "${DISCORD_BOT_TOKEN:?DISCORD_BOT_TOKEN is required}"
: "${DISCORD_GUILD_ID:?DISCORD_GUILD_ID is required}"

AUTH="Authorization: Bot ${DISCORD_BOT_TOKEN}"
JSON="Content-Type: application/json"

command -v curl >/dev/null || {
  echo "ERROR: curl is required"
  exit 1
}

command -v jq >/dev/null || {
  echo "ERROR: jq is required"
  exit 1
}

[[ -f "$CONFIG_FILE" ]] || {
  echo "ERROR: no se encontró $CONFIG_FILE"
  exit 1
}

jq empty "$CONFIG_FILE" || {
  echo "ERROR: $CONFIG_FILE no es JSON válido"
  exit 1
}

echo
echo "========================================="
echo "      O.S.C.A.R. Discord Bootstrap"
echo "========================================="
if [[ "$DRY_RUN" == "true" ]]; then
  echo "(modo --dry-run: no se modifica Discord)"
fi
if [[ "$CLEANUP" == "true" ]]; then
  echo "(modo --cleanup: se borrará lo no declarado en discord-channels.json)"
fi
echo


# ------------------------------------------------------------
# Wrapper único para la API de Discord: maneja 429 (rate limit)
# leyendo retry_after del body y reintentando, en vez de abortar
# todo el bootstrap o depender de sleeps arbitrarios.
# ------------------------------------------------------------

discord_api() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local url="${API}${path}"
  local attempt=0

  while true; do
    local tmp_body http_code body
    tmp_body=$(mktemp)

    if [[ -n "$data" ]]; then
      http_code=$(curl -sS -o "$tmp_body" -w '%{http_code}' \
        -X "$method" -H "$AUTH" -H "$JSON" "$url" -d "$data")
    else
      http_code=$(curl -sS -o "$tmp_body" -w '%{http_code}' \
        -X "$method" -H "$AUTH" "$url")
    fi

    body=$(cat "$tmp_body")
    rm -f "$tmp_body"

    if [[ "$http_code" == "429" ]]; then
      attempt=$((attempt + 1))

      if (( attempt > MAX_RETRIES )); then
        echo "ERROR: rate limited (429) por Discord tras $MAX_RETRIES reintentos en $method $path" >&2
        echo "$body" >&2
        return 1
      fi

      local retry_after wait_for
      retry_after=$(echo "$body" | jq -r '.retry_after // 1')
      wait_for=$(awk "BEGIN { print ${retry_after} + 0.25 }")

      echo "  ! Rate limited (429) en $method $path — esperando ${wait_for}s (intento $attempt/$MAX_RETRIES)..." >&2
      sleep "$wait_for"
      continue
    fi

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
      echo "$body"
      return 0
    fi

    echo "ERROR: Discord API $method $path -> HTTP $http_code" >&2
    echo "$body" >&2
    return 1
  done
}


# ------------------------------------------------------------
# Test authentication
# ------------------------------------------------------------

echo "→ Testing Discord authentication..."

BOT=$(discord_api GET "/users/@me") || exit 1
BOT_NAME=$(echo "$BOT" | jq -r '.username')

echo "  ✓ Authenticated as: $BOT_NAME"


# ------------------------------------------------------------
# Verify guild
# ------------------------------------------------------------

echo "→ Checking server..."

GUILD=$(discord_api GET "/guilds/${DISCORD_GUILD_ID}") || exit 1
GUILD_NAME=$(echo "$GUILD" | jq -r '.name')

echo "  ✓ Server: $GUILD_NAME"


# ------------------------------------------------------------
# Get current channels
# ------------------------------------------------------------

refresh_channels() {
  CHANNELS=$(discord_api GET "/guilds/${DISCORD_GUILD_ID}/channels") || exit 1
}

refresh_channels


# ------------------------------------------------------------
# Lookups contra el snapshot actual de CHANNELS
#
# Discord channel type: 4 = Category, 0 = Text, 2 = Voice
# ------------------------------------------------------------

get_category_id() {
  echo "$CHANNELS" | jq -r \
    --arg NAME "$1" \
    '.[] | select(.type == 4 and .name == $NAME) | .id' \
    | head -1
}

get_channel_id() {
  echo "$CHANNELS" | jq -r \
    --arg NAME "$1" \
    --arg PARENT "$2" \
    '.[] |
     select(.type == 0 and .name == $NAME and .parent_id == $PARENT) |
     .id' \
    | head -1
}


# ------------------------------------------------------------
# Reconcile: crea (o, en --dry-run, solo muestra) las categorías
# y canales declarados en discord-channels.json que falten.
# Nunca borra nada — eso es responsabilidad de --cleanup.
# ------------------------------------------------------------

reconcile() {
  local cat_names
  cat_names=$(jq -r '.categories | keys[]' "$CONFIG_FILE")

  while IFS= read -r cat_name; do
    [[ -z "$cat_name" ]] && continue

    echo
    echo "$cat_name"

    local cat_id
    cat_id=$(get_category_id "$cat_name")

    if [[ -n "$cat_id" ]]; then
      if [[ "$DRY_RUN" == "true" ]]; then
        echo "  KEEP   (categoría) $cat_name"
      else
        echo "  = Category already exists: $cat_name"
      fi
    else
      if [[ "$DRY_RUN" == "true" ]]; then
        echo "  CREATE (categoría) $cat_name"
      else
        echo "  + Creating category: $cat_name"
        local payload result
        payload=$(jq -n --arg name "$cat_name" '{name: $name, type: 4}')
        result=$(discord_api POST "/guilds/${DISCORD_GUILD_ID}/channels" "$payload") || exit 1
        cat_id=$(echo "$result" | jq -r '.id')
        refresh_channels
      fi
    fi

    local chan_rows
    chan_rows=$(jq -r --arg cat "$cat_name" '.categories[$cat][] | [.name, .topic] | @tsv' "$CONFIG_FILE")

    while IFS=$'\t' read -r chan_name chan_topic; do
      [[ -z "$chan_name" ]] && continue

      if [[ "$DRY_RUN" == "true" ]]; then
        local chan_id=""
        if [[ -n "$cat_id" ]]; then
          chan_id=$(get_channel_id "$chan_name" "$cat_id")
        fi
        if [[ -n "$chan_id" ]]; then
          echo "    KEEP   #$chan_name"
        else
          echo "    CREATE #$chan_name"
        fi
      else
        local chan_id
        chan_id=$(get_channel_id "$chan_name" "$cat_id")

        if [[ -n "$chan_id" ]]; then
          echo "  = Channel already exists: #$chan_name"
        else
          echo "  + Creating channel: #$chan_name"
          local payload result
          payload=$(jq -n \
            --arg name "$chan_name" \
            --arg topic "$chan_topic" \
            --arg parent "$cat_id" \
            '{name: $name, type: 0, topic: $topic, parent_id: $parent}')
          result=$(discord_api POST "/guilds/${DISCORD_GUILD_ID}/channels" "$payload") || exit 1
          refresh_channels
        fi
      fi
    done <<< "$chan_rows"

  done <<< "$cat_names"
}


# ------------------------------------------------------------
# Cleanup: compara el servidor contra discord-channels.json y
# borra (o, en --dry-run, solo muestra) categorías/canales que
# existan en Discord pero no estén declarados. Solo se llama si
# el usuario pasó --cleanup explícitamente.
# ------------------------------------------------------------

compute_and_apply_cleanup() {
  refresh_channels

  local desired_cats desired_keys cat_id_name
  desired_cats=$(jq -r '.categories | keys[]' "$CONFIG_FILE")
  desired_keys=$(jq -r '.categories | to_entries[] | .key as $c | .value[] | ($c + "|" + .name)' "$CONFIG_FILE")
  cat_id_name=$(echo "$CHANNELS" | jq -c '[.[] | select(.type == 4) | {id, name}]')

  echo
  echo "Cleanup: comparando estructura declarada contra el servidor..."
  echo

  local found_any=false

  while IFS=$'\t' read -r id type name parent_id; do
    [[ -z "$id" ]] && continue

    local is_desired=false
    local label display

    if [[ "$type" == "4" ]]; then
      label="category"
      display="$name"
      if printf '%s\n' "$desired_cats" | grep -qxF "$name"; then
        is_desired=true
      fi
    elif [[ "$type" == "0" ]]; then
      label="text"
      display="#$name"
      local pname key
      pname=$(echo "$cat_id_name" | jq -r --arg pid "$parent_id" '.[] | select(.id == $pid) | .name' | head -1)
      key="${pname}|${name}"
      if printf '%s\n' "$desired_keys" | grep -qxF "$key"; then
        is_desired=true
      fi
    else
      label="voice"
      display="#$name (voice)"
      is_desired=false
    fi

    if [[ "$is_desired" == "true" ]]; then
      continue
    fi

    found_any=true

    if [[ "$DRY_RUN" == "true" ]]; then
      echo "  DELETE ($label) $display"
    else
      echo "  - Deleting ($label): $display"
      discord_api DELETE "/channels/${id}" >/dev/null || true
    fi
  done < <(echo "$CHANNELS" | jq -r '.[] | select(.type == 4 or .type == 0 or .type == 2) | [.id, (.type | tostring), .name, (.parent_id // "")] | @tsv')

  if [[ "$found_any" == "false" ]]; then
    echo "  (nada para borrar — el servidor ya coincide con discord-channels.json)"
  fi
}


# ============================================================
# Run
# ============================================================

reconcile

if [[ "$CLEANUP" == "true" ]]; then
  compute_and_apply_cleanup
fi


# ============================================================
# Finished
# ============================================================

echo
echo "========================================="
if [[ "$DRY_RUN" == "true" ]]; then
  echo "       O.S.C.A.R. dry-run complete"
else
  echo "       O.S.C.A.R. setup complete"
fi
echo "========================================="
echo
echo "Server: $GUILD_NAME"
echo "Bot:    $BOT_NAME"
echo
echo "Structure (declarada en discord-channels.json):"
echo
jq -r '
  .categories | to_entries[] |
  "\(.key)\n" + (.value | map("   #" + .name) | join("\n")) + "\n"
' "$CONFIG_FILE"
