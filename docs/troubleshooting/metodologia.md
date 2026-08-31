---
title: Metodología
sidebar_position: 1
---

# Troubleshooting por capas

Cuando “no anda”, no empezar reinstalando.

```text
1. Energía
2. Link físico
3. IP / routing
4. DNS
5. Puerto / firewall
6. Proceso / contenedor / pod
7. Dependencia (DB, storage, API)
8. Aplicación
```

## Preguntas

- ¿qué cambió?
- ¿desde cuándo?
- ¿afecta a uno o a todos?
- ¿funciona por IP pero no por nombre?
- ¿funciona desde el host pero no desde otro cliente?
- ¿hay disco/RAM disponible?
- ¿el problema está en producción o solo en monitoring?

## Evidencia antes de cambiar

Capturar logs, métricas, estado y timestamps. Reiniciar demasiado pronto puede borrar la evidencia que explicaba la falla.
