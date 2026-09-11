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


## CPU/RAM/disco y buscador: reubicados dentro del header

Layout final pedido, en 4 filas apiladas:

```
[ hora/fecha ]      [ CPU · RAM · disco ]      [ clima ]
                          O.S.C.A.R.
                          subtítulo
                          buscador
```

`glances` (CPU/RAM/disco — ver más abajo por qué no es el widget `resources` original) y `search` siguen siendo los widgets **nativos** de Homepage (traen datos reales del propio backend) — lo que cambia es su posición: `custom.js` los saca de la fila donde Homepage los renderiza por defecto y los mueve, con `appendChild`, a dos contenedores (`#oscarResourcesSlot`, `#oscarSearchSlot`) dentro del header custom:

```js
function relocateNativeWidgets() {
  var resourcesSlot = document.getElementById("oscarResourcesSlot");
  var searchSlot = document.getElementById("oscarSearchSlot");
  if (!resourcesSlot || !searchSlot) return;

  document.querySelectorAll(".information-widget-resource").forEach(function (el) {
    if (el.parentNode !== resourcesSlot) resourcesSlot.appendChild(el);
  });

  var searchEl = document.querySelector(".widget-container:has(input)");
  if (searchEl && searchEl.parentNode !== searchSlot) {
    searchSlot.appendChild(searchEl);
  }
}
```

Es **mover el nodo real**, no clonarlo ni reconstruirlo — `appendChild` sobre un nodo existente lo saca de donde estaba y lo pone en el nuevo lugar, sin recrearlo. Esto importa porque Homepage sigue actualizando esos widgets con React por su cuenta (nuevo % de CPU cada tanto, etc.): React actualiza por la referencia al nodo real que ya tiene guardada internamente, no por dónde vive ese nodo en el documento en un momento dado, así que reposicionarlo no le impide seguir refrescando los datos. El riesgo real (bajo pero no cero) es que Homepage renderizara nueva UI hermana esperando encontrar el nodo en su ubicación original — se ejecuta `relocateNativeWidgets()` en el mismo `setInterval` de 2s que reconstruye el resto del header, así que si Homepage llegara a devolverlo a su sitio, se vuelve a mover solo.

La fila original de Homepage (donde vivían antes de moverlos) queda vacía y sin CSS propio — sin hijos no ocupa espacio, no hace falta ocultarla a mano.

Estilo, sin caja/fondo, igual que fecha y clima:

```css
#oscarResourcesSlot {
  display: flex;
  flex-direction: row;   /* el mismo div también es .oscar-col (column) — sin esto hereda vertical */
  align-items: center;
  gap: 1rem;
  justify-content: center;
}
.widget-container {
  background: transparent;
  border: none;
  color: #f8fafc;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7);
  font-size: 0.78rem;
}
/* el buscador es el único widget interactivo acá — necesita alguna pista
   visual de que se puede escribir, aunque sea mínima */
.widget-container:has(input) {
  border-bottom: 1px solid rgba(248, 250, 252, 0.35);
}
```

`:has()` (soportado en todos los navegadores modernos desde 2023) distingue el buscador del resto sin necesitar el nombre real de su clase — que es una clase Tailwind generada dinámicamente, no una constante fija en el código fuente de Homepage.

### Por qué es `glances`, no `resources`

El widget `resources` de Homepage, sin nada más, mide el **contenedor de Homepage**, no `core01` entero — CPU y RAM son las del propio proceso de Homepage (casi siempre ~0%, porque es una app liviana), no las de la VM completa. El disco tenía el mismo problema (`disk: /` apuntaba al filesystem interno del contenedor). Un primer parche montó el filesystem del host de solo lectura (`/:/hostfs:ro`) para arreglar el disco, pero CPU/RAM seguían siendo del contenedor — no hay forma de arreglar eso desde adentro del propio contenedor de Homepage.

La solución real fue sumar [Glances](./glances.md), un agente aparte corriendo con `network_mode: host` + `pid: host` en `core01`, que sí ve el host completo — y usar el widget `glances` de Homepage (no `resources`) para leer de ahí:

```yaml
# widgets.yaml
- glances:
    url: http://192.168.0.156:61208
    version: 4
    cpu: true
    mem: true
    disk: /hostroot
    expanded: true
- search:
    provider: google
    focus: false
    showSearchSuggestions: true
    target: _blank
```

`glances` está "diseñado para calzar con el widget `resources`" (según la propia documentación de Homepage) — usa el mismo componente visual por dentro, así que todo el CSS/JS de reubicación de arriba (que apunta a `.information-widget-resource`) siguió funcionando sin cambios al pasar de uno a otro.

`expanded: true` agrega una segunda línea por métrica (total además del valor principal). También se agregó `language: es` en `settings.yaml`, así las etiquetas del widget (que veían en inglés — "cpu", "free", "total") salen en español.

Instalar Glances también dejó en evidencia que **`core01` estaba al 91% de RAM** (4 GB asignados, con 9 contenedores reales corriendo) — se subió a 8 GB antes de sumarle uno más. Ver [creación de `core01`](../proxmox/crear-vm-core01.md#sizing-inicial).

## Header de 3 columnas: hora/fecha · O.S.C.A.R. · clima (custom.js)

Homepage no tiene ningún lugar nativo para mostrar el nombre del proyecto en grande — el `title` de `settings.yaml` solo va al `<title>` del navegador y al manifest PWA, y el único widget relacionado ("logo") es un ícono de 48×48px, sin texto. La primera versión fue solo el título centrado con `datetime`/`openmeteo` como widgets nativos de Homepage abajo — pero esos widgets traen su propia caja/fondo (`.widget-container`) sin margen real para estilar cada uno suelto. Se reemplazó por un reloj y un clima **construidos desde cero** en `custom.js`, en 3 columnas: hora/fecha a la izquierda, "O.S.C.A.R." al centro, clima a la derecha — texto blanco sin caja, solo con sombra para que resalte contra la foto de fondo:

```js
// custom.js
var WEATHER_LAT = -34.6037, WEATHER_LON = -58.3816;
var WEATHER_LABEL = "Buenos Aires";
var WEATHER_TZ = "America/Argentina/Buenos_Aires";
var WEATHER_ICONS = { 0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 61: "🌧️", 95: "⛈️" /* ...resto de códigos WMO */ };

function buildOscarHeader() {
  if (document.getElementById("oscar-header")) { syncSubtitleWidth(); return; }
  var header = document.createElement("div");
  header.id = "oscar-header";
  header.innerHTML =
    '<div class="oscar-col oscar-col-left">' +
      '<span class="oscar-time" id="oscarTime">--:--</span>' +
      '<span class="oscar-date" id="oscarDate">—</span></div>' +
    '<div class="oscar-col oscar-col-center">' +
      '<span class="oscar-title">O.S.C.A.R.</span>' +
      '<span class="oscar-subtitle">Operations, Services, Compute, Automation &amp; Routing</span></div>' +
    '<div class="oscar-col oscar-col-right">' +
      '<span class="oscar-weather-temp" id="oscarWeatherTemp">—</span>' +
      '<span class="oscar-weather-label">' + WEATHER_LABEL + '</span></div>';
  document.body.insertBefore(header, document.body.firstChild);
  syncSubtitleWidth();
}

function updateClock() {
  var now = new Date();
  document.getElementById("oscarTime").textContent =
    new Intl.DateTimeFormat("es-AR", { hour: "2-digit", minute: "2-digit", hour12: true, timeZone: WEATHER_TZ }).format(now);
  document.getElementById("oscarDate").textContent =
    new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric", timeZone: WEATHER_TZ }).format(now);
}

function updateWeather() {
  var url = "https://api.open-meteo.com/v1/forecast?latitude=" + WEATHER_LAT + "&longitude=" + WEATHER_LON +
    "&current=temperature_2m,weather_code&timezone=" + encodeURIComponent(WEATHER_TZ);
  fetch(url).then(function (r) { return r.json(); }).then(function (d) {
    var icon = WEATHER_ICONS[d.current.weather_code] || "🌡️";
    document.getElementById("oscarWeatherTemp").textContent = icon + " " + Math.round(d.current.temperature_2m) + "°C";
  }).catch(function () {});
}

buildOscarHeader();
setInterval(function () { buildOscarHeader(); syncSubtitleWidth(); }, 2000);
updateClock(); setInterval(updateClock, 15000);
updateWeather(); setInterval(updateWeather, 10 * 60 * 1000);
```

Open-Meteo es la misma API pública sin key que ya usaba el widget nativo — acá se llama directo con `fetch`, sin pasar por Homepage. El header entero se inserta en `document.body`, no dentro del contenedor que maneja React, así un re-render de Homepage no lo pisa; el `setInterval` de 2s es red de seguridad + remide el ancho del subtítulo (cambia con el viewport).

`custom.css` pone el header como grid de 3 columnas (`grid-template-columns: 1fr auto 1fr`). Ojo con una distinción que no es obvia: **`justify-self`** posiciona el bloque entero dentro de su columna (fecha pegada al borde izquierdo de la página, clima al derecho — `justify-self: start` / `end`), mientras que **`align-items` del propio `.oscar-col`** centra las dos líneas *entre sí* dentro de ese bloque (hora arriba de fecha, temperatura arriba de ciudad) — son dos ejes de alineación distintos que hay que separar, si se usa solo uno de los dos el bloque termina centrado contra el título en vez de pegado al borde, o las líneas quedan alineadas a un costado en vez de centradas entre ellas. En mobile (`max-width: 640px`) las tres columnas colapsan a una y las tres pasan a `justify-self: center`.

El ícono de clima es SVG inline propio (`WEATHER_SVG` en `custom.js`), no emoji — así el color (blanco, `currentColor`) y la sombra combinan con el resto del texto sin depender de cómo cada sistema operativo dibuje el emoji. Son 7 íconos monolínea (sol, parcialmente nublado, nublado, niebla, lluvia, nieve, tormenta) mapeados desde los [códigos WMO](https://open-meteo.com/en/docs) que devuelve Open-Meteo.

Hora y clima comparten estilo (texto blanco `#f8fafc`, `text-shadow` para separarse de la foto, sin fondo ni borde); fecha y ciudad van más chicas debajo de cada una. El título sigue con la animación de glow tipo aurora, cicla color y sombra entre celeste/verde-agua/violeta cada 6s:

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
- **Los acentos/ñ aparecen como `Ã³`/`Ã±` en `services.yaml`** → dos causas posibles, hay que distinguirlas antes de "arreglar" algo que no está roto:
  1. **El archivo real está corrupto de verdad** → pasó al editarlo con `sed -i` directo en `core01`: el contenedor no tiene una locale UTF-8, y `sed` reinterpreta *todo el archivo* con la locale por defecto al reescribirlo, no solo la línea que toca. La única forma segura de editar este archivo (o cualquiera con tildes) es reescribirlo completo desde una fuente UTF-8 correcta y subirlo por `base64 -d > archivo` — nunca `sed -i` en el contenedor.
  2. **El archivo está bien pero la herramienta de diagnóstico lo muestra mal** → si se inspecciona el contenido pasándolo por la respuesta JSON del `exec-status` de la API de Proxmox (usada para ejecutar comandos en `core01` sin SSH) y se imprime directo, esa capa de transporte re-codifica los bytes UTF-8 y se ve el mismo patrón `Ã³`. Para confirmar cuál de los dos es, pedir el archivo en base64 explícito y decodificarlo del lado de quien lo lee, en vez de confiar en el texto plano que devuelve esa API — si ahí se ve bien, el archivo nunca estuvo roto.
- **Un `<div>` con dos clases distintas hereda un `flex-direction` que no le pusiste** → pasó con `#oscarResourcesSlot`: el mismo elemento tiene `class="oscar-col oscar-col-center"` (que define `flex-direction: column`) **e** `id="oscarResourcesSlot"` con su propio `display: flex`. Como nunca se declaró `flex-direction` en la regla del id, CPU/RAM/disco quedaban apiladas verticalmente en vez de en línea — la especificidad del id gana en las propiedades que sí define (`display`, `gap`, etc.), pero una propiedad que un selector no toca simplemente seguía viniendo del otro. Al reutilizar una clase de layout genérica (`.oscar-col`) en un elemento que también tiene su propio id con reglas de layout, conviene repasar cada propiedad que el genérico define y decidir explícitamente si el id la hereda o la pisa — no asumir que "más específico" alcanza para todo.
