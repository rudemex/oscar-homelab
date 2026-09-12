---
title: DVR Proxy (cámaras)
sidebar_position: 27
---

# DVR Proxy

**Estado:** Actual · Hogar — corriendo en `core01`
**Dónde corre:** Docker Core (`/srv/oscar/apps/dvr-proxy/`)
**Sizing inicial:** liviano (imagen `python:3.12-slim`, un solo script, sin dependencias externas)
**Red/puertos:** `8099` (grilla HTML + video en vivo)
**Persistencia:** ninguna — no guarda nada, solo reenvía video en vivo

## Rol dentro de O.S.C.A.R.

El [DVR Dahua](../hogar/cctv-dahua.md) tiene su propia app web, pero entrar ahí para ver las 4 cámaras es más fricción de la que vale la pena para un vistazo rápido — "para mí tiene más valor ver las cámaras" que un link a la aplicación. Este servicio es un proxy chiquito que arma una página con las 4 cámaras en grilla, **en vivo de verdad** — no fotos que se repiten cada tanto.

La primera versión sí era eso: un snapshot JPEG re-pedido cada 3 segundos por JS. Se corrigió después de probar si el DVR exponía algo mejor — y sí: además del snapshot puntual, el firmware Dahua expone un endpoint de **MJPEG** (`/cgi-bin/mjpg/video.cgi`), un stream HTTP de tipo `multipart/x-mixed-replace` que los navegadores reproducen nativo en un `<img>` — sin ningún JS de por medio, sin refrescos, video real a ~5-6 fps en la subresolución (`subtype=1`, la pensada para vigilancia en grilla, no para ver un canal solo en pantalla completa).

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

`.env` (no versionado — vive solo en `core01`):

```bash
DVR_HOST=192.168.0.224
DVR_USER=admin
DVR_PASS=<contraseña real del DVR>
```

`server.py` usa únicamente la librería estándar de Python (`http.server` + `urllib.request` con `HTTPDigestAuthHandler`) — sin `pip install`, arranca instantáneo y no depende de ningún paquete externo que pueda romperse con el tiempo. Expone:

- `GET /` — la página HTML con la grilla de 4 cámaras, cada `<img>` apuntando a su `/stream`.
- `GET /stream?channel=1..4` — el video en vivo (MJPEG) de un canal. A diferencia de `/snapshot`, esto **nunca termina la respuesta** hasta que el cliente corta la conexión — el handler abre el stream del DVR y va reenviando cada chunk que llega, sin bufferear nada:
  ```python
  upstream = opener.open(DVR_BASE + "/cgi-bin/mjpg/video.cgi?channel=" + str(channel) + "&subtype=1")
  self.send_header("Content-Type", upstream.headers.get("Content-Type"))  # multipart/x-mixed-replace; boundary=...
  while True:
      chunk = upstream.read(4096)
      if not chunk:
          break
      self.wfile.write(chunk)
  ```
  `ThreadingHTTPServer` (no el `HTTPServer` simple) es necesario acá — con 4 cámaras abiertas a la vez, cada una es una conexión que se queda abierta indefinidamente; sin threads, la segunda cámara nunca podría empezar a servirse mientras la primera sigue transmitiendo.
- `GET /snapshot?channel=1..4` — el JPEG de un canal puntual (una sola foto, no streaming) — se mantiene por si hace falta una miniatura o una verificación puntual en algún otro lado.

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

## Configuración en Homepage

La tarjeta del DVR en `services.yaml` apunta acá, no a la IP del DVR:

```yaml
- DVR Dahua:
    href: http://192.168.0.156:8099
    description: Cámaras — grilla de las 4, sin abrir la app del DVR
    icon: dahua.png
    siteMonitor: http://192.168.0.156:8099
```

`siteMonitor` sí puede apuntar acá (a diferencia de la IP directa del DVR — ver troubleshooting de [Homepage](./homepage.md)) porque este proxy responde HTTP normal y bien formado, sin las rarezas del firmware del DVR.

## Seguridad

- las credenciales del DVR quedan solo en el `.env` de este contenedor — nunca en `custom.js`, nunca en git;
- el proxy en sí **no tiene autenticación propia** — cualquiera en la LAN que sepa la URL puede ver las cámaras. Es el mismo nivel de exposición que ya aceptan Glances/MySpeed (herramientas internas sin login, solo LAN, sin Tunnel) — aceptable para una red doméstica plana, a revisar si alguna vez hay visitas frecuentes con acceso a la LAN o se arma una VLAN de invitados;
- no está publicado por el Tunnel — solo alcanzable dentro de la LAN.

## Backup y restore

Nada que respaldar — el contenedor no persiste estado, `docker compose up -d` lo reconstruye idéntico.

## Observabilidad

El `siteMonitor` de su propia tarjeta en Homepage ya cubre "¿está vivo?".

## Troubleshooting

- **`502` al pedir un snapshot** → revisar `docker logs dvr-proxy`. Si dice `SSLV3_ALERT_HANDSHAKE_FAILURE`, el `ctx.set_ciphers(...)`/`minimum_version` no está aplicado — confirmar que el `server.py` en el contenedor tiene esas líneas.
- **La grilla carga pero las imágenes no aparecen** → confirmar `DVR_USER`/`DVR_PASS` en el `.env` — con credenciales incorrectas el DVR devuelve 401 y el proxy lo traduce a 502.
- **El video se ve pero se congela después de un rato** → revisar que el contenedor siga `Up` (`docker ps`) y no se haya reiniciado; una conexión de stream cortada (por ejemplo al reiniciar el contenedor) no se reconecta sola del lado del `<img>` — hay que recargar la página.
- **Varias cámaras a la vez y una no carga** → confirmar que el compose sigue usando `ThreadingHTTPServer`, no `HTTPServer` — con el servidor simple (no threaded), una sola conexión activa bloquea a las demás.
- **La página carga (título visible) pero los 4 recuadros quedan negros, "cargando" para siempre en las devtools** → falta `Transfer-Encoding: chunked` en la respuesta de `/stream` (ver arriba). Síntoma clave para reconocer este caso: `curl` sí muestra el video bien (no distingue si el framing HTTP es correcto, solo lee hasta que el socket se cierra), pero un navegador real no pinta nada — si algo "funciona por curl pero no en el navegador" para un endpoint que hace streaming, sospechar del framing HTTP antes que de la red.

## Documentación oficial

No hay una — es un script propio, sin proyecto upstream que seguir.
