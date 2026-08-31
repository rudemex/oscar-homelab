---
title: Minecraft
sidebar_position: 2
---

# Servidor de Minecraft

**Estado:** Laboratorio · Juegos
**Dónde corre:** Docker Core (`core01`) o VM de laboratorio dedicada
**Sizing inicial:** 2 vCPU, 4 GB RAM (subir si hay mods/muchos jugadores)
**Red/puertos:** `25565/tcp` (juego), `25575/tcp` (RCON, solo interno)
**Persistencia:** el mundo completo — es el único dato de esta sección que realmente importa respaldar

## Rol dentro de O.S.C.A.R.

- servidor Java Edition para jugar con familia/amigos;
- laboratorio de Docker con estado real y backup con consecuencias reales (perder un mundo de meses de construcción sí duele, a diferencia de la mayoría de los labs de este repo).

## Instalación

Usamos [`itzg/minecraft-server`](https://github.com/itzg/docker-minecraft-server), la imagen Docker de referencia de la comunidad (miles de commits, mantenida activamente, soporta Vanilla/Paper/Forge/Fabric).

```bash
mkdir -p /srv/oscar/apps/minecraft
cd /srv/oscar/apps/minecraft
```

`.env`:

```dotenv
MC_VERSION=1.21.4
MEMORY=4G
RCON_PASSWORD=CHANGE_ME
```

`compose.yaml`:

```yaml
services:
  minecraft:
    image: itzg/minecraft-server:java21
    restart: unless-stopped
    environment:
      EULA: "TRUE"
      TYPE: VANILLA
      VERSION: ${MC_VERSION}
      MEMORY: ${MEMORY}
      DIFFICULTY: normal
      MODE: survival
      ENABLE_RCON: "true"
      RCON_PASSWORD: ${RCON_PASSWORD}
      # whitelist recomendada si el server se expone más allá de la LAN:
      # WHITELIST: "usuario1,usuario2"
      # ENFORCE_WHITELIST: "true"
    ports:
      - "25565:25565"
      - "127.0.0.1:25575:25575"   # RCON solo accesible desde el propio host, nunca publicado
    volumes:
      - mc-data:/data
    stdin_open: true
    tty: true

volumes:
  mc-data:
```

`EULA: "TRUE"` es obligatorio — Mojang requiere aceptar explícitamente el [EULA](https://www.minecraft.net/eula) para correr un server; sin esa variable el contenedor se niega a arrancar (a propósito, no es un bug).

```bash
docker compose up -d
docker compose logs -f minecraft
```

El primer arranque genera el mundo y tarda más que los siguientes — esperar a ver `Done` en los logs antes de conectarse.

### Cambiar de Vanilla a Paper/Fabric

Cambiar `TYPE` a `PAPER` o `FABRIC` (y agregar `MODS`/`PLUGINS` según corresponda) — la imagen soporta ambos sin cambiar de compose. No mezclar mods incompatibles con la versión fijada en `MC_VERSION`.

## Seguridad

- **RCON nunca publicado a `0.0.0.0`** — el compose de arriba ya lo ata a `127.0.0.1`; es la consola de administración remota del server, equivalente a una shell con privilegios sobre el mundo.
- si el server se expone más allá de la LAN (ver [exposición a Internet](./vision-general.md#exposición-a-internet)), activar `WHITELIST`/`ENFORCE_WHITELIST` — sin whitelist, cualquiera que encuentre la IP:puerto puede entrar y romper el mundo;
- mantener `MC_VERSION` fijo y actualizado deliberadamente, no en automático — un mod/plugin puede dejar de funcionar con una versión nueva sin aviso.

## Backup y restore

El mundo vive completo en el volumen `mc-data` (`/data` dentro del contenedor) — es el dato más "irreemplazable" de todo este repo, en el sentido literal de horas humanas invertidas que no se recrean solas.

Backup en caliente (Minecraft tolera copiar el mundo mientras corre, pero hay una ventana de inconsistencia si copiás justo en medio de un autosave; más seguro forzar un `save-all` antes):

```bash
# forzar guardado y pausar autosave brevemente vía RCON
docker compose exec minecraft rcon-cli save-all
docker compose exec minecraft rcon-cli save-off

tar -czf mc-backup-$(date +%F).tar.gz -C /var/lib/docker/volumes/minecraft_mc-data/_data .

docker compose exec minecraft rcon-cli save-on
```

(la ruta exacta del volumen puede variar; confirmarla con `docker volume inspect minecraft_mc-data`). Mover el `.tar.gz` fuera del host, igual que cualquier otro backup — ver [estrategia 3-2-1](../backup-dr/estrategia-321.md).

Restore: detener el contenedor, reemplazar el contenido de `mc-data` por el del backup, iniciar.

## Troubleshooting

- **El contenedor arranca y se cierra solo, log dice "You need to agree to the EULA"** → falta `EULA: "TRUE"` en el compose → agregarla, no hay forma de saltear este paso.
- **`OutOfMemoryError` en los logs bajo carga** → `MEMORY` insuficiente para la cantidad de jugadores/distancia de renderizado configurada → subir `MEMORY` (y confirmar que la VM/host tiene esa RAM libre de verdad, no solo asignada).
- **Los amigos no pueden conectarse pero el server corre bien en LAN** → falta el port-forward/VPN, o el firewall del router bloquea `25565/tcp` → revisar la opción de exposición elegida en [visión general](./vision-general.md#exposición-a-internet).
