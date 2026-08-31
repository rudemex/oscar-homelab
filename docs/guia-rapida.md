---
title: Guía rápida
sidebar_position: 2
slug: /guia-rapida
---

# Guía rápida: tu primer homelab

Esta página sola alcanza para pasar de "tengo una compu que no uso" a "tengo un servidor con Proxmox, Docker y un servicio real corriendo", en un fin de semana. Sin desvíos: un camino, una opción recomendada por paso, sin explorar alternativas.

No importa si nunca instalaste Linux. Cada comando está completo — copiás, pegás, listo. Si un término te resulta nuevo, está explicado en el momento en que aparece.

Cuando termines esta guía y quieras ir más profundo (VLANs, backups serios, Kubernetes, GitOps, IA), el resto del sitio está para eso — pero no lo necesitás para arrancar.

## Qué vas a necesitar

Esto es lo **mínimo real**, no una lista de compras. No hace falta el hardware específico de ningún inventario particular — cualquier equipo que cumpla esto sirve:

| Qué | Mínimo | Por qué |
|---|---|---|
| Una computadora dedicada | 4 hilos de CPU con virtualización (Intel VT-x / AMD-V), 8 GB RAM (16 GB cómodo), 1 disco SSD/NVMe de 120 GB+ | Va a ser tu servidor 24/7 — un mini PC de oficina descartado, un NUC, o una torre vieja alcanzan. No necesita ser nueva ni cara. |
| Un pendrive USB | 8 GB+ | Para instalar el sistema operativo del servidor. |
| Cable de red | Ethernet, no Wi-Fi | El servidor va cableado siempre — Wi-Fi en un servidor es una fuente de problemas que no necesitás. |
| Router/switch | El que ya tengas | No hace falta nada especial todavía. |
| Otra computadora | La que estás usando ahora | Para administrar el servidor por red — no vas a necesitar teclado/monitor conectados al servidor después del primer paso. |

¿Ya tenés más de un equipo, o pensás crecer en serio? [Requisitos mínimos por componente](./referencia/requisitos-minimos.md) desglosa esto por rol (Docker, Kubernetes, observabilidad) para cuando llegue el momento — no lo necesitás todavía.

## Paso 1 · Instalar Proxmox

[Proxmox VE](https://www.proxmox.com/) es el software que convierte tu computadora en un servidor capaz de correr varias "computadoras virtuales" (VMs) dentro. Es gratis, y es lo que vas a instalar en el equipo dedicado.

1. Descargar el ISO desde [proxmox.com/downloads](https://www.proxmox.com/en/downloads) (elegir "Proxmox VE").
2. Crear el pendrive booteable con [balenaEtcher](https://etcher.balena.io/) (gratis, mismo proceso en Windows/Mac/Linux): abrir Etcher, elegir el ISO descargado, elegir el pendrive, "Flash".
3. Conectar el pendrive al servidor, prenderlo, y entrar al menú de arranque (usualmente `F11`, `F12` o `Esc` al prender — varía por fabricante) para bootear desde USB.
4. Seguir el instalador: elegir el disco de destino (**borra todo lo que tenga ese disco**), país/huso horario/teclado, y una contraseña de administrador robusta.
5. Configurar la red cuando lo pida: dejar DHCP si no estás seguro, o poner una IP fija si ya sabés cuál querés usar.
6. Terminada la instalación, el servidor reinicia. Ya no necesita más el pendrive, ni el teclado/monitor.

Desde tu otra computadora, abrir en el navegador `https://<IP-del-servidor>:8006` (el navegador va a advertir por certificado autofirmado — es esperable, avanzar igual) y entrar con `root` y la contraseña que elegiste.

## Paso 2 · Crear tu primera VM

Vamos a crear una VM con Ubuntu Server — va a ser el lugar donde corran tus aplicaciones.

**Subir el instalador de Ubuntu a Proxmox:**

1. Descargar el ISO de [Ubuntu Server LTS](https://ubuntu.com/download/server) en tu otra computadora.
2. En Proxmox: `Datacenter → <tu nodo> → local → ISO Images → Upload`, y subir el archivo descargado.

**Crear la VM:**

En Proxmox, botón `Create VM` arriba a la derecha, y completar el asistente:

| Pestaña | Qué elegir |
|---|---|
| General | Nombre: `core01` |
| OS | El ISO de Ubuntu que subiste |
| System | Dejar los valores por defecto |
| Disks | 40 GB alcanza para empezar |
| CPU | 2 cores |
| Memory | 4096 MB (4 GB) |
| Network | Dejar el bridge por defecto (`vmbr0`) |

Confirmar, seleccionar la VM creada y `Start`. Abrir su consola (`Console` en el menú de la VM) y seguir el instalador de Ubuntu:

- Idioma y teclado: los que prefieras.
- Red: dejar DHCP.
- Storage: "use entire disk", sin configuración especial.
- Usuario: elegí un nombre de usuario y una contraseña — vas a usarlos todo el tiempo.
- **"Install OpenSSH server": marcar que SÍ** — sin esto no vas a poder conectarte por SSH después, y es la forma normal de administrar la VM.
- Saltear la instalación de snaps opcionales (servidor web, Docker, etc. — los instalamos nosotros en el paso siguiente, más controlado).

Terminada la instalación, reiniciar cuando lo pida. La VM ya tiene una IP (visible en la consola, o revisando la lista de DHCP de tu router).

**Conectarte desde tu otra computadora:**

```bash
ssh tu-usuario@<IP-de-la-VM>
```

Si nunca usaste SSH ni una terminal, [herramientas básicas](./primeros-pasos/herramientas-basicas.md) lo explica desde cero — pero para seguir esta guía alcanza con pegar el comando de arriba.

## Paso 3 · Instalar Docker

Dentro de la VM (por SSH), actualizar el sistema e instalar Docker con el método oficial:

```bash
sudo apt update
sudo apt full-upgrade -y

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"
```

Cerrar la sesión (`exit`) y volver a conectar por SSH para que el permiso tome efecto. Confirmar que funciona:

```bash
docker run hello-world
```

Si ves un mensaje que empieza con "Hello from Docker!", ya tenés Docker corriendo.

## Paso 4 · Levantar tu primer servicio real

Vamos a levantar [Uptime Kuma](https://github.com/louislam/uptime-kuma) — un monitor de disponibilidad con una interfaz visual agradable. Es una buena primera aplicación: se ve andando en segundos y ya te sirve para algo real (vigilar que tus otros servicios sigan arriba).

```bash
mkdir -p ~/uptime-kuma && cd ~/uptime-kuma
```

Crear un archivo `compose.yaml`:

```bash
nano compose.yaml
```

Pegar esto (`Ctrl+O`, Enter para guardar; `Ctrl+X` para salir):

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1.23.16
    restart: unless-stopped
    volumes:
      - uptime-kuma-data:/app/data
    ports:
      - "3001:3001"

volumes:
  uptime-kuma-data:
```

Levantarlo:

```bash
docker compose up -d
```

Abrir en el navegador `http://<IP-de-la-VM>:3001` — te va a pedir crear un usuario administrador la primera vez. Agregá un monitor de prueba (por ejemplo, un chequeo HTTP a `https://google.com`) para ver cómo se ve funcionando.

## Y ahora, ¿qué sigue?

Ya tenés lo esencial: un hypervisor, una VM con Docker, y un servicio real corriendo. A partir de acá, cada camino es opcional y lo tomás cuando lo necesites — no hace falta seguir un orden estricto:

| Querés... | Andá a... |
|---|---|
| Entender por qué la guía completa está organizada así | [Arquitectura](./arquitectura/vision-general.md) |
| Sumar más servicios (backups, dashboards, automatización) | [Catálogo de servicios](./servicios/catalogo.md) |
| Backups de verdad, no solo "anda" | [Backup y Disaster Recovery](./backup-dr/estrategia-321.md) |
| Separar tu red en zonas (IoT, invitados, servidores) | [VLAN y segmentación](./red/vlans.md) |
| Aprender Kubernetes sobre esto mismo | [Kubernetes y GitOps](./kubernetes/vision-general.md) |
| Un servidor de Minecraft o Counter-Strike | [Servidores de juegos](./juegos/vision-general.md) |
| Ver todo el recorrido completo, fase por fase | [Roadmap](./roadmap/roadmap-general.md) |

Ninguna de esas páginas asume que ya las leíste — podés entrar directo a la que te interese.
