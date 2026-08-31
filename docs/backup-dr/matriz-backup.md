---
title: Matriz de backup
sidebar_position: 2
---

# Matriz

Completar a medida que se instalan servicios. El destino "NAS" en esta tabla es aspiracional: el inventario actual **no tiene un NAS confirmado** (ver [decisiones pendientes](../roadmap/backlog.md)); hasta que exista, el destino real es el SSD SATA del propio Dell (staging) más una copia off-site manual, lo cual **no cumple 3-2-1 todavía** — ver [estrategia 3-2-1](./estrategia-321.md).

| Categoría | Servicio/alcance | Estado | RPO | Backup | Destino | Restore probado |
|---|---|---|---:|---|---|---|
| VM | core01, devops01, k3s01 | pendiente | 24h | Proxmox VM backup (vzdump) | NAS/offsite (futuro) | ☐ |
| LXC | utilidades livianas (DNS, jumpbox) | pendiente | 24h | Proxmox LXC backup (vzdump) | NAS/offsite (futuro) | ☐ |
| Configuración Proxmox | `/etc/pve`, storage.cfg, red | pendiente | 24h | config/export | NAS/offsite | ☐ |
| Secrets | `.env` reales, claves SSH, encryption keys | pendiente | al cambiar | copia cifrada separada del backup general | offsite cifrado, acceso restringido | ☐ |
| Docker volumes | volúmenes con estado (`n8n-data`, `pgdata`, etc.) | pendiente | 24h | snapshot/backup del volumen o dump de la app | NAS/offsite (futuro) | ☐ |
| Base de datos | PostgreSQL de despliegues (ej. `docker-api-postgres`) | pendiente | 24h | `pg_dump` consistente | NAS/offsite (futuro) | ☐ |
| n8n | workflows, credenciales, `N8N_ENCRYPTION_KEY` | pendiente | 24h | DB dump + encryption key (por separado) | NAS/offsite (futuro) | ☐ |
| Git | repos propios/mirrors | pendiente | 24h | repo mirror | offsite | ☐ |
| Kubernetes manifests | repo GitOps (`oscar-gitops`) | n/a | — | ya vive en Git remoto; no requiere backup adicional | remoto Git | n/a |
| Home Assistant | config, historial, `.storage` | pendiente | 24h | native backup (Snapshot/Backup integrado) | NAS/offsite (futuro) | ☐ |
| Nexus | blobstores + metadata (`/nexus-data`) | pendiente | 24h o al cambiar artefactos alojados | export de metadata (tarea interna) + backup del árbol `nexus-data` completo | NAS/offsite (futuro) | ☐ |
| Observabilidad (Prometheus/Loki) | TSDB/chunks en disco | n/a | — | no crítico, recreable scrapeando/reingestando de nuevo; la config (`prometheus.yml`, reglas, `loki-config.yaml`) ya vive en Git y no requiere backup aparte | remoto Git | n/a |
| Grafana | `grafana.db` (usuarios, API keys, alerting state) | pendiente | 24h | copia de `grafana.db`; dashboards/datasources provisionados desde Git se reconstruyen solos | NAS/offsite (futuro) | ☐ |
| Uptime Kuma | `kuma.db` (monitores, notificaciones, historial) | pendiente | 24h | copia de `kuma.db` con el contenedor detenido, o export nativo Settings → Backup | NAS/offsite (futuro) | ☐ |
| Repositorio Restic | password + integridad del repo | pendiente | al rotar | password del repo en gestor de contraseñas + copia offline; `restic check` periódico | 2+ ubicaciones físicas distintas | ☐ |

El check de "restore probado" es tan importante como el de "backup exitoso". Los manifiestos de Kubernetes se excluyen deliberadamente: si el repo GitOps está sano, el estado del cluster se reconstruye reaplicando (`argocd app sync`), así que respaldarlos por separado sería duplicar lo que Git ya garantiza.
