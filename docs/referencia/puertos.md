---
title: Puertos de referencia
sidebar_position: 3
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
| Nexus | 8081 UI/API, **8082 registry Docker** (puerto HTTP dedicado, nunca por el proxy) | interno (`devops`) |
| Argo CD | Ingress Traefik en `argocd.oscar.home` (puerto 80, no port-forward) | interno, resuelve vía wildcard DNS — ver [DNS con AdGuard Home](../red/dns-adguard.md) |
| Forgejo | 3000 HTTP / 2222 SSH → 22 interno | interno (`devops`), detrás de NPM en `git.oscar.home` |
| Beszel | 8090 hub / 45876 agente (protocolo propio, no HTTP — nunca usarlo como `siteMonitor`) | interno, un hub + tres agentes (`core`/`devops`/`k3s`) |
| k3s / Traefik | 80/443 (`LoadBalancer` de k3s, IP del nodo `k3s`) | interno, ingress de todas las apps `*.oscar.home` en k3s |
| MinIO | 9000 API / 9001 consola | interno (laboratorio) |
| Home Assistant | 8123 | interno/proxy |
| MQTT | 1883/8883 | IoT/HA selectivo |
| [Minecraft](../juegos/minecraft.md) | 25565 TCP (juego Java) / 19132 UDP (Bedrock, vía Geyser) / 25575 TCP (RCON) | juego según [exposición elegida](../juegos/vision-general.md#exposición-a-internet); RCON nunca publicado |
| [Counter-Strike 2](../juegos/counter-strike.md) | 27015 TCP+UDP | juego según [exposición elegida](../juegos/vision-general.md#exposición-a-internet) |

Confirmar siempre la configuración real del servicio.

:::caution Colisión conocida
Grafana y Forgejo usan **3000** como puerto interno por defecto. Si ambos corren como contenedores Docker en el mismo host, remapear el puerto publicado de al menos uno de los dos (ej. `"3001:3000"`) — no asumir que "puerto por defecto" es libre solo porque es el default de la imagen.
:::
