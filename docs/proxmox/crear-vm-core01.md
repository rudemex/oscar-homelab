---
title: Crear VM core01
sidebar_position: 7
---

# VM `core01`

`core01` será el primer host Linux de aplicaciones Docker.

## Sizing inicial

Con el Dell aún en 16 GB RAM:

```text
vCPU: 2
RAM: 4 GB
Disk: 60 GB (expandible)
NIC: VirtIO
```

No asignar toda la RAM física entre VMs; Proxmox y filesystem necesitan margen.

## Desde template

1. clonar template Cloud-Init;
2. nombre `core01`;
3. asignar IP/reservation;
4. inyectar SSH public key;
5. iniciar;
6. validar qemu-guest-agent.

## Baseline Linux

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y ca-certificates curl git vim jq qemu-guest-agent
sudo systemctl enable --now qemu-guest-agent
```

## Docker

Instalar Docker Engine usando el repositorio oficial para la distribución elegida. Después:

```bash
docker version
docker compose version
sudo systemctl status docker
```

## Directorios

```bash
sudo mkdir -p /srv/oscar/{apps,data,backup-staging}
sudo chown -R "$USER":"$USER" /srv/oscar
```

Patrón:

```text
/srv/oscar/apps/n8n/compose.yaml
/srv/oscar/apps/uptime-kuma/compose.yaml
/srv/oscar/data/n8n/...
```

## Validación

Desplegar `examples/docker-compose/whoami`, comprobar desde otro cliente y luego destruirlo.

## Snapshot

Una vez validado el baseline y antes de cargar aplicaciones, crear snapshot/backup como punto de recuperación. El snapshot no reemplaza el backup externo.
