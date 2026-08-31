---
title: Counter-Strike 2
sidebar_position: 3
---

# Servidor de Counter-Strike 2

**Estado:** Laboratorio · Juegos
**Dónde corre:** VM de laboratorio dedicada (más pesado que Minecraft, mejor no compartir VM con otros servicios)
**Sizing inicial:** 4 vCPU, 6 GB RAM — sensible a CPU/tickrate, no solo a RAM
**Red/puertos:** `27015/udp+tcp` (juego), `27020/udp` (voz, si aplica)
**Persistencia:** prácticamente ninguna — el juego se re-descarga solo; lo único a versionar son configs/mapas custom

## Rol dentro de O.S.C.A.R.

- servidor dedicado de CS2 para jugar partidas privadas con amigos, con tickrate y reglas propias;
- ejemplo de servicio que **no necesita backup** — la respuesta correcta a "¿cómo lo respaldo?" es "no hace falta", y vale la pena tener ese ejemplo documentado en vez de inventar un procedimiento que no aporta nada.

## Requisito previo: Game Server Login Token (GSLT)

Valve requiere un token gratuito para identificar servidores dedicados públicos — sin él, el server arranca pero Steam no lo lista y puede tener restricciones. Conseguirlo (gratis, con una cuenta Steam):

1. entrar a [steamcommunity.com/dev/managegameservers](https://steamcommunity.com/dev/managegameservers);
2. generar un token para el App ID `730` (Counter-Strike 2);
3. guardar el token — es un secreto, tratarlo como una contraseña (nunca en Git).

## Instalación

Usamos [`joedwards32/cs2`](https://github.com/joedwards32/CS2), imagen Docker mantenida por la comunidad que envuelve SteamCMD para descargar e iniciar el dedicated server.

```bash
mkdir -p /srv/oscar/apps/cs2
cd /srv/oscar/apps/cs2
```

`.env` (el token y las contraseñas son secretos — este archivo **no va a Git**, ver [gestión de secretos](../seguridad/secretos.md)):

```dotenv
CS2_TOKEN=CHANGE_ME_GSLT_TOKEN
SERVER_PASSWORD=
RCON_PASSWORD=CHANGE_ME
```

`compose.yaml`:

```yaml
services:
  cs2:
    image: joedwards32/cs2:latest
    restart: unless-stopped
    stdin_open: true
    tty: true
    ports:
      - "27015:27015/tcp"
      - "27015:27015/udp"
    volumes:
      - cs2-data:/home/steam/cs2-dedicated
    environment:
      CS2_SERVERNAME: "O.S.C.A.R. CS2"
      CS2_PASSWORD: ${SERVER_PASSWORD}
      CS2_RCONPW: ${RCON_PASSWORD}
      CS2_GSLT: ${CS2_TOKEN}
      CS2_MAXPLAYERS: 10
      CS2_GAMEALIAS: competitive
      TZ: America/Argentina/Buenos_Aires

volumes:
  cs2-data:
```

:::note Sobre `:latest` en esta imagen puntual
El resto de este repo evita `:latest` — acá es una excepción deliberada: `joedwards32/cs2` no publica tags por versión de CS2 (el juego se actualiza vía SteamCMD dentro del propio contenedor en cada arranque, no reconstruyendo la imagen), así que fijar un tag de imagen no fija la versión del juego de todas formas. Si te preocupa reproducibilidad exacta, fijá el **digest** de la imagen (`docker inspect --format='{{.RepoDigests}}'`) en vez del tag.
:::

```bash
docker compose up -d
docker compose logs -f cs2
```

La primera descarga del juego vía SteamCMD pesa varios GB y puede tardar bastante según tu conexión — es esperable, no un error.

## Seguridad

- **el GSLT es equivalente a una contraseña de servicio** — si se filtra, alguien puede hacer que Steam asocie tráfico ajeno a tu servidor; regenerarlo desde el mismo panel de Steam si sospechás que se filtró;
- `CS2_RCONPW` protege la consola remota de administración (kick, ban, cambio de mapa) — no dejarla vacía ni reutilizar otra contraseña del homelab;
- `CS2_PASSWORD` (contraseña de sala) es opcional pero recomendable si el server queda expuesto más allá de la LAN — sin ella, cualquiera que encuentre la IP:puerto puede entrar a jugar.

## Backup y restore

No hay nada que respaldar en el sentido habitual: los archivos del juego se re-descargan solos desde Steam en cada `docker compose up` si el volumen se pierde. Lo único que vale la pena versionar en Git (no en un backup, directamente en el repo del homelab) son configs custom si se personalizan (`server.cfg`, listas de mapas rotación, `.vpk` de mapas propios) — todo lo demás es descartable.

## Observabilidad

Mínimo razonable para un servidor de juego, sin sobre-invertir: `docker compose ps` mostrando el contenedor healthy, y un chequeo de disponibilidad del puerto UDP `27015` desde [Uptime Kuma](../servicios/uptime-kuma.md) (chequeo tipo puerto TCP/UDP, no HTTP) si se le quiere dar seguimiento igual que al resto de servicios.

## Troubleshooting

- **El contenedor arranca pero el server no aparece en el navegador de servidores de Steam** → GSLT inválido/vacío, o puerto UDP `27015` no llega desde afuera → revisar `CS2_GSLT` en `.env`, confirmar el port-forward/regla de firewall.
- **La descarga de SteamCMD falla o se queda colgada** → problema de red saliente del host, o Steam caído momentáneamente → revisar conectividad saliente desde la VM (`curl -I https://steamcdn-a.akamaihd.net`), reintentar más tarde.
- **Consumo de CPU muy alto con pocos jugadores** → tickrate configurado más alto de lo que el hardware disponible sostiene → bajar tickrate o revisar cuántos vCPU tiene realmente asignados la VM.
