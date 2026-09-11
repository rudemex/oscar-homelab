---
title: Stack elegido
sidebar_position: 3
---

# Qué vamos a usar

Una cosa es el mínimo técnico para correr algo (ver [requisitos mínimos](../referencia/requisitos-minimos.md)) y otra distinta es qué elegimos nosotros específicamente, y por qué. Esta tabla es esa segunda cosa: una decisión concreta por capa, no todas las opciones posibles.

| Capa | Elegimos | Estado | Por qué (resumen) |
|---|---|---|---|
| Virtualización | [Proxmox VE](../proxmox/instalacion.md) | **Actual** — `oscar-core`, VE 9.2 | snapshots/backups por VM, aislamiento entre plataformas |
| Contenedores | [Docker + Compose](../servicios/docker-compose.md) | Objetivo | estándar de facto, curva de entrada baja |
| Orquestación | [k3s](../kubernetes/instalacion-k3s.md) | Objetivo | Kubernetes real con bajo overhead en un nodo chico |
| GitOps | [Argo CD](../kubernetes/instalacion-argocd.md) | Objetivo | reconciliación declarativa, UI para aprender el modelo |
| Registry/artefactos | [Nexus Repository](../servicios/nexus.md) | Objetivo | un solo servicio para imágenes OCI + proxy npm |
| Git | [Forgejo](../servicios/forgejo.md) | Decisión pendiente | self-hosted, liviano — a confirmar contra alternativas |
| Observabilidad | [Prometheus + Grafana + Loki](../observabilidad/arquitectura.md) + [Uptime Kuma](../servicios/uptime-kuma.md) | Objetivo | métricas, logs y disponibilidad con el ecosistema más adoptado |
| Automatización | [n8n](../servicios/n8n.md) | Objetivo | workflows visuales, conecta el resto de los servicios |
| Firewall/red | [OPNsense](../red/firewall-opnsense.md) | Objetivo, sin hardware todavía | segmentación real cuando exista el appliance dedicado |
| DNS | [AdGuard Home](../red/dns-adguard.md) | **Actual** — LXC 100 en `oscar-core` | bloqueo de publicidad + DNS interno; reemplazó a Pi-hole, elegido por el script de instalación usado, no por una razón técnica fuerte |
| Acceso remoto | [Cloudflare Tunnel + Access](../servicios/cloudflare-tunnel.md) | Objetivo | cero puertos abiertos, identidad delante de paneles |
| Backups | [Restic](../servicios/restic.md) + [estrategia 3-2-1](../backup-dr/estrategia-321.md) | Objetivo | cifrado, deduplicado, backend agnóstico |
| Hogar | [Home Assistant](../servicios/home-assistant.md) | **Actual** — VM 101 `haos-18.2` en `oscar-core` | estándar de facto en automatización doméstica self-hosted |
| IA | [Agentes + MCP + RAG](../ia/vision-general.md) | Futuro (fases) | capa final, sobre todo lo anterior ya observable |

Cada fila tiene su propia página con instalación, seguridad, backup y troubleshooting — esta tabla es el mapa, no el detalle. Si una elección todavía no está tomada, dice "Decisión pendiente" en vez de inventarse una para completar la tabla.

Ver también: [visión general](./vision-general.md) para el diagrama de capas completo, y [topología lógica](./topologia-logica.md) para cómo se conecta todo esto en red.
