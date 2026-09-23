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
RAM: 8 GB
Disk: 60 GB (expandible)
NIC: VirtIO
```

:::caution Corregido tras la experiencia real
Esta página decía 4 GB y una nota de que "no cambia por tener más RAM disponible". Con 9 contenedores reales corriendo (n8n+Postgres, Uptime Kuma, Vaultwarden, Homepage, Beszel hub+agente, Cloudflare Tunnel, Glances) el uso llegó al 91% de 4 GB — nada roto todavía, pero sin margen para nada más. Se subió a 8 GB. La lección real: "VM de servicios livianos" no significa que la suma de varios servicios livianos siga siendo liviana — sí sirve seguir sin inflarla para un solo servicio pesado (eso sí ameritaría una VM aparte), pero 4 GB se quedó corto para la cantidad de contenedores que terminó acumulando.
:::

No asignar toda la RAM física entre VMs; Proxmox y filesystem necesitan margen.

:::caution IP y VMID corregidos tras la experiencia real (2026-09-15)
Esta página usaba `qm clone 9000 101 ...` y `192.168.20.11/24` (el rango `SERVERS` del [plan de direccionamiento](../red/plan-direccionamiento.md) con VLANs) — ninguno de los dos es lo que terminó pasando. **VLANs y segmentación son objetivo, no están implementadas hoy** (ver [migración a red segmentada](../red/migracion-a-red-segmentada.md), "Estado A: red actual" — sigue siendo un único `192.168.0.0/24` plano, sin VLANs, sobre el router de fábrica). Y el VMID `101` terminó ocupado por `haos-18.2` (Home Assistant), no por `core01`. Los valores de abajo son los reales, verificados con `qm config` contra `oscar-core` — no un ejemplo.
:::

## VMs reales (tabla de referencia)

Las tres VMs de aplicación se crearon con el mismo procedimiento, solo cambia VMID/nombre/IP/sizing. Esta página desarrolla el paso a paso completo con `core01` como ejemplo; para `k3s01`/`devops01` alcanza con repetir los mismos pasos sustituyendo estos valores:

| VM | VMID | IP | vCPU | RAM | Rol |
|---|---|---|---|---|---|
| `core01` | 102 | `192.168.0.156/24` | 2 | 4 GB | Docker — servicios base (Homepage, NPM, Vaultwarden, Beszel hub, Cloudflare Tunnel, MySpeed, Glances) |
| `k3s01` | 103 | `192.168.0.150/24` | 4 | 4 GB | k3s — Argo CD, apps desplegadas por GitOps |
| `devops01` | 104 | `192.168.0.151/24` | 6 | 6 GB | Docker — Forgejo, Nexus, CI Runner |
| `lab01` | 105 | `192.168.0.152/24` | 4 | 2 GB | Docker — CS2 |
| `automation` | 107 | `192.168.0.153/24` | 2 | 4 GB | Docker — n8n+PostgreSQL |

RAM y sizing bajados el 2026-09-23 (right-sizing del paso 3 de la reorganización del rack — ver `REORGANIZACION_RACK.md`, raíz del repo) — los valores de la sección "Sizing inicial" de esta página quedaron como estaban para `core01` a modo de ejemplo histórico del paso a paso; los reales de las 5 VM están en esta tabla.

Gateway real para las tres: `192.168.0.1`. Ver el detalle de instalación específico de cada una en su propia página de servicio: [Forgejo](../servicios/forgejo.md) documenta la creación de `devops01`, no se repite acá.

## Desde template

Estos comandos corren **en Proxmox** (por SSH o desde su consola web, Shell del nodo). Asumen el template `9000` creado en [templates y Cloud-Init](./templates-cloud-init.md) — si usaste otro VMID de template, reemplazalo. Si nunca generaste una clave SSH, hacelo antes con [herramientas básicas](../primeros-pasos/herramientas-basicas.md#ssh-conectarte-a-otra-máquina): `ssh-keygen -t ed25519`.

```bash
# 1. Clonar el template como VM nueva (clon completo, no linked)
qm clone 9000 102 --name core01 --full

# 2. Asignar la IP fija real (red plana hoy, sin VLANs — ver nota arriba)
qm set 102 --ipconfig0 ip=192.168.0.156/24,gw=192.168.0.1

# 3. DNS — apuntar a AdGuard con fallback, no dejar el default de la imagen
#    (bug real encontrado el 2026-09-16: core01 se creó con 8.8.8.8 fijo y
#    nunca se corrigió hasta que Homepage necesitó resolver *.oscar.home por
#    primera vez, meses después — ningún contenedor del host podía resolver
#    git.oscar.home/nexus.oscar.home hasta entonces)
qm set 102 --nameserver "192.168.0.93 1.1.1.1"

# 4. Inyectar tu clave pública (contenido de ~/.ssh/id_ed25519.pub en TU computadora, no en Proxmox)
qm set 102 --sshkey ~/.ssh/id_ed25519.pub

# 5. Ajustar sizing al de esta página (ver "Sizing inicial" arriba)
qm set 102 --cores 2 --memory 8192

# 5b. Agrandar el disco — el template clona con su tamaño original (~3.5 GB),
#     no el "Disk" de la tabla de sizing. Sin este paso, Docker Engine falla
#     al instalar por falta de espacio (gotcha real, encontrado al crear
#     `automation` el 2026-09-23). Ajustar el "+56G" al tamaño real deseado.
qm resize 102 scsi0 +56G

# 6. Habilitar autostart — si no, la VM no arranca sola cuando reinicia oscar-core
#    (ver "Autostart de VMs" en operacion.md — encontrado como bug real, no estaba seteado)
qm set 102 --onboot 1

# 7. Iniciar
qm start 102
```

**Si la VM ya existe** (como pasó con `core01`, creada antes de que este paso existiera en la guía): el `--nameserver` de Cloud-Init solo aplica en el primer boot. Corregir a mano en `/etc/netplan/50-cloud-init.yaml` (`nameservers.addresses`) y `netplan apply` — no alcanza con `qm set` después de que la VM ya arrancó una vez.

Esperar unos segundos y validar que arrancó y que el guest agent responde:

```bash
qm agent 102 ping
```

Si no responde nada (sin error) en un par de intentos, el guest agent todavía está iniciando dentro de la VM — esperar y reintentar antes de asumir que algo falló.

El `qm resize` del paso 5b agranda el disco virtual, pero la partición y el filesystem de adentro no crecen solos — hacerlo una vez que la VM esté arriba:

```bash
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1
df -h /
```

## Conectarse y actualizar

Desde tu computadora, no desde Proxmox:

```bash
ssh oscar@192.168.0.156
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
