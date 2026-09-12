---
title: DVR Proxy (cámaras)
sidebar_position: 27
---

# DVR Proxy

**Estado:** Actual · Hogar — corriendo en `core01`
**Dónde corre:** Docker Core (`/srv/oscar/apps/dvr-proxy/`)
**Sizing inicial:** liviano (imagen `python:3.12-slim`, un solo script, sin dependencias externas)
**Red/puertos:** `8099` (grilla HTML + snapshots)
**Persistencia:** ninguna — no guarda nada, solo reenvía imágenes en vivo

## Rol dentro de O.S.C.A.R.

El [DVR Dahua](../hogar/cctv-dahua.md) tiene su propia app web, pero entrar ahí para ver las 4 cámaras es más fricción de la que vale la pena para un vistazo rápido — "para mí tiene más valor ver las cámaras" que un link a la aplicación. Este servicio es un proxy chiquito que arma una página con las 4 cámaras en grilla, cada una refrescándose sola cada 3 segundos (snapshot JPEG, no video real — el DVR no expone video vía HTTP, solo RTSP, que un navegador no reproduce sin un servidor de transcodeo aparte).

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

- `GET /` — la página HTML con la grilla de 4 cámaras (se autorefresca sola con JS, cada 3s).
- `GET /snapshot?channel=1..4` — el JPEG de un canal puntual, re-servido desde el DVR.

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
- **Imágenes se ven pero nunca cambian** → el snapshot es una foto, no video; si la escena real no cambia entre refrescos de 3s, es esperable que se vea igual.

## Documentación oficial

No hay una — es un script propio, sin proyecto upstream que seguir.
