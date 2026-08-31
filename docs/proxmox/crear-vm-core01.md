---
title: Crear VM core01
sidebar_position: 7
---

# VM `core01`

`core01` será el primer host Linux de aplicaciones Docker.

## Sizing inicial

Con el Dell en 32 GB RAM (ver [distribución con 32 GB](../hardware/dell-7060.md#distribución-con-32-gb)):

```text
vCPU: 2
RAM: 4 GB
Disk: 60 GB (expandible)
NIC: VirtIO
```

Este sizing de `core01` no cambia por tener más RAM disponible — sigue siendo la VM de servicios livianos (n8n, Uptime Kuma, dashboards). El margen extra de RAM se usa para sumar VMs nuevas (observabilidad dedicada, k3s con más recursos), no para inflar esta.

No asignar toda la RAM física entre VMs; Proxmox y filesystem necesitan margen.

## Desde template

Estos comandos corren **en Proxmox** (por SSH o desde su consola web, Shell del nodo). Asumen el template `9000` creado en [templates y Cloud-Init](./templates-cloud-init.md) — si usaste otro VMID de template, reemplazalo. Si nunca generaste una clave SSH, hacelo antes con [herramientas básicas](../primeros-pasos/herramientas-basicas.md#ssh-conectarte-a-otra-máquina): `ssh-keygen -t ed25519`.

```bash
# 1. Clonar el template como VM nueva (clon completo, no linked)
qm clone 9000 101 --name core01 --full

# 2. Asignar la IP fija del plan de direccionamiento (ver plan-direccionamiento.md)
qm set 101 --ipconfig0 ip=192.168.20.11/24,gw=192.168.20.1

# 3. Inyectar tu clave pública (contenido de ~/.ssh/id_ed25519.pub en TU computadora, no en Proxmox)
qm set 101 --sshkey ~/.ssh/id_ed25519.pub

# 4. Ajustar sizing al de esta página (ver "Sizing inicial" arriba)
qm set 101 --cores 2 --memory 4096

# 5. Iniciar
qm start 101
```

Esperar unos segundos y validar que arrancó y que el guest agent responde:

```bash
qm agent 101 ping
```

Si no responde nada (sin error) en un par de intentos, el guest agent todavía está iniciando dentro de la VM — esperar y reintentar antes de asumir que algo falló.

## Conectarse y actualizar

Desde tu computadora, no desde Proxmox:

```bash
ssh oscar@192.168.20.11
```

Dentro de la VM:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y ca-certificates curl git nano jq qemu-guest-agent
sudo systemctl enable --now qemu-guest-agent
```

## Instalar Docker

Comandos oficiales de Docker para Ubuntu (repositorio real de `download.docker.com`, no un script de terceros) — correr dentro de `core01`:

```bash
# Agregar la clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Agregar el repositorio de Docker a las fuentes de apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Permitir correr docker sin sudo (cerrar sesión SSH y volver a entrar para que aplique)
sudo usermod -aG docker "$USER"
```

Cerrar la sesión SSH (`exit`) y volver a conectar para que el grupo `docker` tome efecto, y validar:

```bash
docker version
docker compose version
sudo systemctl status docker --no-pager
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
