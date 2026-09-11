---
title: Homepage
sidebar_position: 21
---

# Homepage

**Estado:** Actual · Dashboard — corriendo en `core01`
**Dónde corre:** Docker Core (`/srv/oscar/apps/homepage/`)
**Sizing inicial:** ~100 MB RAM
**Red/puertos:** `3005` HTTP interno — acceso real vía [Cloudflare Tunnel](./cloudflare-tunnel.md) en `home.oscarlab.com.ar`
**Persistencia:** solo configuración (YAML), sin base de datos

## Rol dentro de O.S.C.A.R.

Dashboard de servicios: una página con links y estado de cada servicio del homelab, con widgets de CPU/RAM/disco del host. Es candidato natural para mostrarse en la pantalla táctil del [Control Center](../observabilidad/dashboard-rack.md) apenas esté conectada — más simple de tener andando que armar un dashboard Grafana desde cero.

## Instalación

```bash
mkdir -p /srv/oscar/apps/homepage/config
```

`config/services.yaml` (un grupo por sección, servicios reales con su URL):

```yaml
- Infraestructura:
    - Proxmox (oscar-core):
        href: https://<IP-de-oscar-core>:8006
        description: Hypervisor — administra todas las VMs y contenedores
        icon: proxmox.png
        siteMonitor: https://<IP-de-oscar-core>:8006
        widget:
          type: proxmox
          url: https://<IP-de-oscar-core>:8006
          username: root@pam!homepage
          password: <secret del token, fuera de Git>
          node: oscar-core
    - ProxMenux Monitor:
        href: https://monitor.oscarlab.com.ar
        description: CPU, RAM y disco del hipervisor en vivo
        icon: proxmox.png
        siteMonitor: http://<IP-de-oscar-core>:8008
    - AdGuard Home:
        href: http://<IP-del-LXC-100>
        description: Filtra DNS y bloquea publicidad en toda la red
        icon: adguard-home.png
        siteMonitor: http://<IP-del-LXC-100>
- Servicios:
    - Uptime Kuma:
        href: https://kuma.oscarlab.com.ar
        description: Estado de disponibilidad de todo O.S.C.A.R.
        icon: uptime-kuma.png
        siteMonitor: http://<IP-de-core01>:3001
        widget:
          type: uptimekuma
          url: http://<IP-de-core01>:3001
          slug: oscar
    - n8n:
        href: https://n8n.oscarlab.com.ar
        description: Automatización de workflows
        icon: n8n.png
        siteMonitor: http://<IP-de-core01>:5678/healthz
    - Vaultwarden:
        href: https://vault.oscarlab.com.ar
        description: Gestor de contraseñas propio, compatible con Bitwarden
        icon: vaultwarden.png
        siteMonitor: https://vault.oscarlab.com.ar/alive
    - Beszel:
        href: https://beszel.oscarlab.com.ar
        description: CPU, RAM y disco de core01 en tiempo real
        icon: beszel.png
        siteMonitor: http://<IP-de-core01>:8090
- Hogar:
    - Home Assistant:
        href: http://<IP-de-VM-101>
        description: Automatización y control del hogar
        icon: home-assistant.png
        siteMonitor: http://<IP-de-VM-101>
```

El nombre del segundo grupo es **"Servicios"**, no "core01" — el hostname de la VM no le dice nada a nadie que no conozca el proyecto por dentro. Las descripciones dicen qué hace cada cosa en criollo, no una traducción literal del nombre técnico.

Los links usan los dominios reales (vía [Cloudflare Tunnel](./cloudflare-tunnel.md)) cuando el servicio está publicado, o la IP LAN cuando no (Proxmox, AdGuard, Home Assistant — deliberadamente sin dominio, ver [exposición a Internet](../seguridad/exposicion-internet.md)). Cada tarjeta tiene:

- `icon`: nombre del ícono del set [dashboard-icons](https://github.com/homarr-labs/dashboard-icons) que Homepage bundlea — no hace falta subir imágenes propias;
- `siteMonitor`: URL que Homepage chequea por su cuenta (HEAD, con fallback a GET) para mostrar el puntito de estado en vivo en la tarjeta — independiente de Uptime Kuma, es un chequeo propio de Homepage.

`settings.yaml` también define el layout (columnas por grupo) y `headerStyle: boxedWidgets` para que se vea menos genérico que el default.

## Widgets nativos (datos en vivo en la tarjeta)

Además del `siteMonitor` (puntito de estado), **6 de las 9 tarjetas** tienen un `widget:` que muestra datos reales directo en la card en vez de un link plano — Proxmox, AdGuard Home, Cloudflare Tunnel, Uptime Kuma, Beszel y Home Assistant. Solo n8n y Vaultwarden se quedan con descripción fija: Homepage no tiene una integración nativa para ninguno de los dos.

Cada widget necesitó su propia credencial, todas de solo lectura donde el servicio lo permite:

| Servicio | Credencial | Cómo se generó |
|---|---|---|
| Proxmox | token `root@pam!homepage`, rol `PVEAuditor` | token dedicado, ver arriba |
| AdGuard Home | usuario/password real del panel | no tiene modelo de tokens/roles, solo un admin |
| Cloudflare Tunnel | el mismo token de la cuenta (ya tiene `Tunnel:Edit`, que cubre lectura) | reutilizado, no se creó uno nuevo solo para esto |
| Uptime Kuma | ninguna — lee de la status page pública `/status/oscar` | — |
| Beszel | superusuario dedicado `homepage@oscar.home` | creado por CLI, mismo patrón que en su momento para el agente — ver [Beszel](./beszel.md) |
| Home Assistant | long-lived access token | generado a mano desde el perfil de HA (Seguridad → Tokens de acceso de larga duración) |

```yaml
# Uptime Kuma — lee de una status page, no de la lista de monitores directo
widget:
  type: uptimekuma
  url: http://<IP-de-core01>:3001
  slug: oscar   # la status page se crea aparte en Kuma, con todos los monitores reales dentro

# Proxmox — requiere un token de API dedicado, de solo lectura (rol PVEAuditor)
widget:
  type: proxmox
  url: https://<IP-de-oscar-core>:8006
  username: root@pam!homepage
  password: <secret del token, fuera de Git>
  node: oscar-core

# AdGuard Home — no tiene tokens/roles, solo el usuario/password real del panel
widget:
  type: adguard
  url: http://<IP-del-LXC-100>
  username: <usuario admin>
  password: <password admin, fuera de Git>
  fields: ["queries", "blocked", "filtered", "latency"]

# Cloudflare Tunnel — reutiliza el token de cuenta ya existente (Tunnel:Edit cubre lectura)
widget:
  type: cloudflared
  accountid: <account id>
  tunnelid: <tunnel id>
  key: <token de Cloudflare, fuera de Git>
  fields: ["status", "origin_ip"]

# Beszel — pide un superusuario (no alcanza con la cuenta normal); se creó uno dedicado
widget:
  type: beszel
  url: http://<IP-de-core01>:8090
  username: homepage@oscar.home
  password: <secret, fuera de Git>
  version: 2   # Beszel >= 0.9.0

# Home Assistant — long-lived access token generado a mano desde el perfil de HA
widget:
  type: homeassistant
  url: http://<IP-de-VM-101>
  key: <token, fuera de Git>
  fields: ["people_home", "lights_on", "switches_on"]
```

El token `root@pam!homepage` se creó con `privsep=1` (sin permisos hasta asignarle un rol explícito) — el rol `PVEAuditor` en el path `/` se asignó a mano desde la UI de Proxmox (Datacenter → Permissions → Add → Token Permission), porque asignar roles vía API quedó bloqueado por las reglas de seguridad del entorno de automatización usado para este build.

## Widgets de información (barra superior)

Van en **`widgets.yaml`**, un archivo separado de `settings.yaml` — es un error fácil de cometer (yo mismo lo cometí primero: los puse dentro de `settings.yaml` bajo una clave `widgets:`, y Homepage los ignoró en silencio sin tirar ningún error, así que la página siguió mostrando el widget de recursos viejo nomás; costó varias vueltas de "no veo cambios" hasta confirmar con curl directo al contenedor que el HTML servido no tenía el contenido nuevo).

```yaml
# widgets.yaml
- resources:
    cpu: true
    memory: true
    disk: /
- datetime:
    text_size: xl
    locale: es-AR
    format:
      dateStyle: long
      timeStyle: short
      hour12: false
- openmeteo:
    label: Buenos Aires
    latitude: -34.6037
    longitude: -58.3816
    timezone: America/Argentina/Buenos_Aires
    units: metric
- search:
    provider: google
    showSearchSuggestions: true
    target: _blank
```

`openmeteo` es el widget de clima recomendado por Homepage — no pide registro ni API key (a diferencia de OpenWeatherMap). `settings.yaml` solo tiene título/tema/layout — nada de widgets de info ahí.

## Fondo de pantalla

Es una foto real (aurora boreal, provista por el autor), no el gradiente CSS que había antes — Homepage la sirve nativamente vía `background:` en `settings.yaml`, con blur/saturación/brillo/opacidad ajustables. Requiere montar un volumen aparte:

```yaml
# compose.yaml
volumes:
  - ./config:/app/config
  - ./images:/app/public/images   # necesario para servir imágenes propias
```

```yaml
# settings.yaml
background:
  image: /images/bg-1.jpg
  blur: xl    # bien alto: disimula que la foto (1672×941) se ve pixelada al estirarse en pantallas más grandes
  saturate: 90
  brightness: 45
  opacity: 55   # bajado de 90 a 55 — con más se perdía el contraste contra las tarjetas
```

La imagen original pesaba 4.3 MB (PNG) — se convirtió a JPEG calidad 82 antes de subirla (441 KB), porque esto lo va a cargar también el navegador de la Raspberry que eventualmente maneje la pantalla táctil del rack, y 4+ MB por cada carga de página es innecesario para una foto de fondo.

`custom.css` ya no define el fondo (antes tenía un gradiente + grilla armado en CSS puro, antes de tener esta imagen) — la opacidad de las tarjetas y la barra de widgets se subió dos veces (0.55/0.65 → 0.7/0.78 → **0.85/0.9**, casi opacas) porque con una foto de verdad de fondo, cualquier transparencia notoria le come contraste al texto — mucho más agresivo de lo que hacía falta con el gradiente CSS liso de antes.

## Identidad visual (custom.css)

Homepage carga `config/custom.css` automáticamente (se sirve en `/api/config/custom.css`, referenciado por la propia página) — no hace falta tocar nada del compose, solo poner el archivo ahí. Se usó para:

- fondo con foto real (ver arriba) — antes era un gradiente + grilla en CSS puro, sin imagen que hostear; se cambió cuando apareció una imagen mejor;
- tarjetas de servicio (`.service`) con borde y efecto hover en vez del recuadro plano default;
- nombres de grupo (`.service-group-name`) en mayúsculas con acento celeste, estilo "consola";
- la barra de widgets superior (`.widget-container`) separada visualmente en pastillas, para que CPU/RAM/disco/reloj/clima/buscador no se vean todos pegados.

Los nombres de clase (`.service`, `.service-name`, `.service-description`, `.service-group-name`, `.widget-container`) salen del código fuente de Homepage (`src/components/services/item.jsx` y `group.jsx`), no de la documentación pública — no están listados en `docs/configs/custom-css-js.md`, hubo que revisar el repo directo.


## Sin soporte: páginas con carrusel/slide

Homepage es un dashboard de una sola página — no tiene una función nativa para rotar entre distintas vistas o pantallas completas. Si eventualmente se quiere que la [pantalla táctil del rack](../observabilidad/dashboard-rack.md) cicle entre Homepage, Kuma, Beszel, etc., eso se resuelve del lado del navegador en modo kiosko (la Raspberry que maneje la pantalla), no configurando Homepage — queda para cuando se arme esa pieza.

`compose.yaml`:

```yaml
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:${HOMEPAGE_VERSION}
    restart: unless-stopped
    volumes:
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      HOMEPAGE_ALLOWED_HOSTS: "<IP-de-core01>:3005,home.oscarlab.com.ar"
    ports:
      - "3005:3000"
```

```bash
docker compose up -d
```

:::caution Gotcha real encontrado al instalar
Homepage (basado en Next.js) valida el header `Host` de cada request desde una versión reciente — sin `HOMEPAGE_ALLOWED_HOSTS` seteado explícitamente a **cada** host:puerto/dominio real usado, responde `400` (o `{"error": "Host validation failed"}`) a todo lo que no esté en la lista. Es una lista separada por comas, no un solo valor — pasó exactamente esto al sumar Cloudflare Tunnel: `home.oscarlab.com.ar` respondía "Host validation failed" hasta agregarlo a la lista junto con la IP:puerto que ya estaba.
:::

El mount de `/var/run/docker.sock` es opcional — habilita el "Docker widget" para ver contenedores directamente desde Homepage. Es de solo lectura (`:ro`), pero igual implica el mismo riesgo que cualquier acceso al socket de Docker (ver [seguridad de contenedores](../seguridad/contenedores.md)); si no se necesita ese widget, se puede quitar el volumen.

## Seguridad

- muestra links y nombres de todos los servicios internos — no es sensible por sí mismo, pero es un mapa completo de la infraestructura si alguien no autorizado accede; por eso, a diferencia de otros dashboards de estado, va detrás de [Cloudflare Access](./cloudflare-tunnel.md) igual que los paneles administrativos;
- el socket de Docker montado (si se usa) es el mismo riesgo de siempre: acceso de lectura al socket permite ver toda la configuración de contenedores del host;
- sin autenticación propia — la protección real hoy es Cloudflare Access delante, no algo de Homepage mismo.

## Backup y restore

Todo el estado es la carpeta `config/` (YAML de servicios, widgets, settings) — no hay base de datos. Versionarla en Git es razonable si no tiene URLs/tokens sensibles adentro; si los tiene, tratarla como cualquier config con secretos (fuera de Git, backup aparte).

## Observabilidad

Disponibilidad HTTP del puerto 3005 alcanza — es un dashboard, no un servicio con estado crítico.

## Troubleshooting

- **`400` o `{"error": "Host validation failed"}`** → el host/dominio usado no está en `HOMEPAGE_ALLOWED_HOSTS` — ver nota arriba; hay que agregar cada forma de acceso (IP:puerto, dominio) por separado, no alcanza con una sola.
- **Un servicio aparece pero el link no funciona** → URL puesta en `services.yaml` no coincide con la IP/puerto real del servicio — confirmar contra el [catálogo de servicios](./catalogo.md).
