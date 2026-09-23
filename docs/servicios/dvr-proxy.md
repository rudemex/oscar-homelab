---
title: DVR Proxy (cámaras)
sidebar_position: 27
---

# DVR Proxy

**Estado:** Retirado — reemplazado por [go2rtc](./go2rtc.md)
**Dónde corría:** Docker Core (`/srv/oscar/apps/dvr-proxy/`) — contenedor parado (`docker compose down`), archivos sin borrar en `core` por si hace falta volver atrás
**Sizing inicial:** liviano (imagen `python:3.12-slim`, un solo script, sin dependencias externas)
**Red/puertos:** `8099` (ya no en uso)
**Persistencia:** ninguna — no guardaba nada, solo reenviaba imágenes del DVR

:::note Por qué se retiró
Este proxy hablaba HTTP/Digest con el DVR — el mismo protocolo que usa su interfaz web, con todas sus rarezas (TLS viejo, snapshots o MJPEG). Después de tres vueltas completas (ver abajo) el techo real no estaba en el proxy sino en el protocolo: para tener video fluido de verdad, publicado por el dominio público, hacía falta hablarle al DVR por **RTSP** (su protocolo nativo de streaming) y reempaquetarlo en un formato que los navegadores entiendan — eso es exactamente lo que hace [go2rtc](./go2rtc.md), que lo reemplazó por completo. Se deja esta página como está — la saga completa (TLS viejo, framing HTTP, el límite real de Cloudflare con streams infinitos) tiene enseñanzas que valen la pena, aunque el código ya no corra.
:::

## Rol dentro de O.S.C.A.R. (histórico)

El [DVR Dahua](../hogar/cctv-dahua.md) tiene su propia app web, pero entrar ahí para ver las 4 cámaras es más fricción de la que vale la pena para un vistazo rápido — "para mí tiene más valor ver las cámaras" que un link a la aplicación. Este servicio era un proxy chiquito que armaba una página con las 4 cámaras en grilla.

Hubo tres vueltas completas antes de retirarlo, las tres documentadas abajo porque dejaron enseñanzas reales:

1. **v1, snapshots cada 3s**: la versión más simple, un `<img>` con el `src` reescrito por JS cada tanto.
2. **v2, MJPEG real**: el firmware Dahua expone un endpoint de **MJPEG** (`/cgi-bin/mjpg/video.cgi`), un stream HTTP `multipart/x-mixed-replace` que los navegadores reproducen nativo en un `<img>` sin ningún JS — video real a ~5-6 fps. Andaba perfecto **en la LAN**, pero se rompió al publicar el proxy por el Tunnel para que la tarjeta de Homepage cargara bien por HTTPS: Cloudflare no sostiene un stream de longitud indefinida (ver más abajo, "Cloudflare Tunnel no sostiene un stream infinito") — el pedido quedaba "pending" para siempre en el navegador, sin importar que el proxy funcionara perfecto.
3. **v3, snapshots cada 1s**: mismo mecanismo que v1, pero mucho más frecuente — a simple vista se veía casi en vivo, y como cada pedido es una respuesta HTTP normal y acotada (no un stream sin fin), Cloudflare la manejaba sin problema. Funcionó técnicamente, pero el usuario lo probó y no le convenció — "se ve muy trabado". Eso llevó a evaluar Frigate para tener video real; se revisaron los recursos de `core` (2 vCPUs, sin GPU, 45GB libres compartidos) y Frigate completo (detección + grabación continua) hubiera competido por esos recursos con el resto de los servicios — se optó por **go2rtc**, el mismo motor de re-streaming que usa Frigate por debajo pero sin detección ni grabación, que reemplazó a `dvr-proxy` del todo.

## Por qué un proxy y no apuntar directo al DVR

El endpoint de snapshot del DVR (`/cgi-bin/snapshot.cgi?channel=N`) necesita autenticación Digest con el usuario/contraseña reales del equipo. Esas credenciales **no pueden viajar en `custom.js`** — es un archivo que baja cualquiera en la LAN sin login, así que quedarían expuestas en texto plano a cualquiera con acceso a la red. El proxy las guarda del lado del servidor (variables de entorno del contenedor) y sirve las imágenes ya autenticadas, sin que el navegador necesite saber nada de la contraseña real.

## Instalación

```bash
mkdir -p /srv/oscar/apps/dvr-proxy
```

`compose.yaml`:

```yaml
services:
  dvr-proxy:
    image: python:3.12-slim
    container_name: dvr-proxy
    restart: unless-stopped
    working_dir: /app
    command: python server.py
    ports:
      - "8099:8099"
    volumes:
      - ./server.py:/app/server.py:ro
    environment:
      DVR_HOST: ${DVR_HOST}
      DVR_USER: ${DVR_USER}
      DVR_PASS: ${DVR_PASS}
```

`.env` (no versionado — vive solo en `core`):

```bash
DVR_HOST=192.168.0.224
DVR_USER=admin
DVR_PASS=<contraseña real del DVR>
```

`server.py` usa únicamente la librería estándar de Python (`http.server` + `urllib.request` con `HTTPDigestAuthHandler`) — sin `pip install`, arranca instantáneo y no depende de ningún paquete externo que pueda romperse con el tiempo. Expone:

- `GET /` — la página HTML con la grilla de 4 cámaras. Cada `<img>` arranca con `src="/snapshot?channel=N"` y un `<script>` la reescribe cada 1 segundo con un cache-buster (`&t=` + timestamp) — ver "Cloudflare Tunnel no sostiene un stream infinito" más abajo para el porqué de este mecanismo en vez de `/stream`.
- `GET /snapshot?channel=1..4` — el JPEG de un canal puntual (una sola foto, respuesta HTTP normal con `Content-Length`). Es lo que usan hoy tanto la página completa como la tarjeta de Homepage, refrescado por JS.
- `GET /stream?channel=1..4` — el video en vivo (MJPEG) de un canal, **sigue existiendo y andando por LAN**, ya no lo usa nada público. A diferencia de `/snapshot`, esto **nunca termina la respuesta** hasta que el cliente corta la conexión — el handler abre el stream del DVR y va reenviando cada chunk que llega, sin bufferear nada:
  ```python
  upstream = opener.open(DVR_BASE + "/cgi-bin/mjpg/video.cgi?channel=" + str(channel) + "&subtype=1")
  self.send_header("Content-Type", upstream.headers.get("Content-Type"))  # multipart/x-mixed-replace; boundary=...
  while True:
      chunk = upstream.read(4096)
      if not chunk:
          break
      self.wfile.write(chunk)
  ```
  `ThreadingHTTPServer` (no el `HTTPServer` simple) es necesario acá — con varias cámaras abiertas a la vez, cada una es una conexión que se queda abierta indefinidamente; sin threads, la segunda cámara nunca podría empezar a servirse mientras la primera sigue transmitiendo.

### El detalle no obvio: TLS viejo

El firmware del DVR solo negocia protocolos/cifrados TLS que el contexto SSL **por defecto** de Python rechaza de entrada (`SSLV3_ALERT_HANDSHAKE_FAILURE`) — mismo servidor al que `curl` sí se conectaba sin problema, porque el OpenSSL del sistema tiene un nivel de seguridad más permisivo por defecto. Hubo que bajarlo a mano en el contexto SSL:

```python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.minimum_version = ssl.TLSVersion.TLSv1
ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
```

Sin esto, cualquier intento de conexión HTTPS al DVR desde Python falla en el handshake, aunque el mismo request funcione perfecto desde la terminal con `curl`.

### El otro detalle no obvio: framing sin `chunked`, video que nunca pinta

Primera versión de `/stream` respondía sin `Content-Length` (imposible, es un stream sin fin) **ni** `Transfer-Encoding: chunked` — solo escribía bytes crudos y confiaba en que el cierre de la conexión marcara el final. `curl` no tiene problema con eso (lee hasta que el socket se cierra, y lo mostró bien en todas las pruebas por terminal) — pero un navegador real, recibiendo una respuesta sin ninguna forma declarada de delimitar el cuerpo, se quedaba esperando indefinidamente sin pintar un solo frame: la página cargaba (el `200 OK` llegaba), los 4 recuadros de cámara se veían negros, y en las herramientas de desarrollador la petición quedaba en estado "cargando" para siempre. Costó varias rondas de diagnóstico remoto (probar la URL sola vs. la página completa, confirmar que otro puerto LAN sí cargaba, comparar reglas de NAT/firewall entre puertos) llegar al dato real: no era de red, era el *framing* HTTP de la respuesta.

La solución es `Transfer-Encoding: chunked` — el mecanismo estándar de HTTP para streams de longitud indefinida — junto con `protocol_version = "HTTP/1.1"` en el `Handler` (el default de `BaseHTTPRequestHandler` es HTTP/1.0, que no sabe de `chunked`):

```python
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    ...
    self.send_header("Transfer-Encoding", "chunked")
    self.end_headers()
    while True:
        chunk = upstream.read(4096)
        if not chunk:
            break
        self.wfile.write(("%x\r\n" % len(chunk)).encode() + chunk + b"\r\n")
    self.wfile.write(b"0\r\n\r\n")
```

Cada trozo de datos se envuelve con su tamaño en hexadecimal + `\r\n` antes, y `\r\n` después — el formato exacto que espera un cliente HTTP/1.1 para poder ir procesando el cuerpo a medida que llega, en vez de esperar a que la conexión se cierre.

```bash
docker compose up -d
```

## Configuración en Homepage (histórica)

La tarjeta del DVR en `services.yaml` llegó a tener varias formas mientras este proxy y después go2rtc estuvieron activos (widget `mjpeg` apuntando a la IP LAN → el mismo widget por el Tunnel → una `<img>` propia armada en `custom.js` con `/snapshot` refrescado cada 1s → un `iframe` con video real vía go2rtc). Ninguna sigue en pie — hoy es un link simple con chequeo de estado, documentado en [Homepage](./homepage.md#dvr-dahua-de-video-en-vivo-a-solo-estado).

## Cloudflare Tunnel no sostiene un stream infinito

Publicar `cam.oscarlab.com.ar` por el Tunnel (ver más abajo) resolvía el problema original — mixed content al cargar por HTTPS un recurso `http://` — pero destapó uno nuevo: el widget `mjpeg` apuntando a `/stream?channel=1` a través del dominio público se quedaba **"pending" para siempre** en el navegador, sin cargar nunca ni tirar un error visible.

Los logs de `cloudflared` (`docker logs cloudflared`) mostraron el porqué:

```
ERR error="stream 76773 canceled by remote with error code 0" ingressRule=7 originService=http://192.168.0.156:8099
ERR Request failed error="stream 76773 canceled by remote with error code 0" dest=https://cam.oscarlab.com.ar/stream?channel=2
```

El pedido sí llegaba hasta el proxy (`docker logs dvr-proxy` no mostraba ningún error, ni 502, ni traceback — la conexión al DVR y el reenvío andaban perfecto) pero el Tunnel cortaba el lado que mira hacia el navegador, una y otra vez. La causa es una limitación real de Cloudflare (sin ningún switch de "no bufferear" disponible en un plan gratuito): su proxy no está pensado para relayar una respuesta HTTP de longitud indefinida como esta — la bufferea esperando un final que nunca llega, y en algún momento la corta.

Por eso el video en vivo real (`/stream`, MJPEG) quedó limitado a acceso directo por LAN, y tanto la página completa como la tarjeta de Homepage pasaron a usar `/snapshot` refrescado cada 1 segundo por JS — una respuesta HTTP acotada normal, que el Tunnel relaya sin ningún problema.

## Publicado por el Tunnel, atrás de Access (histórico)

Mientras este proxy estuvo activo, `cam.oscarlab.com.ar` lo publicaba por el Cloudflare Tunnel con una app de Cloudflare Access adelante — mismo patrón que Beszel, Uptime Kuma, n8n, etc. Ese hostname **ya no existe**: cuando se retiró este proxy a favor de [go2rtc](./go2rtc.md), la decisión fue no volver a publicar las cámaras en ningún dominio público — ni siquiera protegido por Access. Se dieron de baja el DNS, la app de Access y la regla del Tunnel enteros; las cámaras hoy solo se ven estando en la LAN de casa (ver [go2rtc](./go2rtc.md#por-qué-solo-lan)).

## Seguridad (histórica)

- las credenciales del DVR quedaban solo en el `.env` de este contenedor — nunca en `custom.js`, nunca en git;
- el proxy en sí **no tenía autenticación propia** — toda persona que llegara directo a `http://192.168.0.156:8099` desde la LAN podía ver las cámaras sin login. Mismo modelo de riesgo que sigue vigente hoy con go2rtc.

## Backup y restore

Nada que respaldar — el contenedor no persistía estado.

## Observabilidad

Ya no aplica — el contenedor está parado.

## Troubleshooting (histórico — el servicio está retirado)

Se deja como referencia, por si algún día se vuelve a necesitar hablarle HTTP directo al DVR (por ejemplo, para un endpoint puntual que go2rtc no cubra):

- **`502` al pedir un snapshot** → revisar `docker logs dvr-proxy`. Si dice `SSLV3_ALERT_HANDSHAKE_FAILURE`, el `ctx.set_ciphers(...)`/`minimum_version` no está aplicado — confirmar que el `server.py` en el contenedor tiene esas líneas.
- **La grilla carga pero las imágenes no aparecen** → confirmar `DVR_USER`/`DVR_PASS` en el `.env` — con credenciales incorrectas el DVR devuelve 401 y el proxy lo traduce a 502.
- **Varias cámaras a la vez y una no carga** → confirmar que el compose sigue usando `ThreadingHTTPServer`, no `HTTPServer` — con el servidor simple (no threaded), una sola conexión activa bloquea a las demás.
- **La página carga (título visible) pero los 4 recuadros quedan negros, "cargando" para siempre en las devtools, accediendo por LAN a `/stream`** → falta `Transfer-Encoding: chunked` en la respuesta de `/stream` (ver arriba). Síntoma clave para reconocer este caso: `curl` sí muestra el video bien (no distingue si el framing HTTP es correcto, solo lee hasta que el socket se cierra), pero un navegador real no pinta nada — si algo "funciona por curl pero no en el navegador" para un endpoint que hace streaming, sospechar del framing HTTP antes que de la red.
- **Un `<img>` apuntando a un stream MJPEG se queda "pending" para siempre viendo por un dominio detrás de Cloudflare Tunnel** → no es un bug de esta app puntual, es una limitación real de Cloudflare con respuestas HTTP de longitud indefinida — ver "Cloudflare Tunnel no sostiene un stream infinito" arriba. Aplica a cualquier cosa que intente lo mismo, no solo a este proxy.

## Documentación oficial

No hay una — es un script propio, sin proyecto upstream que seguir.
