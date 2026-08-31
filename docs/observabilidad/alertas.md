---
title: Alertas
sidebar_position: 5
---

# Alertas accionables

Una alerta debe decir **qué pasó, dónde, desde cuándo y qué hacer después**.

## Ejemplo conceptual

```yaml
alert: DiskSpaceLow
expr: filesystem_free_ratio < 0.15
for: 15m
labels:
  severity: warning
annotations:
  summary: "Poco espacio en {{ $labels.instance }}"
  runbook: "/docs/runbooks/disco-lleno"
```

## Severidades

- `info`: observar, no despertar a nadie;
- `warning`: requiere acción planificable;
- `critical`: servicio esencial o riesgo de pérdida de datos.

Si todas son críticas, ninguna lo es.
