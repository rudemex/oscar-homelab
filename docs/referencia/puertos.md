---
title: Puertos de referencia
sidebar_position: 2
---

# Puertos

La tabla ayuda a diagnosticar; no significa que deban abrirse entre todas las redes.

| Servicio | Puerto típico | Exposición |
|---|---:|---|
| SSH | 22 | MGMT/VPN |
| DNS | 53 TCP/UDP | LAN seleccionada |
| HTTP | 80 | proxy/app |
| HTTPS | 443 | proxy/app |
| Proxmox UI | 8006 | MGMT |
| Grafana | 3000 | interno/proxy |
| Prometheus | 9090 | interno |
| Loki | 3100 | interno (solo Grafana/promtail) |
| Uptime Kuma | 3001 | interno |
| n8n | 5678 | interno/proxy |
| Nexus | 8081 | interno (npm proxy/hosted) |
| Argo CD | 8080 (port-forward local) → svc 443 | MGMT, sin publicar |
| Forgejo | 3000 HTTP / 22 SSH (decisión pendiente) | interno |
| MinIO | 9000 API / 9001 consola | interno (laboratorio) |
| Home Assistant | 8123 | interno/proxy |
| MQTT | 1883/8883 | IoT/HA selectivo |

Confirmar siempre la configuración real del servicio.

:::caution Colisión conocida
Grafana y Forgejo usan **3000** como puerto interno por defecto. Si ambos corren como contenedores Docker en el mismo host, remapear el puerto publicado de al menos uno de los dos (ej. `"3001:3000"`) — no asumir que "puerto por defecto" es libre solo porque es el default de la imagen.
:::
