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

### De carrusel a acordeón nativo

Los 3 grupos (Infraestructura, Servicios, Hogar) pasaron por dos experimentos antes de asentarse en su forma actual:

1. **Pestañas nativas de Homepage** (`tab: <nombre>` en `settings.yaml` → `layout:`) + swipe simulado — se sentía a animación, no a gesto real (Homepage desmonta/monta cada tab, nunca coexisten dos paneles).
2. **Carrusel de scroll horizontal** con `scroll-snap`, puntitos de navegación, y arrastre con mouse armado a mano (`mousedown`/`mousemove`/`mouseup` sobre `scrollLeft`) — técnicamente funcionaba (scroll real, no simulado), pero tampoco convenció como experiencia final.

La versión que quedó es la más simple de las tres: **sin ningún JS ni CSS propio para la navegación entre grupos**. Sin `tab:` en `layout:`, los 3 grupos vuelven al comportamiento por defecto de Homepage — todos renderizados juntos, apilados verticalmente — y cada uno ya trae de fábrica su propio acordeón: `ServicesGroup` envuelve el contenido en un [`<Disclosure>`](https://headlessui.com/react/disclosure) de Headless UI, con una flechita que rota y colapsa/expande al clickear el nombre del grupo. Cada grupo es independiente (no es un acordeón estricto — pueden quedar varios abiertos a la vez), y arrancan todos abiertos por default, sin tocar `groupsInitiallyCollapsed` ni `initiallyCollapsed` en ningún grupo.

## Widgets nativos (datos en vivo en la tarjeta)

Además del `siteMonitor` (puntito de estado), **7 de las 13 tarjetas** tienen un `widget:` que muestra datos reales directo en la card en vez de un link plano — Proxmox, AdGuard Home, Cloudflare Tunnel, Uptime Kuma, Beszel, Home Assistant y [MySpeed](./myspeed.md). n8n, Vaultwarden y Glances se quedan con descripción fija: Homepage no tiene una integración nativa para ninguno de los tres — la de Glances existe (es la que usa el header, ver más abajo) pero es para pedir datos puntuales, no para armar una card con métricas en vivo. [Nginx Proxy Manager](./nginx-proxy-manager.md) y el [DVR Dahua](../hogar/cctv-dahua.md) también quedan sin widget por ahora: NPM porque falta cambiar su login de fábrica antes de tener credenciales reales que usar, y el DVR porque Homepage no tiene una integración nativa para DVRs Dahua genéricos.

Glances tenía datos pero no tarjeta: se usaban sus métricas en el header (ver "CPU/RAM/disco y buscador" más abajo) pero nadie podía ir a su UI propia (procesos, red, contenedores — mucho más que lo que muestra el header) sin escribir la IP a mano. Se agregó como card en Infraestructura, al lado de ProxMenux Monitor — mismo criterio que el resto de las herramientas internas sin dominio público (Proxmox, AdGuard, Home Assistant): href a la IP LAN directa, sin pasar por el túnel.

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
  systemId: <id del sistema en Beszel>   # sin esto, "overview" en vez de las métricas reales
  fields: ["cpu", "memory", "disk"]

# Home Assistant — long-lived access token generado a mano desde el perfil de HA
widget:
  type: homeassistant
  url: http://<IP-de-VM-101>
  key: <token, fuera de Git>
  fields: ["people_home", "lights_on", "switches_on"]

# MySpeed
widget:
  type: myspeed
  url: http://<IP-de-core01>:5216
  fields: ["ping", "download", "upload"]

# Uptime Kuma — se le sumó "uptime" al default (up/down) para ver el % real
widget:
  type: uptimekuma
  url: http://<IP-de-core01>:3001
  slug: oscar
  fields: ["up", "down", "uptime"]
```

### El bug de Beszel: "overview" en vez de las métricas reales

El widget de Beszel llevaba semanas configurado sin `systemId` — sin ese dato, Homepage lo pone en modo "overview" (`fields` disponibles: `systems`, `up` — solo cuenta cuántos sistemas hay conectados y cuántos están arriba), en vez de modo "sistema puntual" (`fields`: `name`, `status`, `updated`, `cpu`, `memory`, `disk`, `network` — las métricas reales de `core01`). La tarjeta nunca mostró un error, simplemente mostraba información **real pero irrelevante** ("1 sistema, 1 arriba" en vez de "CPU 4.6%, RAM 19%, disco 21%") — el tipo de bug que no salta a la vista si no se sabe qué buscar.

El `systemId` de `core01` se sacó de la propia base de Beszel (es PocketBase por debajo, con su API REST estándar):

```bash
# autenticar como superusuario
curl -X POST 'http://<host-beszel>:8090/api/collections/_superusers/auth-with-password' \
  -H 'Content-Type: application/json' \
  -d '{"identity":"homepage@oscar.home","password":"<password>"}'
# con el token de la respuesta, listar sistemas
curl 'http://<host-beszel>:8090/api/collections/systems/records' \
  -H 'Authorization: <token>'
```

El `id` del sistema `core01` en esa respuesta es el `systemId` que hace falta en `services.yaml`. Nota al margen: el endpoint de auth es `_superusers` (con guion bajo, PocketBase reciente) — `admins` (el nombre viejo) da `404 Missing or invalid collection context`.

### Verificar qué está pidiendo un widget, sin adivinar

Para confirmar qué le llega realmente a una tarjeta (sin esperar a que se refresque sola, o para depurar un widget que "no muestra nada"), Homepage expone su propio proxy interno:

```
GET /api/services/proxy?group=<grupo>&service=<nombre>&index=0&type=<tipo>&endpoint=<endpoint>
```

El `endpoint` no es libre — tiene que ser una de las claves que el widget define en su propio `mappings` (código fuente de Homepage, `src/widgets/<tipo>/widget.js`) — para Beszel es `systems`, no `single_system` ni ningún nombre que suene razonable a ojo. Adivinar el nombre del endpoint devuelve `{"error":"Unsupported service endpoint"}`, no una pista de cuál es el correcto — hay que ir a leer el código fuente del widget puntual para saberlo con certeza.

El token `root@pam!homepage` se creó con `privsep=1` (sin permisos hasta asignarle un rol explícito) — el rol `PVEAuditor` en el path `/` se asignó a mano desde la UI de Proxmox (Datacenter → Permissions → Add → Token Permission), porque asignar roles vía API quedó bloqueado por las reglas de seguridad del entorno de automatización usado para este build.

## Widgets de información — historia (ya no se ven en pantalla)

Los widgets nativos de info (`resources`, `datetime`, `openmeteo`, `search`) van en **`widgets.yaml`**, un archivo separado de `settings.yaml` — es un error fácil de cometer (yo mismo lo cometí primero: los puse dentro de `settings.yaml` bajo una clave `widgets:`, y Homepage los ignoró en silencio sin tirar ningún error; costó varias vueltas de "no veo cambios" hasta confirmar con curl directo al contenedor que el HTML servido no tenía el contenido nuevo).

Dicho esto: hoy **ninguno de los cuatro se ve en pantalla**. `datetime`, `openmeteo` y `search` se reemplazaron por versiones propias en `custom.js` (ver las secciones de abajo), y `resources` quedó reemplazado por `glances`, configurado pero oculto (ver "CPU/RAM/disco y buscador" más abajo). Lo único que queda en `widgets.yaml` es:

```yaml
# widgets.yaml
- glances:
    url: http://192.168.0.156:61208
    version: 4
    cpu: true
    mem: true
    disk: /hostroot
    expanded: true
```

`settings.yaml` solo tiene título/tema/layout/idioma/fondo — nada de widgets de info ahí, esa es justo la confusión de arriba.

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

### Aurora animada encima de la foto

El pedido fue literal: "que la foto de fondo tenga algo animado tipo aurora". Antes de escribir código se revisó cómo Homepage arma el fondo ([`pages/index.jsx`](https://github.com/gethomepage/homepage/blob/main/src/pages/index.jsx), [`styles/globals.css`](https://github.com/gethomepage/homepage/blob/main/src/styles/globals.css)): la foto vive en un `<div id="background">` con `position: fixed; inset: 0; z-index: 0`, hermano de `#page_wrapper` (el contenido real) — sin ese div, no hay dónde "engancharse" con seguridad.

`buildAuroraBackground()` en `custom.js` inserta un nuevo `<div id="oscar-aurora-bg">` **como hermano de `#background`, inmediatamente después** (`insertAdjacentElement("afterend", ...)`) — nunca adentro, nunca reemplazándolo. Con el mismo `z-index: 0` pero apareciendo más tarde en el DOM, pinta arriba de la foto y abajo de `#page_wrapper` (que sigue viniendo después todavía) — es el mismo principio de "agregar un nodo nuevo, nunca tocar uno existente" que ya rigió todo el header.

Adentro van 3 manchas de color (`div.oscar-aurora-blob`) grandes (45-55% del ancho de pantalla), borroneadas (`filter: blur(70px)`) y con los mismos 3 colores del brillo animado del título — cian `#38bdf8`, verde-agua `#5eead4`, violeta `#a78bfa`. Cada una deriva sola con su propio `@keyframes` (`translate` + `scale`, 16s/20s/24s, todas con duración distinta para que nunca se sincronicen) — es pura animación CSS, sin ningún loop de JS corriendo, así que el costo real es GPU compositing, no CPU.

El contenedor entero tiene `mix-blend-mode: screen`: en vez de tapar la foto con manchas de color planas, **suma luz** sobre lo que ya está debajo — el mismo comportamiento que la luz real de una aurora sobre el cielo nocturno, no una capa opaca encima. Respeta `prefers-reduced-motion`.

La primera versión (`opacity: 0.55`, `blur(90px)`, recorridos de 6-10vw, duraciones de 26-38s) casi no se notaba — el pedido fue "hacé que se note un poco más". Se subió `opacity` a `0.8`, se bajó el blur a `70px` (manchas más definidas), se duplicó aproximadamente el recorrido de cada `@keyframes` (hasta 14-20vw) y se acortaron las duraciones (16-24s) — mismo movimiento orgánico, más rápido y más amplio.

## Identidad visual (custom.css)

Homepage carga `config/custom.css` automáticamente (se sirve en `/api/config/custom.css`, referenciado por la propia página) — no hace falta tocar nada del compose, solo poner el archivo ahí. Se usó para:

- fondo con foto real (ver arriba) — antes era un gradiente + grilla en CSS puro, sin imagen que hostear; se cambió cuando apareció una imagen mejor;
- tarjetas de servicio (`.service`) con borde y efecto hover en vez del recuadro plano default;
- nombres de grupo (`.service-group-name`) en mayúsculas con acento celeste, estilo "consola";
- la barra de widgets superior (`.widget-container`) separada visualmente en pastillas, para que CPU/RAM/disco/reloj/clima/buscador no se vean todos pegados.

Los nombres de clase (`.service`, `.service-name`, `.service-description`, `.service-group-name`, `.widget-container`) salen del código fuente de Homepage (`src/components/services/item.jsx` y `group.jsx`), no de la documentación pública — no están listados en `docs/configs/custom-css-js.md`, hubo que revisar el repo directo.

### Números de los widgets: más peso visual, un color de acento por grupo

Cada estadística de un widget nativo (los recuadros con un valor y una etiqueta abajo — "23%", "CPU", etc.) es un `.service-block` dentro de un `.service-container` (`src/components/services/widget/{block,container}.jsx` de Homepage) — sin nombre de clase propio para el valor y la etiqueta por separado, son simples `<div>` con clases utilitarias de Tailwind (`font-thin text-sm` el valor, `font-bold text-xs uppercase` la etiqueta). Por defecto se veían chicos y apagados contra la foto de fondo — para un widget cuya única razón de existir es mostrar un número real, que ese número no se lea bien es el peor resultado posible. Se le subió tamaño/peso al valor (`.service-block > div:first-child`, ahora `0.95rem`/`700`/`tabular-nums`) y se le dio a cada bloque un fondo sutil propio con borde, en vez de flotar suelto contra la tarjeta.

Los 3 grupos (Infraestructura, Servicios, Hogar) pasaron a tener cada uno su propio color de acento en el nombre — cian, verde-agua, violeta, el mismo trío que ya usa el brillo del título, la aurora del fondo y las barras de CPU/RAM/disco del header — en vez de los 3 en el mismo celeste. Como Homepage no expone el nombre del grupo como atributo de datos, el color se asigna por posición (`#services > .services-group:nth-of-type(1|2|3) .service-group-name`) — funciona porque, sin tabs ni carrusel, los 3 grupos son hermanos apilados siempre en el mismo orden.

## CPU/RAM/disco y buscador: reconstruidos, no reubicados

Layout final pedido, en 2 filas apiladas:

```
[ clima ]      O.S.C.A.R.      [ hora/fecha ]
              subtítulo
─────────────────────────────────────────────
[ buscador ]     saludo     [ CPU · RAM · Disco ]
```

Pasó por varias versiones intermedias antes de esta: primero clima/CPU-RAM-disco/hora los 3 en una fila con el título arriba de todo; después el título arriba y esa fila (con recursos en el centro) abajo, entre dos líneas; después recursos y buscador en dos filas separadas, cada una centrada; después esas mismas dos filas, cada una pegada a un borde (buscador a la izquierda, recursos a la derecha) pero todavía apiladas una arriba de la otra. Ninguna terminaba de convencer — la versión final: título+subtítulo en el centro de la fila de arriba (reemplazando ahí a los recursos), y abajo de la línea divisoria, **una sola fila** con el buscador a la izquierda y CPU/RAM/disco a la derecha, `justify-content: space-between` en `.oscar-row-bottom` en vez de dos filas con `flex-start`/`flex-end` por separado.

En el HTML de `buildOscarHeader()` esto es: `.oscar-col-center` (adentro de `.oscar-row-top`) pasó de contener `#oscarResourcesSlot` a contener el `<span class="oscar-title">` y el `<span class="oscar-subtitle">`; y `#oscarResourcesSlot` se independizó en su propia fila (`<div class="oscar-row-resources" id="oscarResourcesSlot">`), fuera del grid de 3 columnas. `.oscar-row-top` solo necesita `border-bottom` ahora — ya no está encerrada entre dos bloques, es la primera fila del header.

El clima y la hora/fecha arrancaron al revés (hora a la izquierda, clima a la derecha) y se intercambiaron de lado después — no hay una razón funcional para uno u otro orden, fue puramente estético. El intercambio es un cambio de una línea en `buildOscarHeader()`: qué `<span>`s van adentro de `.oscar-col-left` vs `.oscar-col-right`, sin tocar CSS (esas clases solo fijan el borde de alineación de la columna, no el contenido).

La fecha lleva un ícono de calendario al lado, y "Buenos Aires" un pin de ubicación — mismo estilo SVG de trazo que el resto (`CALENDAR_SVG`/`PIN_SVG` en `custom.js`, clase `.oscar-inline-icon` en el CSS). En la fecha, el ícono va en un `<span>` separado del texto (que sigue siendo `#oscarDate`, actualizado por `updateClock()`) — necesario porque `textContent` pisaría cualquier HTML que estuviera adentro del mismo nodo, incluido el ícono.

### Primer intento (revertido): mover los nodos nativos con `appendChild`

La primera versión sacaba los widgets nativos `resources`/`search` de la fila donde Homepage los renderiza por defecto y los movía, con `appendChild`, a los contenedores del header custom — mismo nodo real de React, solo reposicionado. Funcionaba visualmente, pero **rompía la página entera de a ratos** con:

```
NotFoundError: Failed to execute 'removeChild' on 'Node':
The node to be removed is not a child of this node.
```

Causa: el widget de recursos se refresca cada 1.5s vía React (`refreshInterval` interno). En algún ciclo de ese refresco, React intentó actualizar/reemplazar ese nodo **en su ubicación original** — pero ya no estaba ahí, porque `appendChild` lo había movido a otro lado del árbol. React no busca el nodo por posición en el documento en cada actualización; guarda una referencia directa, así que mover el nodo no rompe los *cambios de contenido* (por eso "funcionaba visualmente" un rato) — pero si React necesita tocar el **padre original** (insertar/quitar un hermano, por ejemplo en un remount del árbol), encuentra una estructura que ya no coincide con lo que espera, y explota. Es información que no está en ninguna documentación de Homepage — se encontró en producción, con la página realmente caída.

### Solución real: reconstruir todo desde cero, nunca mover nodos ajenos

Ninguno de los 4 bloques del header es hoy un widget nativo reposicionado. CPU/RAM/disco y el buscador se arman en `custom.js`, igual que ya se hacía con el reloj y el clima:

```js
function formatGB(bytes) {
  return (bytes / 1024 / 1024 / 1024).toFixed(1);
}

function updateResources() {
  var slot = document.getElementById("oscarResourcesSlot");
  fetch("/api/widgets/glances?index=0&version=4&disk=1")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      // CPU: % + núcleos · RAM: % + "usado/total GB" · disco: % + "usado/total GB"
      // (mnt_point === "/hostroot", el bind mount de solo lectura de la raíz del host)
    });
}
setInterval(updateResources, 5000);
```

`/api/widgets/glances` es la ruta **interna** de Homepage (mismo origen que la página) — el mismo endpoint que usaba el widget nativo por debajo. Pedirle los datos directo a Glances (`http://192.168.0.156:61208`) desde el navegador **no funciona para nadie que entre desde fuera de la LAN**: es una IP privada, e ir por afuera del túnel es exactamente el problema que Cloudflare Tunnel existe para resolver. Pasar por la ruta interna de Homepage evita ese problema (Homepage llama a Glances del lado del servidor) y de paso evita CORS.

### De texto chico a barra de progreso

La primera versión de este bloque era solo ícono + `%` en texto chico — poco legible de un vistazo, y sin el valor absoluto (cuántos GB usados de cuántos totales), que es la parte que más importa para saber si hay margen real. Se probó también un gauge circular (SVG, % adentro del anillo) — más grande, pero seguía sin transmitir de un vistazo "qué tan cerca del límite" tan bien como una barra horizontal, y ocupaba más alto que ancho. La versión final: tres columnas lado a lado (CPU, RAM, Disco), cada una con un ícono grande a la izquierda y, a la derecha, 3 líneas — nombre, el rango real, y la barra de progreso con el `%` al lado —

```
     ┌ CPU              ┌ RAM              ┌ Disco
[i]  │ 2 núcleos    [i]  │ 1.4/8.0 GB   [i]  │ 10.1/57.1 GB
     └ [▓▓░░░] 18%       └ [▓▓░░░] 17%       └ [▓▓░░░] 18%
```

```js
var RESOURCE_BASE_COLOR = { cpu: "#38bdf8", mem: "#5eead4", disk: "#a78bfa" };

function resourceColor(key, pct) {
  if (pct >= 90) return "#f87171"; // rojo — crítico
  if (pct >= 75) return "#fbbf24"; // ámbar — atención
  return RESOURCE_BASE_COLOR[key] || "#38bdf8";
}

function resourceItemHtml(key, pct, name, detailText) {
  var color = resourceColor(key, pct);
  // ícono grande a la izquierda; a la derecha, un <div class="oscar-bar-body">
  // de 3 líneas (nombre, valor, barra+%). La barra es un
  // <div class="oscar-bar-track"> con un <div class="oscar-bar-fill"> cuyo
  // width inline es "pct%" y cuyo background es `color` — sin SVG ni canvas.
}
```

El color base es distinto por recurso (cian CPU, verde-agua RAM, violeta disco — la misma paleta del brillo del título) tanto en el ícono como en el relleno de la barra, pero por encima de 75% pasa a ámbar y por encima de 90% a rojo, sin importar cuál sea. El criterio de esos dos umbrales salió directo de lo que pasó con la RAM: llegar al 91% real fue lo que forzó [subir `core01` de 4 a 8 GB](../proxmox/crear-vm-core01.md#sizing-inicial) — la idea es que la próxima vez que algún recurso se acerque a ese punto, se note en el dashboard sin tener que ir a mirar Glances aparte.

El ícono se agrandó a propósito (1.8rem, casi el doble del que tenía al lado del nombre en la versión anterior) y quedó **en paralelo** con las 3 líneas de texto, no arriba de ellas — así su alto no se suma al del texto, sino que compite con él por el más alto de los dos. Eso deja a toda la columna de recursos con una altura parecida a la del bloque hora/fecha y al de clima, que son los otros dos bloques de esta misma fila — el objetivo era que las tres columnas se sientan del mismo peso visual, no que una quede visiblemente más chica que las otras dos.

El valor real (`2 núcleos`, `1.4/8.0 GB`) se agrandó de 0.62rem a 0.72rem — es el dato que más importa de las 3 líneas y el que menos peso visual tenía. Para compensar el espacio que ganó, se achicó el `gap` entre el nombre de arriba y el bloque valor+barra de abajo (`.oscar-bar-body`, de 0.15rem a 0.05rem) — menos interlineado entre el título y el resto, para que las 3 líneas se lean como un solo bloque compacto en vez de tres líneas sueltas.

El widget `glances` **sigue existiendo** en `widgets.yaml` — hace falta que esté configurado ahí para que esa ruta interna funcione (Homepage busca la URL/versión/disco por índice en su config real, no por lo que se le pase en la query). Lo que cambia es que ya no se muestra: se oculta con CSS, sin tocarlo de ningún otro modo —

```css
.information-widget-resource,
.information-widget-link {
  display: none !important;
}
```

`display: none` no mueve ni desconecta el nodo del árbol de React — sigue exactamente donde Homepage lo puso, actualizándose cada 1.5s sin que nadie le preste atención. Es la diferencia clave con el intento anterior: ocultar es seguro, reubicar no.

`.information-widget-link` se sumó después: Homepage envuelve **todo** el widget de recursos en un `<a href="...">` que apunta a la URL configurada en `widgets.yaml` (`http://192.168.0.156:61208`, la IP LAN de Glances) — ocultar solo `.information-widget-resource` (el contenido de adentro) dejaba ese `<a>` vacío pero seguía ahí, clickeable: un botón gris sin texto ni ícono que llevaba directo a la UI de Glances en la LAN. Se encontró en producción — el usuario lo reportó como "un botón que no dice nada". Hubo que ocultar el wrapper entero, no solo su contenido.

El buscador es más simple todavía — un `<input>` propio que en `Enter` abre `https://www.google.com/search?q=...` en una pestaña nueva. No hay necesidad de reusar el widget nativo de búsqueda para algo tan básico. Comparte fila con CPU/RAM/disco: `.oscar-row-bottom` los pone a los dos en la misma línea, buscador a la izquierda y recursos a la derecha (`justify-content: space-between`), no en dos filas apiladas.

### Saludo según la hora, no el widget nativo "greeting"

Homepage tiene un widget de información llamado `greeting` (texto fijo, sin franja horaria, configurable en `widgets.yaml`) — pero vive en la barra de widgets de arriba, que en este header ya no existe (la reemplazó por completo el header custom). En vez de intentar reubicar ese widget nativo (la lección de siempre: no tocar nodos que React maneje), se construyó uno propio: `updateGreeting()` calcula la hora en la misma zona horaria que el reloj (`WEATHER_TZ`) y arma el texto en `<span id="oscarGreeting">`, insertado como elemento central de `.oscar-row-bottom`, entre el buscador y los recursos.

La primera versión tenía una sola frase fija por franja horaria ("Buenos días"/"Buenas tardes"/"Buenas noches"). El pedido fue que variaran y tuvieran que ver con el homelab — se armó un pool de 4 frases por franja (madrugada/mañana/tarde/noche), todas relacionadas a O.S.C.A.R./el rack/`core01`, y en cada actualización se elige una al azar dentro de la franja que corresponda:

```js
var GREETING_PHRASES = {
  madrugada: ["El rack nunca duerme", "core01 sigue despierto", /* ... */],
  mañana: ["Arrancando el día con O.S.C.A.R.", /* ... */],
  tarde: ["La tarde avanza, el rack no para", /* ... */],
  noche: ["O.S.C.A.R. cuidando el homelab mientras descansás", /* ... */]
};

function updateGreeting() {
  var hour = /* hora actual en WEATHER_TZ */;
  var bucket = hour < 6 ? "madrugada" : hour < 12 ? "mañana" : hour < 20 ? "tarde" : "noche";
  var phrases = GREETING_PHRASES[bucket];
  el.textContent = phrases[Math.floor(Math.random() * phrases.length)];
}
```

Se actualiza cada 45 segundos (bajado de 5 minutos — a 5 minutos el cambio no se notaba sin dejar la pantalla abierta un buen rato) — el pool (7 frases por franja, subido de las 4 iniciales) da margen de sobra para no repetirse siempre igual dentro de una misma franja horaria (aunque, al ser al azar, nada impide que salga la misma frase dos veces seguidas — si el sorteo repite la frase actual, `updateGreeting()` no dispara la transición). El texto también se agrandó dos veces (0.78rem → 1.05rem → 1.25rem, peso 700) para que pese más que el resto de la fila, no solo lo mismo.

El cambio de frase tiene un fundido simple: se lleva `opacity` a `0` (con `transition: opacity 0.3s ease` en `.oscar-greeting`), se espera esos 300ms con `setTimeout`, recién ahí se cambia el `textContent`, y se vuelve a `opacity: 1` — evita el salto brusco de un texto reemplazándose de golpe.

**Centrado real, no "en el medio del espacio sobrante":** con `justify-content: space-between` (buscador a la izquierda, recursos a la derecha, saludo en el medio), el saludo quedaba centrado *entre los otros dos elementos*, no en el centro real de la página — si el buscador y los recursos no miden lo mismo, ese "medio" se corre para un lado. Se cambió a la misma técnica que ya usa `.oscar-row-top` para centrar el título: grid de 3 columnas `1fr auto 1fr`, con el buscador en `justify-self: start` y los recursos en `justify-self: end` — así el elemento central queda matemáticamente centrado en el ancho total de la fila, sin importar cuánto midan los costados.

La primera versión era un `<input>` sin caja, solo con una línea (`border-bottom`) debajo del texto — funcional pero se perdía contra el resto del header. Se rediseñó como una píldora "glass": fondo semitransparente con `backdrop-filter: blur(8px)`, borde sutil, `border-radius: 999px`, y un ícono de lupa (`SEARCH_SVG`) a la izquierda del texto.

Se probó también un brillo cian en el borde + `box-shadow` al enfocar el input (con `:focus-within` en el contenedor) — no gustó, se sacó. Hoy la píldora se ve igual esté enfocada o no: sin `:focus-within`, y el `<input>` con `outline: none` y `box-shadow: none` explícitos para que tampoco aparezca el foco azul por defecto del navegador. También se agrandó: ícono más grande (0.95rem → 1.1rem), texto más grande (0.8rem → 0.88rem) y, sobre todo, más ancho (`min-width` del input, 200px → 340px) — que fue el pedido concreto ("más grande" quería decir más ancho, no más alto). El padding vertical de la píldora se probó más grande primero (0.65rem) y después se achicó (0.4rem) para bajarle el alto sin tocar el ancho.

**Regla que queda de esto para cualquier próxima idea de "reposicionar un widget nativo de Homepage con JS":** no. Si hace falta en otro lugar del layout, se reconstruye desde cero (fetch a la ruta interna si hay datos reales de por medio, como acá) y se oculta el original con `display: none`, nunca se lo mueve por el DOM.

### Por qué los datos vienen de `glances`, no de `resources`

El widget nativo `resources` de Homepage, sin nada más, mide el **contenedor de Homepage**, no `core01` entero — CPU y RAM son las del propio proceso de Homepage (casi siempre ~0%, porque es una app liviana), no las de la VM completa. El disco tenía el mismo problema (`disk: /` apuntaba al filesystem interno del contenedor). No hay forma de arreglar eso desde adentro del propio contenedor de Homepage — hace falta un agente con visibilidad real del host.

Por eso [Glances](./glances.md) corre aparte, con `network_mode: host` + `pid: host` en `core01`, y `widgets.yaml` usa el widget `glances` (no `resources`) para tener esos datos disponibles del lado del servidor:

```yaml
# widgets.yaml — el único widget nativo que queda; no se muestra en pantalla
# (ver "Solución real" arriba), pero tiene que seguir configurado acá para
# que /api/widgets/glances tenga de dónde sacar los datos.
- glances:
    url: http://192.168.0.156:61208
    version: 4
    cpu: true
    mem: true
    disk: /hostroot
    expanded: true
```

`expanded: true` no cambia nada en pantalla (el widget nativo está oculto), pero sí afecta qué campos trae la respuesta de `/api/widgets/glances`, que es lo que `custom.js` lee. También se agregó `language: es` en `settings.yaml` — no le pega a esta parte reconstruida a mano, pero sigue siendo relevante para cualquier otro widget nativo de Homepage que se use en el futuro.

Instalar Glances también dejó en evidencia que **`core01` estaba al 91% de RAM** (4 GB asignados, con 9 contenedores reales corriendo) — se subió a 8 GB antes de sumarle uno más. Ver [creación de `core01`](../proxmox/crear-vm-core01.md#sizing-inicial).

## Header de 3 columnas: hora/fecha · O.S.C.A.R. · clima (custom.js)

Homepage no tiene ningún lugar nativo para mostrar el nombre del proyecto en grande — el `title` de `settings.yaml` solo va al `<title>` del navegador y al manifest PWA, y el único widget relacionado ("logo") es un ícono de 48×48px, sin texto. La primera versión fue solo el título centrado con `datetime`/`openmeteo` como widgets nativos de Homepage abajo — pero esos widgets traen su propia caja/fondo (`.widget-container`) sin margen real para estilar cada uno suelto. Se reemplazó por un reloj y un clima **construidos desde cero** en `custom.js`, en 3 columnas: hora/fecha a la izquierda, "O.S.C.A.R." al centro, clima a la derecha — texto blanco sin caja, solo con sombra para que resalte contra la foto de fondo:

:::note Snapshot histórico, no el archivo completo actual
El bloque de abajo es la versión que agregó el reloj/clima por primera vez (con íconos emoji). Después se sumaron los íconos SVG, la fila de CPU/RAM/disco y el buscador (ver "CPU/RAM/disco y buscador" más arriba) al mismo `custom.js` — se deja este fragmento porque explica bien el razonamiento original de las 3 columnas, no porque sea el archivo completo tal cual está hoy en `core01`.
:::

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
- **Un botón gris sin texto ni ícono, que lleva a la IP LAN de un servicio (ej. `192.168.0.156:61208`, Glances)** → un widget nativo oculto solo a medias. Homepage envuelve el widget entero en un `<a class="information-widget-link">` que apunta a la `url` de `widgets.yaml`; si el CSS solo oculta el contenido de adentro (`.information-widget-resource` en este caso) el `<a>` sigue ahí, vacío pero clickeable. Hay que ocultar también `.information-widget-link` — ver la sección de arriba sobre CPU/RAM/disco. Para confirmar qué widget es el culpable antes de tocar CSS a ciegas: `curl -s -H "Host: <lo que use HOMEPAGE_ALLOWED_HOSTS>" http://localhost:3005/ | grep -o '<a href="http://<ip-sospechosa>"[^>]*>'` — la clase del `<a>` dice qué widget es (`information-widget-<nombre>`).
- **Doble scroll vertical (una barra en el borde de la página, otra más adentro)** → Homepage arma `#page_wrapper`/`#inner_wrapper` con `height: 100%` + `overflow-auto`, pensados como una caja interna del alto del viewport que scrollea sola. `#oscar-header` se inyecta como hijo de `<body>`, *antes* de esa caja — suma su propio alto por encima, el documento entero termina más alto que un viewport, y el navegador le agrega su propio scroll externo además del interno: dos barras.
  - **Primer intento (revertido): `body` a flex-column, con `#page_wrapper` ajustado por `flex` al espacio libre bajo el header** (header fijo arriba, caja interna del alto restante). Funcionaba, pero se sentía como un scroll "encajonado" en una caja interna, no como el de una página común — no convenció.
    - Dentro de ese intento, la primera variante (`flex:1 1 0%; height:0` en `#page_wrapper`) **hizo desaparecer todas las tarjetas de servicio**: ese `height:0` explícito, combinado con `flex-basis:0%`, terminaba resolviendo la altura real de `#page_wrapper` en 0 en vez de dejar que `flex-grow` la expandiera — y como `#inner_wrapper` calcula su alto como `100%` de `#page_wrapper`, también quedaba en 0, ocultando los grupos de servicios sin ningún error visible. La forma correcta de esa técnica hubiera sido `flex: 1 1 auto` + `min-height: 0` (el default de un ítem de flex es `min-height: auto`, que le impide encogerse por debajo de su contenido — `min-height:0` saca esa traba) — pero el resultado visual seguía sin convencer.
  - **Solución final: anular la caja interna, no compensarla.** En vez de mantener `#inner_wrapper` como una caja de scroll propia y hacerle lugar al header con flexbox, se le anula directamente el `h-full`/`overflow-auto` a `#page_wrapper` y `#inner_wrapper` (`height: auto; overflow: visible`) — dejan de imponer su propia superficie de scroll, y el documento fluye normal. `html`/`body` quedan como la **única** superficie de scroll, moviendo todo junto (header incluido, que ahora sí se puede scrollear fuera de vista) como cualquier página web común — más simple que la variante con flexbox, y es el resultado que se sentía "nativo".
  - Primera pasada de este fix (solo `#page_wrapper`/`#inner_wrapper` sin tocar `html`/`body`) dejó la página **sin ningún scroll** — ni interno ni externo: el contenido desbordaba, pero `html`/`body` seguían con `height: 100%` (fijo, no `auto`) del CSS base de Homepage, y en esa combinación el navegador no generaba una superficie de scroll para alcanzar lo que desbordaba. Se sumó `html, body, #__next { height: auto !important }` — saca el `100%` fijo de toda la cadena, así el documento crece con su contenido real en vez de quedar atado a la altura del viewport.
  - **Pedido final: header fijo arriba, todo lo demás scrollea debajo.** `#oscar-header` pasó de `position: relative` a `position: fixed; top:0; left:0; right:0` — al sacarlo del flujo del documento por completo, **ya no puede volver a sumar su alto al de `#page_wrapper`**, sea cual sea el resto del CSS: es la causa raíz del doble scroll resuelta de una vez, no un ajuste alrededor de ella. Como un elemento `fixed` no empuja a nada, `#page_wrapper` necesita un `padding-top` del mismo alto que el header para que el contenido no arranque tapado debajo — `wireHeaderOffset()` en `custom.js` lo mide en vivo con `getBoundingClientRect().height` (nunca un valor fijo a mano, porque el alto real del header cambia según el ancho de pantalla) y lo mantiene al día con un `ResizeObserver` sobre el propio header, sin sondear a mano. `html`/`body` con `overflow: auto`/`height: auto` (ya establecido en el punto anterior) siguen siendo la única superficie de scroll — ahora simplemente el header no participa de ella.
    - **Header transparente + `fixed` = "se pisa" aunque el z-index esté bien.** El header nunca tuvo `background` propio (vivía sobre la foto/aurora, pensado para leerse con solo texto+sombra) — al volverse `fixed`, las tarjetas que scrollean por detrás quedan técnicamente en un nivel de apilamiento más bajo (`z-index: 30` en el header les gana), pero como el header es transparente, esas tarjetas se siguen viendo *a través* de él — visualmente da la sensación de que se superponen, aunque el orden de apilamiento sea correcto.
      - Primer intento: fondo oscuro bastante opaco (`rgba(11,15,20,0.88)`) + blur chico (`14px`) — tapaba bien, pero se veía como un bloque negro sólido pegado arriba, sin relación con la foto/aurora de fondo. No gustó.
      - Versión final: **casi sin tinte, todo el trabajo lo hace el blur.** `background: rgba(11,15,20,0.25)` (mucho más sutil) + `backdrop-filter: blur(26px) saturate(150%)` — el mismo criterio que la barra de menú de iOS/macOS: lo que pasa por detrás sigue estando ahí (se nota que hay algo, y los colores de la foto/aurora se cuelan desenfocados), pero queda completamente ilegible por el blur tan fuerte, sin necesidad de tapar todo con un color plano. El `saturate(150%)` compensa que un blur intenso tiende a lavar los colores — los mantiene vivos en vez de verse grises.
      - **El vidrio esmerilado solo aparece al scrollear, no todo el tiempo.** Arriba de todo (`scrollY = 0`) el header queda `background: transparent` — se ve la foto/aurora limpia, sin nada tapando. `wireHeaderScrollEffect()` escucha el evento `scroll` en `window` y le agrega la clase `.oscar-header-scrolled` (la que trae el fondo+blur) apenas se pasa un umbral chico (`scrollY > 12px`, para no activarse con el rebote elástico de un trackpad en la posición 0), sacándosela de nuevo si se vuelve arriba del todo. El cambio entre un estado y otro lo anima el `transition` del CSS (`background`/`box-shadow`/`backdrop-filter`, 0.35s) — el JS solo agrega o saca una clase, nunca anima nada a mano.
- **Un widget de Homepage se agrega a un elemento centrado con `flex` + `space-between` y no queda en el centro real de la página** → `space-between` centra un elemento del medio *entre los otros dos*, no en el centro geométrico de la fila — si esos otros dos no miden lo mismo, el del medio se corre. La forma de centrar de verdad (la que ya usa `.oscar-row-top` para el título) es un grid de 3 columnas `1fr auto 1fr`: las dos columnas de los costados, al ser fracciones iguales, dejan siempre el mismo espacio de sobra a cada lado sin importar cuánto midan los elementos — el del medio (`auto`) queda matemáticamente centrado.
