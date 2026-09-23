---
title: MySpeed
sidebar_position: 25
---

# MySpeed

**Estado:** Actual · Observabilidad — corriendo en `core`
**Dónde corre:** Docker Core (`/srv/oscar/apps/myspeed/`)
**Sizing inicial:** liviano, sin requisitos especiales
**Red/puertos:** `5216` (API + UI web)
**Persistencia:** SQLite en `./data`, con volumen — los tests históricos sobreviven a un `docker compose down`

## Rol dentro de O.S.C.A.R.

Corre tests de velocidad de internet en un cron propio y guarda el historial (ping/descarga/subida) para poder ver tendencias — no reemplaza un test manual puntual, es para notar con el tiempo si el enlace se está degradando.

## Instalación

```bash
mkdir -p /srv/oscar/apps/myspeed/data
```

`compose.yaml`:

```yaml
services:
  myspeed:
    image: germannewsmaker/myspeed:${MYSPEED_VERSION}
    container_name: myspeed
    restart: unless-stopped
    ports:
      - "5216:5216"
    volumes:
      - ./data:/myspeed/data
    environment:
      TZ: America/Argentina/Buenos_Aires
```

`.env`: `MYSPEED_VERSION=1.0.9` (versión fijada — el tag `latest` en Docker Hub apunta al mismo build que `1.0.9`, no hay una versión más nueva numerada).

```bash
docker compose up -d
```

## Configuración en Homepage

```yaml
- MySpeed:
    href: http://192.168.0.156:5216
    description: Historial de velocidad de internet, tests automáticos cada tanto
    icon: myspeed.png
    siteMonitor: http://192.168.0.156:5216
    widget:
      type: myspeed
      url: http://192.168.0.156:5216
```

Sin `password:` en el widget — recién instalado, sin contraseña configurada todavía en MySpeed. Si más adelante se le pone una desde su propia UI, hay que sumarla acá también (`widget.password`), si no el widget deja de poder leer los datos.

## Seguridad

- sin autenticación propia por defecto — la UI web queda accesible en toda la LAN;
- no está publicado por el Tunnel — solo alcanzable dentro de la LAN, igual que Glances.

## Backup y restore

El volumen `./data` tiene el historial de tests en SQLite — sí vale la pena respaldarlo si el historial importa; si se pierde, MySpeed arranca de cero y sigue corriendo tests nuevos sin problema.

## Observabilidad

Uptime Kuma puede sumar un chequeo sobre el puerto 5216 — pendiente, no está cargado todavía.

## Troubleshooting

- **El widget no muestra datos** → esperar a que corra al menos un test (MySpeed corre los suyos por cron interno, no bajo demanda desde Homepage) — `/api/speedtests?limit=1` devuelve `[]` hasta el primer test real.
- **Homepage no puede conectarse** → confirmar que la URL usa la IP LAN de `core`, no `localhost` (Homepage no comparte la red del host).

## Documentación oficial

https://docs.myspeed.dev/
