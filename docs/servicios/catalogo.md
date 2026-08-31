---
title: Catálogo de servicios
sidebar_position: 1
---

# Catálogo de servicios

La tabla resume el rol previsto. **Objetivo** no significa “instalar ya”: cada servicio entra cuando su fase del roadmap lo requiere.

| Servicio | Estado | Ubicación sugerida | Para qué lo usamos |
|---|---|---|---|
| [Docker y Docker Compose](./docker-compose.md) | Objetivo · Core | VM `core01` y, cuando convenga, VMs específicas | ejecutar n8n, Uptime Kuma, dashboards y utilidades |
| [EasyPanel](./easypanel.md) | Laboratorio · Plataforma de apps | VM Docker dedicada o `core01` durante la etapa inicial | comparar un PaaS casero contra el flujo GitOps; redundante con Compose+k3s si no aporta algo distinto |
| [Sonatype Nexus Repository](./nexus.md) | Objetivo · DevOps | VM `devops01` | proxy/cache de npm |
| [Forgejo / Git local](./forgejo.md) | Objetivo · Decisión pendiente | VM `devops01` o VM pequeña dedicada | mirror de repositorios importantes |
| [CI Runner](./ci-runner.md) | Objetivo · Decisión pendiente | VM `devops01` o runners efímeros | compilar proyectos Node |
| [Argo CD](./argocd.md) | Objetivo · GitOps | cluster k3s | sincronizar Helm/manifests |
| [Prometheus](./prometheus.md) | Objetivo · Observabilidad | VM observabilidad o k3s, según fase | métricas de hosts |
| [Grafana](./grafana.md) | Objetivo · Observabilidad | VM observabilidad o Docker Core | dashboard de rack |
| [Loki](./loki.md) | Objetivo · Logs | VM observabilidad o k3s | logs de contenedores |
| [Uptime Kuma](./uptime-kuma.md) | Objetivo · Disponibilidad | Docker Core | HTTP checks |
| [n8n](./n8n.md) | Objetivo · Automatización | Docker Core o VM dedicada cuando crezca | backups coordinados |
| [Home Assistant](./home-assistant.md) | Objetivo · Hogar | Raspberry Pi 5 futura o VM dedicada | automatización doméstica |
| [Cloudflare Tunnel + Access](./cloudflare-tunnel.md) | Objetivo · Acceso remoto | VM Core o nodo dedicado de conectividad | publicar una demo web |
| [Eclipse Mosquitto MQTT](./mosquitto.md) | Laboratorio / Hogar | Raspberry Pi o VM Core | sensores Pi Zero |
| [Ollama](./ollama.md) | Laboratorio · IA local | Dell/VM solo para modelos compatibles con recursos; hardware futuro para cargas mayores | probar LLM local |
| [Open WebUI](./open-webui.md) | Laboratorio · IA | Docker Core conectado a proveedor/modelo permitido | UI para Ollama |
| [Restic](./restic.md) | Objetivo · Backup | clientes/VMs que necesiten backup de archivos | backup de configs |
| [MinIO](./minio.md) | Laboratorio · Object Storage | VM/storage de laboratorio | aprender API S3 |

## Criterio de adopción

Antes de sumar un servicio, responder:

1. ¿qué problema real resuelve?
2. ¿ya tenemos otro servicio que resuelve lo mismo?
3. ¿qué datos persistirá?
4. ¿qué backup necesita?
5. ¿cómo sabremos que está sano?
6. ¿qué dependencia nueva introduce?
7. ¿podemos destruirlo y reconstruirlo desde Git?

El objetivo no es maximizar la cantidad de logos del dashboard; es maximizar lo que aprendemos y lo fácil que resulta operar el conjunto.
