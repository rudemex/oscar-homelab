---
title: Arquitectura de observabilidad
sidebar_position: 1
---

# Observabilidad

Queremos responder tres preguntas rápidamente:

1. ¿está caído?
2. ¿por qué está degradado?
3. ¿qué cambió antes de fallar?

```mermaid
flowchart LR
  NODES[Nodos/exporters] --> PROM[Prometheus]
  APPS[Apps] --> PROM
  LOGS[Logs] --> LOKI[Loki]
  PROM --> GRAF[Grafana]
  LOKI --> GRAF
  PROM --> ALERT[Alertmanager]
  UPTIME[Uptime Kuma] --> NOTIFY[Notificaciones]
  ALERT --> NOTIFY
```

## Golden signals caseras

- latencia;
- tráfico;
- errores;
- saturación.

A eso sumamos temperatura, batería UPS y salud de discos por tratarse de hardware doméstico.
