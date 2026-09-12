---
title: go2rtc (cámaras)
sidebar_position: 28
---

# go2rtc

**Estado:** Retirado — la tarjeta del DVR volvió a ser un link simple con chequeo de estado (ver [Homepage](./homepage.md#dvr-dahua-de-video-en-vivo-a-solo-estado))
**Dónde corría:** Docker Core (`/srv/oscar/apps/go2rtc/`) — contenedor parado (`docker compose down`), archivos sin borrar en `core01`
**Sizing inicial:** liviano (un solo binario Go, imagen oficial `alexxit/go2rtc:1.9.14`)
**Red/puertos:** `1984` (ya no en uso)
**Alcance:** solo LAN — sin dominio público, sin Cloudflare Tunnel ni Access

:::note Por qué se retiró
Después de resolver casi todo (HD real, LAN-only, página propia con el estilo del dashboard) quedó pendiente un problema de orientación: 3 de las 4 cámaras graban en "modo pasillo" y el DVR las rota al mostrarlas — el RTSP crudo no trae esa rotación, y ninguno de los dos sentidos de giro probados en CSS (`rotate(90deg)`/`rotate(-90deg)`) coincidía con cómo se ven en el monitor real del DVR. En vez de seguir iterando, la decisión fue frenar del todo: **no vale la pena seguir invirtiendo tiempo y recursos en tener video de las cámaras dentro de Homepage** — la tarjeta volvió a ser un link + chequeo de estado, como la mayoría de las demás. Se deja esta página como referencia técnica (el truco de `static_dir`, el de rotación con unidades de container query, el porqué de LAN-only) por si en algún momento se retoma.
:::

## Rol dentro de O.S.C.A.R. (histórico)

Reemplazó a [DVR Proxy](./dvr-proxy.md) para ver las cámaras del [DVR Dahua](../hogar/cctv-dahua.md) — mismo objetivo (video en la tarjeta de Homepage y en una grilla de las 4, sin abrir la app nativa del DVR), pero por un camino distinto: en vez de que el proxy le hable HTTP al DVR y reenvíe eso, go2rtc le hablaba **RTSP** — el protocolo nativo de streaming de cualquier cámara/DVR IP, mucho más apto para esto que HTTP — y lo reempaquetaba en formatos que un navegador puede reproducir directo.

### Por qué go2rtc y no Frigate

El pedido original era Frigate (grabación continua + detección de movimiento/objetos con IA). Antes de instalarlo se revisaron los recursos reales de `core01`: **2 vCPUs, sin GPU/`/dev/dri`, 45GB libres de disco compartidos con el resto de los servicios** (Homepage, n8n, Beszel, NPM, etc.). Frigate completo hubiera competido por esas 2 vCPUs con todo lo demás corriendo en la misma VM, y llenado el disco en días con grabación 24/7 de 4 canales. go2rtc es el mismo motor de re-streaming que usa Frigate por debajo, pero **sin detección ni grabación** — solo relayea video, con un consumo de CPU/disco mínimo (confirmado en producción: ~8% de una vCPU y 45MB de RAM con las 4 cámaras en HD conectadas al mismo tiempo). Si en algún momento se suma más CPU dedicada o un acelerador (Coral, iGPU con passthrough) a `core01`, Frigate vuelve a ser una opción real — hoy no lo era.

### Por qué solo LAN

La primera versión de esto se publicó por el Cloudflare Tunnel (`cam.oscarlab.com.ar`) con una app de Access adelante — mismo patrón que el resto de los servicios de esta cuenta, protegido con login. Después de verlo funcionando, la decisión fue sacarlo igual: **cámaras de seguridad son un caso distinto** — tener cualquier puerta hacia internet, aunque esté atrás de autenticación, no daba la tranquilidad que sí da para el resto de los servicios (Homepage, Beszel, etc.). Se dio de baja el hostname público entero — DNS, la app de Access y la regla del Tunnel — y `go2rtc` quedó escuchando solo en la IP LAN de `core01`, sin ninguna puerta de entrada desde afuera. La consecuencia directa: las cámaras (tarjeta y grilla) solo cargan estando conectado a la red de casa; no hay, por ahora, ninguna forma de verlas de lejos (una VPN propia tipo Tailscale/WireGuard sería el camino si en algún momento se quiere eso, sin volver a exponer nada directamente a internet).

## Instalación

`compose.yaml`:

```yaml
services:
  go2rtc:
    image: alexxit/go2rtc:1.9.14
    container_name: go2rtc
    restart: unless-stopped
    ports:
      - "1984:1984"
    volumes:
      - ./go2rtc.yaml:/config/go2rtc.yaml:ro
      - ./www:/config/www:ro
```

`go2rtc.yaml` (no versionado — las credenciales del DVR viven solo acá, mismo tratamiento que tenía el `.env` de `dvr-proxy`):

```yaml
api:
  listen: ":1984"
  static_dir: "/config/www"

streams:
  cam1: "rtsp://admin:<password-del-DVR-urlencoded>@192.168.0.224:554/cam/realmonitor?channel=1&subtype=0"
  cam2: "rtsp://admin:<password-del-DVR-urlencoded>@192.168.0.224:554/cam/realmonitor?channel=2&subtype=0"
  cam3: "rtsp://admin:<password-del-DVR-urlencoded>@192.168.0.224:554/cam/realmonitor?channel=3&subtype=0"
  cam4: "rtsp://admin:<password-del-DVR-urlencoded>@192.168.0.224:554/cam/realmonitor?channel=4&subtype=0"
```

`subtype=0` pide el stream principal del DVR (calidad completa) — la primera versión usaba `subtype=1` (el substream, menor resolución) con el criterio de que iba a salir por internet a través del Tunnel, y convenía algo liviano. Una vez que se decidió que todo esto queda solo en la LAN (ver más abajo), ese motivo dejó de existir — no hay límite de ancho de banda real dentro de la red de casa, así que no tenía sentido seguir viendo las cámaras en baja resolución.

`static_dir: "/config/www"` hace que go2rtc sirva una carpeta propia en vez de su visor HTML de fábrica — ver "Página propia" más abajo.

**Ojo con el `@` de la contraseña**: es el mismo carácter que separa credenciales de host en una URL — si la contraseña lo tiene (como en este caso), hay que mandarlo urlencodeado (`%40`), si no el parser de la URL RTSP corta la contraseña en el lugar equivocado y la conexión falla.

```bash
docker compose up -d
```

Sin `pip install` ni build — la imagen oficial ya trae el binario compilado.

## Página propia, no el visor de fábrica de go2rtc

go2rtc trae un visor HTML propio ya armado (`stream.html`) — se usó al principio, pero tiene la estética genérica de go2rtc (fondo negro liso, texto de debug tipo "mse"/"loading" arriba de cada cámara), nada que ver con el resto del dashboard. Se reemplazó por una página propia (`/srv/oscar/apps/go2rtc/www/index.html`), servida por el propio go2rtc gracias al `static_dir` de arriba — no hace falta un contenedor aparte.

La página reutiliza el motor de video real de go2rtc (`video-rtc.js`, una copia textual del archivo oficial, sin tocar) a través de un `<video-rtc>` (acá renombrado `<cam-video>`, una subclase mínima solo para apagar los controles nativos del navegador y mutear el audio, necesario para que el autoplay funcione sin que el usuario tenga que tocar nada):

```js
class CamVideo extends VideoRTC {
  oninit() {
    super.oninit();
    this.video.controls = false;
    this.video.muted = true;
  }
}
customElements.define("cam-video", CamVideo);
```

Dos modos, según la URL:

- **`?ch=N`** — una sola cámara, sin título ni grilla, el video llena el 100% del espacio disponible. Es lo que usa el `iframe` de la tarjeta en Homepage.
- **sin parámetros** — la grilla completa, las 4 cámaras en un grid 2×2 que ocupa toda la pantalla (sin un ancho máximo fijo como en la primera versión) y se reacomoda solo al redimensionar la ventana, con etiqueta de canal y badge "Vivo" — mismo estilo visual que tenía la vieja página de `dvr-proxy`.

`video.mode = "webrtc,mse,hls"` en los dos modos — WebRTC necesita una conexión de medios UDP directa entre el navegador y `core01`, algo que solo existe estando en la misma LAN (por eso no hubiera servido de nada cuando esto pasaba por el Tunnel, ver "Por qué solo LAN" arriba). Ahora que todo es LAN, WebRTC sí conecta perfecto — es la opción de menor latencia, primera en la lista de prioridad, y de hecho es lo que termina usando el navegador en la práctica.

### Barras negras, no recortada

Las 4 cámaras no comparten la misma orientación: 3 quedaron configuradas en modo vertical (960×1080 real) y 1 en horizontal. En un grid parejo de 2×2, eso deja dos caminos: `object-fit: contain` (se ve la imagen completa, con una franja negra a los costados de las verticales) o `object-fit: cover` (llena la celda entera, recortando arriba/abajo lo que no entra). Se probó primero `cover` — aprovecha mejor el espacio de la pantalla — pero al verlo en vivo se perdía contenido real de la escena en las cámaras verticales (justo lo que uno quiere ver en una cámara de seguridad), así que se volvió a `contain`: nunca se pierde nada, a costa de las franjas negras.

```css
.cam cam-video video { width: 100%; height: 100%; object-fit: contain; }
```

### El problema que no se llegó a resolver: la rotación

3 de las 4 cámaras graban en "modo pasillo" (vertical, pensado para aprovechar mejor un pasillo/balcón angosto) — el propio DVR las rota 90° al mostrarlas en su monitor, pero el RTSP crudo que recibe go2rtc no trae esa rotación aplicada. Se armó una corrección en CSS, detectando solas las cámaras verticales (`videoWidth < videoHeight` una vez que el navegador conoce las dimensiones reales) y rotándolas con `transform: rotate()`, usando unidades de container query (`cqw`/`cqh`) para que el elemento rotado siga ocupando el 100% de su celda sin quedar cortado:

```css
.cam cam-video.rotate {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100cqh;
  height: 100cqw;
  transform: translate(-50%, -50%) rotate(-90deg);
}
```

El truco en sí funcionaba (la imagen pasaba de vertical a horizontal, llenando la celda), pero **ningún sentido de giro coincidió con el monitor real del DVR** — se probaron `rotate(90deg)` y `rotate(-90deg)`, los únicos dos sentidos posibles para pasar de vertical a horizontal, y los dos se reportaron como "se ven mal". No se investigó más a fondo (por ejemplo, si distintas cámaras necesitan sentidos de giro distintos entre sí, en vez de uno global para las tres) porque en ese punto se decidió retirar el servicio entero — queda esto documentado por si se retoma.

## Configuración en Homepage (histórica)

```yaml
- DVR Dahua:
    href: http://192.168.0.156:1984
    description: Cámaras en vivo — las 4 en grilla, solo accesible en la LAN de casa
    icon: dahua.png
    siteMonitor: http://192.168.0.156:1984
    widget:
      type: iframe
      src: http://192.168.0.156:1984/?ch=1
      allowPolicy: autoplay
```

`href` y `siteMonitor` iban a la IP LAN directa (no había dominio público) — un click en la tarjeta abría la grilla completa. El widget `iframe` de la tarjeta —nativo de Homepage, no código propio— mostraba la cámara 1 sola. `allowPolicy: autoplay` era necesario porque, sin eso, el navegador puede bloquear el autoplay del video dentro del iframe.

**El video se veía estirado/deformado en la tarjeta.** `video-rtc.js` fuerza el `<video>` a `width:100%; height:100%` de su contenedor, sin `object-fit` propio — así que si el contenedor no respeta la proporción real del video, lo aplasta. No se usó `classes:` (el mecanismo normal de Homepage para el alto del iframe, vía clases de Tailwind) porque eso hubiera fijado una altura en píxeles sin relación con la proporción real del video — y además una clase de Tailwind "nueva", tipeada solo en `services.yaml` y nunca usada en ningún `.jsx` real de Homepage, no tiene garantizado tener CSS generado (Tailwind solo compila las clases que encuentra escaneando el código fuente en build time). Se resolvió con una regla en `custom.css` de Homepage con la proporción real de la cámara 1 (aspect-ratio explícito) en vez de una clase.

## Seguridad (histórica)

- las credenciales RTSP del DVR quedaban solo en `go2rtc.yaml`, en `core01` — nunca en `custom.js`, nunca en git;
- go2rtc **no tiene autenticación propia** (lo advierte su propia documentación: "passes requests from localhost... without HTTP authorization... it's your responsibility to set up secure external access") — cualquiera en la LAN que supiera la URL podía ver las cámaras sin login. Mismo modelo de riesgo que MySpeed/Glances y, antes, `dvr-proxy`;
- no había ninguna puerta desde internet — más estricto que el resto de los servicios de esta cuenta (que sí están detrás de Cloudflare Access), a propósito.

## Backup y restore

Nada que respaldar — sin estado propio.

## Observabilidad

Ya no aplica — el contenedor está parado.

## Troubleshooting (histórico)

- **Un canal no conecta (`producers: []` o vacío en `/api/streams`)** → revisar `docker logs go2rtc` por el error RTSP puntual; casi siempre es la contraseña mal urlencodeada (el `@` sin `%40`) o el DVR rechazando una quinta conexión simultánea al mismo canal (algunos firmwares Dahua limitan conexiones RTSP concurrentes por canal — si hay otra app/NVR también conectada al mismo canal, puede fallar).
- **Se ve sin audio** → el canal 4 sí trae audio (PCMA) en el stream principal, pero `<video>` arranca muteado a propósito (`this.video.muted = true` en `CamVideo`, necesario para que el autoplay funcione en cualquier navegador sin interacción) — no es que falte audio, está apagado por defecto. Otros canales pueden no tener audio configurado en el DVR directamente.
- **Las cámaras verticales se ven angostas, con franjas negras a los costados** → es a propósito, ver "Barras negras, no recortada" arriba (`object-fit: contain` — se prefirió ver la escena completa antes que perder los bordes superior/inferior) — no es un bug.
- **Las cámaras verticales se ven rotadas para el lado equivocado** → problema real, sin resolver — ver "El problema que no se llegó a resolver: la rotación" arriba.
- **Cambié `go2rtc.yaml` y no se aplicó** → hacía falta reiniciar el contenedor (`docker compose restart go2rtc`), no recargaba la config solo.
- **Cambié `www/index.html` y seguía viendo la versión vieja** → eso se servía en caliente, sin reiniciar nada — el problema casi siempre era **caché del navegador**, no del servidor. A diferencia de Homepage, esta página no pasaba por Cloudflare — no había nada que purgar del lado del servidor, hacía falta un hard refresh (`Cmd+Shift+R` / `Ctrl+Shift+R`) en el navegador.

## Documentación oficial

- [github.com/AlexxIT/go2rtc](https://github.com/AlexxIT/go2rtc) — repo y README completo
- [www/README.md](https://github.com/AlexxIT/go2rtc/blob/master/www/README.md) — `video-rtc.js`, la base de la página propia de este servicio
- [internal/api/README.md](https://github.com/AlexxIT/go2rtc/blob/master/internal/api/README.md) — `static_dir` y el resto de la config de la API HTTP
