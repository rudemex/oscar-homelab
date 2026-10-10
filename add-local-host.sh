#!/usr/bin/env bash
# Agrega un hostname *.oscar.home a /etc/hosts de ESTA máquina.
# Hace falta porque el resolver activo de esta Mac usa DNS público (8.8.8.8/1.1.1.1),
# que no conoce dominios internos — ver docs/red/dns-adguard.md.
# Idempotente: si la entrada ya existe, no la duplica.
#
# Uso:
#   ./add-local-host.sh <hostname> [ip]
#   ip por default: 192.168.0.156 (NPM) — el mismo patrón que git.oscar.home/nexus.oscar.home.
#   Para servicios de k3s (Traefik) usar 192.168.0.150 en su lugar.

set -euo pipefail

HOSTNAME="${1:?uso: $0 <hostname> [ip]}"
IP="${2:-192.168.0.156}"
ENTRY="$IP $HOSTNAME"

if grep -qE "[[:space:]]$HOSTNAME([[:space:]]|$)" /etc/hosts; then
  echo "Ya existe una entrada para $HOSTNAME en /etc/hosts:"
  grep -E "[[:space:]]$HOSTNAME([[:space:]]|$)" /etc/hosts
  echo "No se tocó nada. Editalo a mano si la IP está mal."
  exit 0
fi

echo "Agregando: $ENTRY"
sudo tee -a /etc/hosts > /dev/null <<< "$ENTRY"

sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null || true

echo "Listo. Probando..."
curl -s -o /dev/null -w "http://$HOSTNAME/ -> %{http_code}\n" "http://$HOSTNAME/" || true
