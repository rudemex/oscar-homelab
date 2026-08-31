---
title: Workflow de salud diario
sidebar_position: 2
---

# Informe diario de salud

## Flujo

```mermaid
flowchart LR
  CRON[Schedule] --> P[Prometheus]
  CRON --> U[Uptime Kuma]
  CRON --> B[Backups]
  P --> N[n8n]
  U --> N
  B --> N
  N --> SUM[Resumen]
  SUM --> MSG[Notificación]
```

## Contenido

- nodos caídos;
- CPU/RAM anormales;
- discos > 80%;
- backups recientes;
- servicios reiniciados;
- temperatura máxima;
- cambios relevantes.

La IA puede redactar el resumen, pero la recolección y los umbrales deben ser determinísticos.
