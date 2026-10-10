#!/usr/bin/env bash
# Da de alta (o actualiza) un servicio LAN de OSCAR de punta a punta:
#   1. Proxy Host en Nginx Proxy Manager (crea o actualiza, idempotente).
#   2. Rewrite de DNS en AdGuard — delegado a Hermes Agent (nunca toca la
#      credencial de AdGuard directamente, mismo patrón usado para hermes-docs).
#
# Uso:
#   NPM_EMAIL=automation@oscar.home NPM_PASSWORD=*** \
#     ./register-lan-service.sh <hostname> <forward_ip> <forward_port> [esquema]
#
# Ejemplo:
#   ./register-lan-service.sh hermes-docs.oscar.home 192.168.0.154 8085
#
# Variables de entorno:
#   NPM_API_URL   (default: http://192.168.0.156:81)
#   NPM_EMAIL     (requerido)
#   NPM_PASSWORD  (requerido)
#   NPM_TARGET    IP a la que debe apuntar el rewrite de AdGuard (default: 192.168.0.156, NPM)
#   HERMES_NAMESPACE (default: oscar-ai)
#   HERMES_DEPLOYMENT (default: hermes-agent)
#   SKIP_ADGUARD=1  para saltar el paso de AdGuard (por si el rewrite ya existe)

set -euo pipefail

HOSTNAME="${1:?uso: $0 <hostname> <forward_ip> <forward_port> [esquema]}"
FORWARD_IP="${2:?falta forward_ip}"
FORWARD_PORT="${3:?falta forward_port}"
SCHEME="${4:-http}"

NPM_API_URL="${NPM_API_URL:-http://192.168.0.156:81}"
NPM_EMAIL="${NPM_EMAIL:?seteá NPM_EMAIL}"
NPM_PASSWORD="${NPM_PASSWORD:?seteá NPM_PASSWORD}"
NPM_TARGET="${NPM_TARGET:-192.168.0.156}"
HERMES_NAMESPACE="${HERMES_NAMESPACE:-oscar-ai}"
HERMES_DEPLOYMENT="${HERMES_DEPLOYMENT:-hermes-agent}"

echo "==> Autenticando contra NPM ($NPM_API_URL)..."
TOKEN="$(curl -sS -X POST "$NPM_API_URL/api/tokens" \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$NPM_EMAIL\",\"secret\":\"$NPM_PASSWORD\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")"

if [ -z "$TOKEN" ]; then
  echo "No se pudo autenticar contra NPM." >&2
  exit 1
fi

echo "==> Buscando si ya existe un Proxy Host para $HOSTNAME..."
EXISTING_ID="$(curl -sS "$NPM_API_URL/api/nginx/proxy-hosts" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
hosts = json.load(sys.stdin)
host = '$HOSTNAME'
for h in hosts:
    if host in h.get('domain_names', []):
        print(h['id'])
        break
")"

PAYLOAD=$(python3 -c "
import json
print(json.dumps({
    'domain_names': ['$HOSTNAME'],
    'forward_scheme': '$SCHEME',
    'forward_host': '$FORWARD_IP',
    'forward_port': int('$FORWARD_PORT'),
    'access_list_id': 0,
    'certificate_id': 0,
    'ssl_forced': False,
    'caching_enabled': False,
    'block_exploits': True,
    'advanced_config': '',
    'meta': {'letsencrypt_agree': False, 'dns_challenge': False},
    'allow_websocket_upgrade': False,
    'http2_support': False,
    'enabled': True,
    'locations': []
}))
")

if [ -n "$EXISTING_ID" ]; then
  echo "==> Ya existe (id $EXISTING_ID) — actualizando forward_host/forward_port..."
  curl -sS -X PUT "$NPM_API_URL/api/nginx/proxy-hosts/$EXISTING_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" -w "\nHTTP %{http_code}\n"
else
  echo "==> No existía — creando Proxy Host nuevo..."
  curl -sS -X POST "$NPM_API_URL/api/nginx/proxy-hosts" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" -w "\nHTTP %{http_code}\n"
fi

if [ "${SKIP_ADGUARD:-0}" = "1" ]; then
  echo "==> SKIP_ADGUARD=1, no se toca AdGuard."
  exit 0
fi

echo "==> Pidiéndole a Hermes Agent que cree el rewrite de AdGuard ($HOSTNAME -> $NPM_TARGET)..."
kubectl exec -n "$HERMES_NAMESPACE" "deploy/$HERMES_DEPLOYMENT" -- \
  /opt/hermes/.venv/bin/hermes -z "Agregá un DNS rewrite en AdGuard: el dominio $HOSTNAME debe resolver a $NPM_TARGET. Si ya existe un rewrite igual, no lo dupliques. Usá la herramienta de AdGuard para crearlo ahora, no me expliques cómo hacerlo manualmente."

echo "==> Listo. Probá: curl --resolve $HOSTNAME:80:$NPM_TARGET http://$HOSTNAME/"
