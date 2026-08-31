---
title: Logs con Loki
sidebar_position: 4
---

# Logs

Loki no recolecta logs por sí mismo; necesita un agente. Ver la instalación de **Promtail** junto a Loki en [instalación del stack](./instalacion-stack.md#4b-loki--promtail).

## Labels recomendadas

Labels de baja cardinalidad:

```text
host
service
namespace
environment
```

No usar request IDs o usernames como labels de Loki; esos valores se consultan dentro del contenido del log.

## Correlación

Un buen flujo de incidente:

1. Uptime Kuma detecta caída;
2. Grafana muestra spike de RAM;
3. Loki muestra `OOMKilled`/error asociado;
4. runbook indica mitigación;
5. luego se corrige causa raíz.
