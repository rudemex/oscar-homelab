---
title: Índice de runbooks
sidebar_position: 1
slug: /runbooks/indice-runbooks
---

# Runbooks

Un runbook es un procedimiento operativo, no una explicación teórica. Debe poder ejecutarse bajo presión.

| Runbook | Cuándo usarlo |
|---|---|
| [Host Proxmox inaccesible](./proxmox-inaccesible.md) | no responde UI/ping/SSH |
| [VM caída](./vm-caida.md) | VM detenida o no saludable |
| [Disco lleno](./disco-lleno.md) | filesystem/datastore alto |
| [DNS caído](./dns-caido.md) | clientes no resuelven |
| [Servicio Docker caído](./docker-servicio-caido.md) | contenedor unhealthy/down |
| [k3s degradado](./k3s-degradado.md) | nodo/pods no Ready |
| [Backup fallido](./backup-fallido.md) | job no completó |
| [Restaurar VM](./restore-vm.md) | recuperación completa |
| [Rotar secreto](./rotacion-secreto.md) | exposición/renovación |
| [Corte eléctrico](./corte-electrico.md) | UPS en batería o apagado planificado |
| [Argo CD OutOfSync](./argocd-outofsync.md) | drift entre Git y el cluster, o sync fallido |
| [Prometheus target down](./prometheus-target-down.md) | un exporter/host deja de reportar métricas |
| [Grafana no responde](./grafana-no-responde.md) | UI caída o extremadamente lenta |
| [Nexus lleno](./nexus-lleno.md) | datastore de artefactos/registry al límite |
| [Temperatura alta](./temperatura-alta.md) | Dell o rack por encima de rango normal |
