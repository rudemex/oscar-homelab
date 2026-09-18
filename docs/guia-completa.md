---
title: Guía completa
sidebar_position: 3
slug: /guia-completa
---

# Guía completa: armá tu homelab de punta a punta

La [guía rápida](./guia-rapida.md) te lleva de "tengo una compu" a "tengo Proxmox, Docker y un servicio corriendo" en un fin de semana. Esta guía es el paso siguiente: todo lo que hace falta para tener un homelab completo — Git propio, CI/CD, Kubernetes, acceso remoto seguro, automatización del hogar y hasta un servidor de juegos — explicado sin asumir que sos ingeniero de infraestructura.

No hace falta leerla de una sentada. Cada parte se apoya en la anterior, pero podés parar después de cualquiera y tener algo útil funcionando.

:::tip Antes de arrancar
Si todavía no hiciste la [guía rápida](./guia-rapida.md), hacela primero — asume que ya tenés Proxmox instalado y una VM con Docker corriendo.
:::

## Cómo está organizada

| Parte | Qué construís | Por qué en ese orden |
|---|---|---|
| 1 · La base física | Hardware, hypervisor, backup, seguridad mínima | Todo lo demás corre encima de esto — si esto falla, se cae todo junto |
| 2 · Servicios esenciales | Reverse proxy, monitoreo, contraseñas | Higiene básica antes de sumar más superficie de ataque |
| 3 · Tu plataforma de desarrollo | Git privado, CI/CD, Kubernetes | El corazón "DevOps" del homelab |
| 4 · Acceso y hogar | Acceso remoto, Home Assistant, juegos | Lo que hace que el homelab se sienta tuyo, no solo un laboratorio |

Cada sección tiene un link "para profundizar" hacia la documentación técnica completa — esta guía te da el camino recto, esa documentación tiene todos los detalles, casos borde y decisiones de diseño.

---

# Parte 1 · La base física

## 1. Elegí y dimensioná tu hardware

No hace falta hardware carísimo. Lo que sí importa es dimensionar bien para lo que vas a correr:

| Rol | Mínimo razonable | Notas |
|---|---|---|
| Hypervisor (Proxmox) | 4 hilos de CPU con virtualización, 16 GB RAM, 250 GB SSD/NVMe | Un mini PC de oficina descartado o un NUC alcanzan de sobra |
| Red | Ethernet cableado, no Wi-Fi | El servidor va cableado siempre |
| Backup | Un segundo disco o destino de red, aparte del principal | Ver el paso 4 — no es opcional |

El detalle completo, desglosado por rol (Docker, Kubernetes, observabilidad) para cuando quieras crecer en serio, está en [requisitos mínimos](./referencia/requisitos-minimos.md) — es la referencia real, no una lista de compras de nadie en particular.

## 2. Instalá el hypervisor

[Proxmox VE](https://www.proxmox.com/) convierte tu máquina en un servidor capaz de correr varias VMs. Los pasos base ya están en la [guía rápida](./guia-rapida.md#paso-1--instalar-proxmox) — acá el agregado es pensar en términos de **varias VMs con roles separados**, no una sola VM que hace todo:

| VM | Rol | Por qué separada |
|---|---|---|
| `core` | Servicios base: reverse proxy, monitoreo, contraseñas, automatización | Si se cae, no se lleva puesto tu Git ni tu CI |
| `devops` | Git, registry de imágenes, CI/CD | Carga de I/O y actualizaciones distintas al resto |
| `k3s` | Kubernetes | Aislado — un experimento roto ahí no afecta lo demás |

No hace falta crear las tres el primer día. Podés arrancar con una sola VM (la de la guía rápida) e ir separando cuando sientas que un servicio pesado le está robando recursos a otro — la separación es una decisión de higiene, no un requisito técnico del día uno.

**Para profundizar:** [instalación de Proxmox](./proxmox/instalacion.md), [storage](./proxmox/storage.md), [VM vs LXC](./proxmox/vm-vs-lxc.md).

### Cloud-Init: crear VMs sin repetir el instalador a mano

Si vas a crear varias VMs (una por rol), armar un *template* una sola vez te ahorra repetir el instalador de Ubuntu cada vez:

```bash
# 1. Descargar la cloud image oficial de Ubuntu Server
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img -O /var/lib/vz/template/iso/noble-cloudimg.qcow2

# 2. Crear la VM base (sin disco todavía)
qm create 9000 \
  --name ubuntu-2404-cloudinit-tpl \
  --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-pci \
  --ostype l26

# 3. Importar el disco de la cloud image
qm importdisk 9000 noble-cloudimg.qcow2 local-lvm
qm set 9000 --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot order=scsi0
qm set 9000 --serial0 socket --vga serial0

# 4. Usuario y clave SSH por defecto de la plantilla
qm set 9000 --ciuser tuusuario --sshkey ~/.ssh/id_ed25519.pub
qm set 9000 --ipconfig0 ip=dhcp

# 5. DNS — apuntalo a algo confiable desde el día uno (ver nota abajo)
qm set 9000 --nameserver "1.1.1.1"

# 6. Convertir en template
qm template 9000
```

Después, cada VM nueva es un clon completo (no *linked*, para no depender del template en producción):

```bash
qm clone 9000 <vmid-nuevo> --name <nombre> --full
qm set <vmid-nuevo> --ipconfig0 ip=<ip-fija>/24,gw=<tu-gateway>
qm set <vmid-nuevo> --cores <n> --memory <mb>
qm set <vmid-nuevo> --onboot 1
qm start <vmid-nuevo>
```

:::caution Dos cosas que se pagan caro si se saltean
- **`--onboot 1` en cada VM**: sin esto, si el hypervisor se reinicia (corte de luz, update), las VMs quedan apagadas hasta que las prendas a mano — aunque todo adentro esté configurado para levantar solo.
- **DNS del template**: si no lo fijás acá, cada VM nueva hereda el default de la imagen (a veces un DNS que no es el tuyo). Corregirlo después de que la VM ya arrancó una vez requiere editar `/etc/netplan/` a mano en cada una — mucho más trabajo que fijarlo una vez en el template.
:::

**Para profundizar:** [templates y Cloud-Init](./proxmox/templates-cloud-init.md), [autostart de VMs](./proxmox/operacion.md#autostart-de-vms-onboot).

## 3. Backup mínimo viable — antes de seguir, no al final

Es tentador dejar el backup para "cuando tenga algo importante que perder". El problema es que para cuando lo notás, ya es tarde. Un backup automático mínimo lleva minutos de configurar:

Desde la consola de Proxmox: `Datacenter → Backup → Add` — programá un job que corra de noche, sobre todas las VMs (`all:1`, así cualquier VM nueva se suma sola sin tocar el job de nuevo), modo snapshot, comprimido, con una retención razonable (ej. últimos 5 + 1 mensual).

La regla real detrás de esto es **3-2-1**: 3 copias, en 2 medios distintos, con 1 copia fuera del lugar físico. Un backup que vive en el mismo disco/máquina que respalda no protege contra la falla que más importa — que se rompa el equipo entero. No hace falta resolver la copia off-site el primer día, pero sí saber que es una brecha real hasta que la resuelvas.

**Para profundizar:** [backups en Proxmox](./proxmox/backups.md), [estrategia 3-2-1](./backup-dr/estrategia-321.md), [matriz de qué respaldar](./backup-dr/matriz-backup.md).

## 4. Seguridad base de cada VM

Antes de exponer cualquier cosa — ni siquiera a tu propia LAN — cuatro hábitos que cuestan poco y evitan la mayoría de los problemas reales:

- **SSH por clave, nunca por password.** Se configura una vez en el template (paso anterior) y listo para todas las VMs que salgan de ahí.
- **Actualizaciones del sistema al día** (`apt update && apt full-upgrade`), no solo el día que se crea la VM.
- **Ningún panel de administración expuesto directo a Internet** — ni Proxmox, ni Portainer, ni nada que tenga acceso de escritura a tu infraestructura. Esto se resuelve solo en la Parte 4 (acceso remoto), pero es la regla a tener en la cabeza desde ahora.
- **Un gestor de contraseñas propio** para las credenciales que vas generando (llega en el paso 7) — nunca la misma contraseña reciclada entre servicios.

**Para profundizar:** [hardening de Linux](./seguridad/hardening-linux.md), [manejo de secretos](./seguridad/secretos.md), [exposición a Internet](./seguridad/exposicion-internet.md), [modelo de amenazas](./seguridad/modelo-amenazas.md).

---

# Parte 2 · Servicios esenciales

## 5. Reverse proxy y DNS interno

A medida que sumás servicios, vas a querer acceder a cada uno por un nombre (`git.tuhomelab.local`) en vez de recordar `192.168.0.x:puerto` para cada cosa. Un reverse proxy con UI propia resuelve esto sin escribir configuración de nginx a mano.

**Nginx Proxy Manager** es liviano y tiene panel web:

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      - "80:80"
      - "81:81"
      - "443:443"
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
```

Primer login en `http://<ip-de-la-vm>:81` con las credenciales de fábrica del proyecto (cambiarlas inmediatamente), y desde ahí cada "Proxy Host" nuevo es: dominio interno → IP:puerto del servicio real.

Para que `git.tuhomelab.local` resuelva de verdad en tu red, necesitás algo de DNS interno — **AdGuard Home** (o Pi-hole) cumple ese rol además de bloquear publicidad: instalalo, y agregale una entrada "DNS rewrite" por cada hostname interno que crees.

**Para profundizar:** [Nginx Proxy Manager](./servicios/nginx-proxy-manager.md), [DNS con AdGuard Home](./red/dns-adguard.md).

## 6. Monitoreo básico y un dashboard central

Dos piezas chicas que dan mucho valor por poco esfuerzo:

**Uptime Kuma** — te avisa cuando algo se cae:

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    restart: unless-stopped
    volumes:
      - uptime-kuma-data:/app/data
    ports:
      - "3001:3001"
volumes:
  uptime-kuma-data:
```

Primer acceso crea el admin, y desde ahí agregás un monitor HTTP/TCP por cada servicio real que vayas sumando — a medida que crece el homelab, este paso se vuelve automático.

**Homepage** — un dashboard central con link y estado de todo, para no tener que recordar 15 puertos distintos:

```yaml
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    restart: unless-stopped
    volumes:
      - ./config:/app/config
    ports:
      - "3000:3000"
```

Se configura editando `config/services.yaml` — un servicio, un bloque YAML con nombre, link y (opcional) un widget que le pega a la API del servicio para mostrar datos en vivo.

**Para profundizar:** [Uptime Kuma](./servicios/uptime-kuma.md), [Homepage](./servicios/homepage.md).

## 7. Tu propio gestor de contraseñas

Antes de seguir generando credenciales para cada servicio nuevo (y vas a generar muchas), tené un lugar propio para guardarlas. **Vaultwarden** es un servidor compatible con Bitwarden, liviano:

```yaml
services:
  vaultwarden:
    image: vaultwarden/server:latest
    restart: unless-stopped
    environment:
      SIGNUPS_ALLOWED: "false"   # deshabilitar después de crear tu cuenta
    volumes:
      - vw-data:/data
    ports:
      - "127.0.0.1:8080:80"      # nunca expuesto directo a la LAN, ver Parte 4
volumes:
  vw-data:
```

Dejá `SIGNUPS_ALLOWED=true` solo para crear tu primera cuenta, y apagalo apenas la tengas — sin esto, cualquiera en tu red podría crearse una cuenta en tu propio gestor de contraseñas.

**Para profundizar:** [Vaultwarden](./servicios/vaultwarden.md).

---

# Parte 3 · Tu plataforma de desarrollo

Esta parte es la más "DevOps" de la guía: tener tu propio Git, tu propio registro de imágenes Docker, y un pipeline de CI/CD real, todo autohosteado.

## 8. Git privado

**Forgejo** (fork de Gitea) es liviano y con SQLite alcanza para uso personal, sin necesitar una base de datos aparte:

```yaml
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:latest
    restart: unless-stopped
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      FORGEJO__database__DB_TYPE: sqlite3
      FORGEJO__server__DOMAIN: git.tuhomelab.local
      FORGEJO__server__ROOT_URL: http://git.tuhomelab.local/
      FORGEJO__service__DISABLE_REGISTRATION: "true"   # sin auto-registro público
    volumes:
      - forgejo-data:/data
    ports:
      - "3000:3000"
      - "2222:22"     # si el puerto 22 del host ya lo usa el SSH de la VM
volumes:
  forgejo-data:
```

Primer acceso crea la cuenta admin desde el instalador web. Con `DISABLE_REGISTRATION: "true"` nadie más puede crearse una cuenta — sos el único usuario a menos que invites a alguien.

**Para profundizar:** [Forgejo / Git local](./servicios/forgejo.md).

## 9. Registry de imágenes y CI/CD

**Nexus Repository** te da un registry Docker privado (y proxy de npm, si lo necesitás):

```yaml
services:
  nexus:
    image: sonatype/nexus3:latest
    restart: unless-stopped
    volumes:
      - nexus-data:/nexus-data
    ports:
      - "8081:8081"   # UI/API
      - "8082:8082"   # registry Docker — puerto dedicado, no comparte el 8081
volumes:
  nexus-data:
```

Después de crear el repositorio `docker-hosted` desde la UI, dos ajustes que no son obvios pero evitan horas de diagnóstico:

- **`writePolicy: "allow"`**, no `"allow_once"` — con la opción por defecto, un CI que re-pushea el mismo tag (`latest`) en cada build falla con "asset already exists".
- **Un usuario dedicado** para el CI (no la cuenta admin), con permisos acotados solo al repo Docker.

**Forgejo Actions** (el runner de CI incluido en Forgejo) corre los workflows. Con el runner registrado contra tu instancia, un `.forgejo/workflows/ci.yml` mínimo hace lint → test → build → push:

```yaml
name: CI
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: docker
    steps:
      - uses: actions/checkout@v4
      - run: npm install && npm test
      - run: docker build -t <tu-registry>:8082/miapp:${{ github.sha }} .
      - run: echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login <tu-registry>:8082 -u "${{ secrets.REGISTRY_USER }}" --password-stdin
      - run: docker push <tu-registry>:8082/miapp:${{ github.sha }}
```

Los secretos (`REGISTRY_USER`, `REGISTRY_PASSWORD`) se configuran en Forgejo, a nivel de usuario si querés que los hereden todos tus repos sin repetirlos — `Settings → Applications → Actions secrets`.

**Para profundizar:** [Sonatype Nexus](./servicios/nexus.md), [CI Runner](./servicios/ci-runner.md), [pipeline de ejemplo completo](./devops/pipeline-ejemplo.md) (con el circuito cerrado hasta un deploy real).

## 10. Kubernetes con GitOps

Este es el paso más grande de la guía — vale la pena tomárselo con calma. La idea central de GitOps: el estado deseado de tu cluster vive en un repo Git, y una herramienta (Argo CD) lo mantiene sincronizado solo — nunca corrés `kubectl apply` a mano para algo permanente.

**Instalar k3s** (una distribución liviana de Kubernetes, un solo comando):

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes -o wide
```

Ya viene con un Ingress controller (Traefik) y load balancer (ServiceLB) — suficiente para un homelab, sin instalar nada aparte.

**Instalar Argo CD** dentro del cluster:

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.13.2/manifests/install.yaml
kubectl -n argocd get pods -w   # esperar a que todo quede Running
```

:::caution
El `kubectl apply` normal (sin `--server-side`) puede fallar con un error de "annotation too long" en un CRD grande de Argo CD — es un límite real de Kubernetes con el método de apply por defecto, no un typo. Usar `--server-side` desde el principio.
:::

Acceso inicial (antes de tener el reverse proxy de la Parte 2 apuntando acá):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

Entrar a `https://localhost:8080` con `admin` y esa contraseña, cambiarla, y borrar el secret inicial.

**Tu primer repo GitOps**: un repo Git (en tu propio Forgejo) con una carpeta por aplicación, cada una con sus manifiestos de Kubernetes. Argo CD apunta a ese repo y despliega lo que encuentra — agregar una app nueva es agregar una carpeta y un commit, no tocar el cluster directo.

**Para profundizar:** [instalación de k3s](./kubernetes/instalacion-k3s.md), [instalar Argo CD](./kubernetes/instalacion-argocd.md), [patrones de despliegue](./kubernetes/patrones-despliegue.md), y como ejercicio guiado: [Docker whoami](./despliegues/docker-whoami.md), [Kubernetes whoami](./despliegues/kubernetes-whoami.md), [demo GitOps completa](./despliegues/gitops-demo.md).

---

# Parte 4 · Acceso y hogar

## 11. Acceso remoto sin abrir puertos

Dos formas complementarias de llegar a tu homelab desde afuera, sin abrir puertos en tu router (que es exactamente lo que la Parte 1 te dijo que evitaras):

- **Cloudflare Tunnel**: para publicar un servicio específico hacia Internet con un dominio propio, con autenticación delante (Cloudflare Access) — bueno para algo que vas a compartir o usar vos desde cualquier lado sin VPN.
- **Tailscale**: para tener tu LAN entera accesible como si estuvieras en tu casa, sin publicar nada — mejor para administración general, no para "compartir un link".

No son excluyentes: muchos homelabs usan Tailscale para administración propia y Cloudflare Tunnel solo para lo puntual que quieren compartir con otra persona.

**Para profundizar:** [Cloudflare Tunnel](./servicios/cloudflare-tunnel.md), [acceso remoto con Tailscale](./red/acceso-remoto.md).

## 12. Automatización del hogar

[Home Assistant](https://www.home-assistant.io/) es el estándar de facto para automatización doméstica self-hosted — sensores, luces, enchufes inteligentes, cámaras, todo bajo un mismo panel, sin depender de la nube del fabricante de cada dispositivo.

Se instala como su propia VM (no como contenedor Docker — necesita acceso más directo al hardware para ciertas integraciones, como USB de radios Zigbee/Z-Wave):

1. Descargar la imagen de [Home Assistant OS](https://www.home-assistant.io/installation/) para tu plataforma.
2. Crear una VM dedicada en Proxmox (2 vCPU / 4 GB RAM alcanza para empezar) y bootear desde esa imagen.
3. Primer acceso vía `http://<ip-de-la-vm>:8123` — el asistente de configuración inicial te guía para crear la cuenta y detectar dispositivos en tu red.

Es un ecosistema grande — no hace falta integrar todo el primer día. Empezar con lo que ya tenés (una cámara IP, un enchufe inteligente) y sumar de a poco es más sostenible que intentar migrar todo de una vez.

**Para profundizar:** [Home Assistant](./servicios/home-assistant.md).

## 13. Servidor de juegos (opcional)

Si te gusta jugar en tus propios términos (sin depender de un servidor de terceros, con tus propias reglas/mods), un homelab también es un buen lugar para hostear un servidor de juegos. Dos ejemplos comunes:

**Minecraft** — servidor Java, corre bien en Docker:

```yaml
services:
  minecraft:
    image: itzg/minecraft-server:latest
    restart: unless-stopped
    environment:
      EULA: "TRUE"
      MEMORY: "4G"
    volumes:
      - mc-data:/data
    ports:
      - "25565:25565"
volumes:
  mc-data:
```

**Counter-Strike 2** (u otro servidor dedicado de Source/GoldSrc) — vía SteamCMD, en un contenedor o VM liviana dedicada, según cuánta gente lo va a usar.

Decidí de antemano **cómo lo vas a exponer** a tus amigos (¿Tailscale para jugar solo entre quienes ya están en tu red, o publicarlo puntualmente?) — la misma lógica de la Parte 4, paso 11, aplica acá: no abras puertos directo al router salvo que entiendas el riesgo real de tener un servidor de juegos escuchando en Internet.

**Para profundizar:** [servidores de juegos](./juegos/vision-general.md), [Minecraft](./juegos/minecraft.md), [Counter-Strike 2](./juegos/counter-strike.md).

---

## Y ahora, ¿qué sigue?

Con las 4 partes de arriba tenés un homelab completo y funcional: base sólida, higiene básica, tu propia plataforma de desarrollo, y acceso remoto seguro. A partir de acá, todo es opcional y en el orden que quieras:

| Querés... | Andá a... |
|---|---|
| Observabilidad seria (métricas históricas, dashboards) | [Prometheus + Grafana](./observabilidad/arquitectura.md) — objetivo, no un paso obligatorio |
| Una capa de IA que entienda tu homelab | [Visión de la capa de IA](./ia/vision-general.md) |
| Separar tu red en zonas (IoT, invitados, servidores) | [VLAN y segmentación](./red/vlans.md) |
| Practicar diagnóstico con ejercicios guiados | [Laboratorios](./laboratorios/indice.md), de SSH básico hasta IA read-only |
| Un checklist resumen para imprimir | [Checklist del primer build](./roadmap/checklist-primer-build.md) |
| Saber qué hacer si algo se rompe | [Runbooks](./runbooks/indice-runbooks.md) y [troubleshooting](./troubleshooting/metodologia.md) |

Ninguna de esas páginas asume que ya leíste el resto — entrá directo a la que te interese.
