---
title: Visión general
sidebar_position: 1
---

# Servidores de juegos

**Estado:** Laboratorio. Ninguno de los dos servidores de esta sección es parte de la arquitectura core de O.S.C.A.R. — son un uso divertido y legítimo del homelab, pero no deben competir por recursos con `core01`, `devops01` o `k3s01` cuando importa que esos anden bien.

## Por qué son distintos al resto de "servicios"

Todo lo demás en [servicios](../servicios/catalogo.md) existe para operar o aprender infraestructura. Un servidor de Minecraft o de Counter-Strike existe para jugar con amigos — eso cambia las prioridades:

- **no necesitan alta disponibilidad**: si se caen un sábado a la noche, se reinician y listo, no hace falta un runbook de incident response;
- **su "backup" es mucho más simple**: en Minecraft importa el mundo (irreemplazable si hay horas de construcción); en CS2 no hay casi nada que respaldar, el juego se re-descarga solo;
- **compiten por RAM/CPU con todo lo demás** — ver la nota de sizing en cada página antes de prenderlos junto con el resto del stack, sobre todo si vas a jugar mientras el resto de O.S.C.A.R. sigue corriendo.

## Requisitos de RAM por servidor

| Servidor | RAM mínima jugable | RAM cómoda | Notas |
|---|---:|---:|---|
| [Minecraft Java](./minecraft.md) | 2 GB | 4 GB+ | crece con mods/plugins y con la distancia de renderizado |
| [Counter-Strike 2](./counter-strike.md) | 4 GB | 6 GB+ | sensible a CPU además de RAM; tickrate alto pide más núcleo dedicado |

Con los 32 GB actuales del Dell (ver [distribución con 32 GB](../hardware/dell-7060.md#distribución-con-32-gb)) ya repartidos entre Proxmox + `core01` + `devops01` + `k3s01` + observabilidad, queda margen para uno de los dos corriendo de forma más permanente sin apretar — pero **no ambos a la vez, todo el tiempo, además del resto del stack**. La forma más segura de usarlos sigue siendo on-demand (`qm start`/`docker compose up -d` cuando se va a jugar, `down`/`stop` después), reservando "dejarlo prendido siempre" para uno solo de los dos y solo si se valida que no genera presión sobre el resto de servicios.

## Dónde corren

Ambos se documentan como contenedores Docker en una VM — no ameritan una VM dedicada por sí solos. Puede ser `core01` si se van a usar ocasionalmente y coordinar con el resto, o una VM de laboratorio separada y apagada la mayor parte del tiempo si el uso es más frecuente y no se quiere arriesgar a saturar `core01` justo cuando otro servicio lo necesita.

## Exposición a Internet

Para jugar con amigos que no están en tu red, hay tres opciones razonables, de más a menos simple:

1. **VPN a la LAN** (WireGuard/Tailscale): cada amigo se conecta como si estuviera en tu red local. Más simple de asegurar, requiere que instalen un cliente VPN.
2. **Port-forward directo** en el router, solo al puerto del juego (no HTTP, así que Cloudflare Tunnel clásico no aplica igual que a Grafana/n8n). Más simple para los amigos, expone directamente tu IP pública al puerto del juego — aceptable para un servidor de juego (no es un panel administrativo), pero mantené el juego actualizado.
3. **Cloudflare Tunnel con soporte TCP genérico** (`cloudflared access tcp`): más elaborado de configurar, evita abrir puertos, tiene sentido si ya tenés Cloudflare Tunnel andando para otra cosa.

Ninguna de las tres es "la correcta" — depende de cuántos amigos, qué tan seguido, y si ya tenés VPN configurada por otro motivo.
