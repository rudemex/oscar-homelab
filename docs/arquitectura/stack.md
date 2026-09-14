---
title: Stack elegido
sidebar_position: 3
---

# Qué vamos a usar

Una cosa es el mínimo técnico para correr algo (ver [requisitos mínimos](../referencia/requisitos-minimos.md)) y otra distinta es qué elegimos nosotros específicamente, y por qué. Esta tabla es esa segunda cosa: una decisión concreta por capa, no todas las opciones posibles.

| Capa | Elegimos | Estado | Por qué (resumen) |
|---|---|---|---|
| Virtualización | [Proxmox VE](../proxmox/instalacion.md) | **Actual** — `oscar-core`, VE 9.2 | snapshots/backups por VM, aislamiento entre plataformas |
| Contenedores | [Docker + Compose](../servicios/docker-compose.md) | **Actual** — `core01`, Docker 29 | estándar de facto, curva de entrada baja |
| Orquestación | [k3s](../kubernetes/instalacion-k3s.md) | Objetivo | Kubernetes real con bajo overhead en un nodo chico |
| GitOps | [Argo CD](../kubernetes/instalacion-argocd.md) | Objetivo | reconciliación declarativa, UI para aprender el modelo |
| Registry/artefactos | [Nexus Repository](../servicios/nexus.md) | Objetivo | un solo servicio para imágenes OCI + proxy npm |
| Git | [Forgejo](../servicios/forgejo.md) | **Actual** (ADR-010) | self-hosted, liviano, corriendo en `devops01`; CI con Forgejo Actions pendiente |
| Observabilidad completa | [Prometheus + Grafana + Loki](../observabilidad/arquitectura.md) | Objetivo | métricas, logs y disponibilidad con el ecosistema más adoptado |
| Observabilidad liviana | [Uptime Kuma](../servicios/uptime-kuma.md) + [Beszel](../servicios/beszel.md) | **Actual** — ambos completos (hub + agente) | disponibilidad + CPU/RAM/disco sin el setup de exporters de Prometheus |
| Automatización | [n8n](../servicios/n8n.md) | **Actual** — `core01`, n8n 2.38.7 + Postgres 17 | workflows visuales, conecta el resto de los servicios |
| Gestor de contraseñas | [Vaultwarden](../servicios/vaultwarden.md) | **Actual** — `core01`, Vaultwarden 1.37.2 | Bitwarden-compatible, propio; resuelve la reutilización de contraseñas detectada durante el build |
| Dashboard de servicios | [Homepage](../servicios/homepage.md) | **Actual** — `core01`, Homepage v2.3.0 | landing con links y estado; candidato para la pantalla táctil |
| Firewall/red | [OPNsense](../red/firewall-opnsense.md) | Objetivo, sin hardware todavía | segmentación real cuando exista el appliance dedicado |
| DNS | [AdGuard Home](../red/dns-adguard.md) | **Actual** — LXC 100 en `oscar-core` | bloqueo de publicidad + DNS interno; reemplazó a Pi-hole, elegido por el script de instalación usado, no por una razón técnica fuerte |
| Acceso remoto | [Cloudflare Tunnel + Access](../servicios/cloudflare-tunnel.md) | **Actual** — 5 servicios publicados en `oscarlab.com.ar`, cada uno con Access delante | cero puertos abiertos, identidad delante de paneles |
| Backups | [Restic](../servicios/restic.md) + [estrategia 3-2-1](../backup-dr/estrategia-321.md) | Objetivo | cifrado, deduplicado, backend agnóstico |
| Hogar | [Home Assistant](../servicios/home-assistant.md) | **Actual** — VM 101 `haos-18.2` en `oscar-core` | estándar de facto en automatización doméstica self-hosted |
| Indicador visual | [`oscar-led-controller`](../hardware/led-status.md) (app propia) | **Actual** (código) — Hue/Tapo hoy, WS2812B+ESP32 planeado | traduce el estado real de O.S.C.A.R. a color/animación en una luz física |
| IA | [Agentes + MCP + RAG](../ia/vision-general.md) | Futuro (fases) | capa final, sobre todo lo anterior ya observable |

Cada fila tiene su propia página con instalación, seguridad, backup y troubleshooting — esta tabla es el mapa, no el detalle. Si una elección todavía no está tomada, dice "Decisión pendiente" en vez de inventarse una para completar la tabla.

Ver también: [visión general](./vision-general.md) para el diagrama de capas completo, y [topología lógica](./topologia-logica.md) para cómo se conecta todo esto en red.
