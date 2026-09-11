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

Es una foto real (aurora boreal), no el gradiente CSS que había antes — Homepage la sirve nativamente vía `background:` en `settings.yaml`, con blur/saturación/brillo/opacidad ajustables. Requiere montar un volumen aparte:

```yaml
# compose.yaml
volumes:
  - ./config:/app/config
  - ./images:/app/public/images   # necesario para servir imágenes propias
```

```yaml
# settings.yaml
background:
  image: /images/bg-2.jpg
  blur: ""   # sin blur — la foto de Pexels tiene resolución real, no hace falta disimular nada
  saturate: 90
  brightness: 40
  opacity: 40
```

Pasó por dos imágenes antes de esta:

1. Una foto provista por el autor (4.3 MB PNG, 1672×941) — se veía pixelada al estirarse en pantallas más grandes, incluso con blur alto.
2. Dos intentos con fotos de un banco de imágenes de pago (`magnific.com`/Freepik) — ambas con la marca de agua **"Magnific" repetida por toda la imagen** en cualquier resolución consultada (se probó pidiendo hasta 2560px de ancho vía el parámetro `w=` de su CDN, el mismo dominio cachea 2000px como máximo real). Quedaron descartadas — no se puede publicar una imagen con marca de agua de un banco pago sin la licencia.
3. La actual: **Pexels** (banco 100% gratuito, sin atribución obligatoria, sin marca de agua), foto real de aurora verde sobre cielo estrellado, 1920×1280, sin horizonte/paisaje que compita visualmente con las tarjetas — 101 KB después de la compresión propia de Pexels, no hizo falta recomprimir.

Regla práctica que quedó de esto: antes de usar cualquier imagen de un buscador, chequear si el dominio es un banco de pago (Freepik/Magnific, Shutterstock, etc.) — casi siempre entregan preview con marca de agua sin importar qué resolución se pida por URL.

`custom.css` ya no define el fondo (antes tenía un gradiente + grilla armado en CSS puro, antes de tener esta imagen) — la opacidad de las tarjetas y la barra de widgets se subió dos veces (0.55/0.65 → 0.7/0.78 → **0.85/0.9**, casi opacas) porque con una foto de verdad de fondo, cualquier transparencia notoria le come contraste al texto — mucho más agresivo de lo que hacía falta con el gradiente CSS liso de antes.

## Identidad visual (custom.css)

Homepage carga `config/custom.css` automáticamente (se sirve en `/api/config/custom.css`, referenciado por la propia página) — no hace falta tocar nada del compose, solo poner el archivo ahí. Se usó para:

- fondo con foto real (ver arriba) — antes era un gradiente + grilla en CSS puro, sin imagen que hostear; se cambió cuando apareció una imagen mejor;
- tarjetas de servicio (`.service`) con borde y efecto hover en vez del recuadro plano default;
- nombres de grupo (`.service-group-name`) en mayúsculas con acento celeste, estilo "consola";
- la barra de widgets superior (`.widget-container`) separada visualmente en pastillas, para que CPU/RAM/disco/reloj/clima/buscador no se vean todos pegados.

Los nombres de clase (`.service`, `.service-name`, `.service-description`, `.service-group-name`, `.widget-container`) salen del código fuente de Homepage (`src/components/services/item.jsx` y `group.jsx`), no de la documentación pública — no están listados en `docs/configs/custom-css-js.md`, hubo que revisar el repo directo.


## Reorganizar la barra de widgets superior

Por defecto Homepage pone **todos** los widgets de info (`resources`, `datetime`, `openmeteo`, `search`) en una sola fila estirada de punta a punta — con los 4 juntos se veía amontonado y sin jerarquía. Se separó en dos filas con puro CSS, sin tocar `widgets.yaml` ni mover ningún nodo del DOM (evita pelear con los re-renders de React, que si movés el elemento real vía JS te lo puede volver a poner en su lugar original):

```css
/* fecha/hora + clima + buscador: centrados y agrupados */
div:has(> .information-widget-datetime) {
  justify-content: center !important;
  gap: 0.6rem;
}

/* CPU/RAM/disco: fila propia, con un divisor sutil arriba */
.information-widget-resource {
  order: 10;
}
.information-widget-resource:first-of-type {
  flex-basis: 100%;      /* fuerza el salto de línea dentro del mismo flex row */
  justify-content: center;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px solid rgba(56, 189, 248, 0.15);
}
```

El truco es `flex-basis: 100%` en el *primer* elemento `.information-widget-resource` (CPU, RAM y disco son tres instancias del mismo widget, una por métrica) — fuerza que ese y los siguientes salten a una fila nueva dentro del mismo contenedor flex-wrap, sin necesitar un contenedor HTML distinto. `:has()` (soportado en todos los navegadores modernos desde 2023) selecciona el contenedor padre real de `datetime` sin depender de una clase propia de Homepage para ese wrapper — las clases que trae son utilitarias de Tailwind (`flex`, `justify-between`, etc.), no hay una clase semántica estable para engancharse ahí directamente.

## Header con el nombre del proyecto (custom.js)

Homepage no tiene ningún lugar nativo para mostrar el nombre del proyecto en grande — el `title` de `settings.yaml` solo va al `<title>` del navegador y al manifest PWA, y el único widget relacionado ("logo") es un ícono de 48×48px, sin texto. Para el título grande tipo "O.S.C.A.R." del mockup original hizo falta `custom.js`:

```js
// custom.js
function addOscarHeader() {
  var existing = document.getElementById("oscar-header");
  if (existing) {
    syncSubtitleWidth();   // el ancho de .oscar-title cambia con el viewport (mobile/desktop)
    return;
  }
  var header = document.createElement("div");
  header.id = "oscar-header";
  header.innerHTML =
    '<span class="oscar-title">O.S.C.A.R.</span>' +
    '<span class="oscar-subtitle">Operations, Services, Compute, Automation &amp; Routing</span>';
  document.body.insertBefore(header, document.body.firstChild);
  syncSubtitleWidth();
}

function syncSubtitleWidth() {
  var title = document.querySelector("#oscar-header .oscar-title");
  var subtitle = document.querySelector("#oscar-header .oscar-subtitle");
  if (!title || !subtitle) return;
  var width = title.getBoundingClientRect().width;
  if (width > 0) subtitle.style.width = width + "px";
}

addOscarHeader();
document.addEventListener("DOMContentLoaded", addOscarHeader);
setInterval(addOscarHeader, 2000);   // red de seguridad + remide el ancho en cada pasada
```

Se inserta directo en `document.body`, no dentro del contenedor que maneja React — así un re-render de Homepage no lo pisa. El `setInterval` cumple dos roles: red de seguridad si algo llega a borrar el header, y remedir el ancho real de "O.S.C.A.R." (cambia según el viewport) para que el subtítulo, centrado debajo y en fuente más chica, quede exactamente con el mismo ancho — se logra fijando `subtitle.style.width` en píxeles al ancho medido del título, y dejando que el texto haga wrap natural dentro de ese ancho.

`custom.css` pone el header en columna centrada (`flex-direction: column; align-items: center`), y `overflow-wrap: break-word` en el subtítulo — sin eso, una palabra larga como "Automation" se salía del ancho angosto que le da el título y rompía el efecto. El título además tiene una animación de glow tipo aurora, cicla color y sombra entre celeste/verde-agua/violeta cada 6s:

```css
@keyframes oscar-aurora-glow {
  0%, 100% { color: #38bdf8; text-shadow: 0 0 22px rgba(56, 189, 248, .55), 0 0 46px rgba(56, 189, 248, .25); }
  33%      { color: #5eead4; text-shadow: 0 0 22px rgba(94, 234, 212, .55), 0 0 46px rgba(94, 234, 212, .25); }
  66%      { color: #a78bfa; text-shadow: 0 0 22px rgba(167, 139, 250, .55), 0 0 46px rgba(167, 139, 250, .25); }
}
.oscar-title { animation: oscar-aurora-glow 6s ease-in-out infinite; }
```

Ver el archivo completo en `core01`, no vale la pena duplicarlo acá.

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
