---
title: Glances
sidebar_position: 24
---

# Glances

**Estado:** Actual · Observabilidad — corriendo en `core01`
**Dónde corre:** Docker Core (`/srv/oscar/apps/glances/`), `network_mode: host` + `pid: host`
**Sizing inicial:** ~60 MB RAM
**Red/puertos:** `61208` (API + UI web, modo `-w`)
**Persistencia:** ninguna — es un monitor en vivo, sin base de datos

## Rol dentro de O.S.C.A.R.

Fuente de datos real de CPU/RAM/disco del **host `core01`**, para el widget de recursos de [Homepage](./homepage.md). No es un reemplazo de Beszel (que también mide el host y además guarda historial) — es específicamente lo que necesita el widget nativo `glances` de Homepage, que solo sabe hablar con esta API puntual.

## Por qué existe

Antes de esto, la fila de CPU/RAM/disco del dashboard mostraba el uso del **contenedor de Homepage**, no el de `core01` — casi siempre ~0% de CPU/RAM, porque Homepage es una app liviana, y eso es justamente lo que hacía que "no se entendiera": los números no reflejaban nada real. Homepage no tiene forma de medir el host completo por sí solo; necesita un agente aparte que sí lo mida — Glances es el que documentación oficial de Homepage recomienda para esto.

## Instalación

```bash
mkdir -p /srv/oscar/apps/glances
```

`compose.yaml`:

```yaml
services:
  glances:
    image: nicolargo/glances:${GLANCES_VERSION}
    container_name: glances
    restart: unless-stopped
    network_mode: host
    pid: host
    privileged: true
    environment:
      GLANCES_OPT: "-w"
      TZ: America/Argentina/Buenos_Aires
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /:/hostroot:ro
```

`network_mode: host` + `pid: host` son necesarios para que Glances vea el CPU/RAM reales del host en vez de los del propio contenedor — mismo criterio que ya se usa en [Beszel](./beszel.md#instalaci%C3%B3n) para el agente. `privileged: true` es requisito de Glances para leer algunos sensores/estadísticas del sistema.

`/:/hostroot:ro` es el mismo truco que se usó primero directo en Homepage (antes de existir Glances acá): sin este mount, el disco reportado es el filesystem interno del contenedor, no el disco real de `core01` — con el mount, Glances expone `/hostroot` como punto de montaje real y ahí sí coincide con `df -h /` del host.

`.env`: `GLANCES_VERSION=4.5.6-full` — el tag `-full` no es opcional acá, es la variante de imagen que trae los plugins extra (sensores, Docker) que el resto de este setup necesita; el tag corto `4.5.6` sin sufijo es una imagen más chica sin esos plugins.

```bash
docker compose up -d
```

## Configuración en Homepage

`widgets.yaml`:

```yaml
- glances:
    url: http://192.168.0.156:61208
    version: 4
    cpu: true
    mem: true
    disk: /hostroot
    expanded: true
```

La URL usa la IP LAN de `core01`, no `localhost` — Homepage no corre en `network_mode: host` (usa bridge con `3005:3000`), así que necesita la IP real para llegar a Glances, que sí está en la red del host.

## Seguridad

- `privileged: true` + `pid: host` le dan al contenedor visibilidad total del host — es una excepción deliberada, igual que el `network_mode: host` de Beszel/Cloudflare Tunnel, justificada por lo que necesita medir; no se lo expone directo a Internet (no está en el túnel, solo lo consume Homepage internamente vía LAN);
- la UI web de Glances (puerto 61208) queda accesible en toda la LAN sin autenticación propia — aceptable hoy (red plana, sin exposición externa), revisar si alguna vez se expone vía Tunnel (necesitaría Access delante, como todo lo demás).

## Backup y restore

No hay estado que respaldar — si se pierde el contenedor, `docker compose up -d` lo reconstruye igual.

## Observabilidad

Es la propia herramienta de observabilidad — el círculo de "quién vigila al vigilante" lo cierra el monitor de Uptime Kuma sobre el puerto 61208.

## Troubleshooting

- **El disco muestra el filesystem del contenedor, no el real** → falta el mount `/:/hostroot:ro`, o `widgets.yaml` sigue apuntando a `/` en vez de `/hostroot` — ver "Configuración en Homepage" arriba.
- **CPU/RAM en 0% o sin datos** → confirmar que el contenedor tiene `network_mode: host` y `pid: host` — sin esos dos, Glances mide su propio contenedor, mismo problema que tenía el widget nativo de Homepage antes de esto.
- **Homepage no puede conectarse** → confirmar que la URL en `widgets.yaml` usa la IP LAN de `core01`, no `localhost` (Homepage no comparte la red del host).

## Documentación oficial

https://github.com/nicolargo/glances
