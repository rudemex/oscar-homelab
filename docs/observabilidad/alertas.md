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

**Presentación en Discord:** estos 3 niveles se mapean a un esquema de 7 niveles (`INFO`/`SUCCESS`/`WARNING`/`DEGRADED`/`CRITICAL`/`RECOVERY`/`FAILED`) solo al formatear un mensaje para Discord — no es un esquema paralelo, es una capa de presentación que distingue además eventos operativos (éxito/fallo/recuperación) que este esquema de 3 niveles no cubre. Ver la tabla completa en [Discord → Severidades](../servicios/discord.md#severidades).
