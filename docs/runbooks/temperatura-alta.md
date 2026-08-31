---
title: Temperatura alta
sidebar_position: 16
---

# Temperatura alta (Dell / rack)

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Confirmar la lectura: `sensors` (paquete `lm-sensors`) en el host Proxmox, o el dashboard de Grafana si ya hay un exporter de temperatura configurado.
2. Distinguir carga vs. ambiente: ¿subió la temperatura porque hay una carga sostenida inusual (backup pesado, build de CI, restore drill), o subió sin cambio de carga aparente (posible falla de ventilación)?
3. Si es carga: es esperable dentro de rango; validar que no supere el umbral crítico del fabricante y dejar que baje al terminar la tarea.
4. Si es ambiente: revisar físicamente el rack — entrada de aire obstruida, panel de ventilación sucio, equipos calientes sin espacio de respiración (ver [layout del rack](../hardware/rackmate-t2.md)).
5. Revisar `dmesg`/logs del kernel por eventos de throttling térmico (`thermal_zone`, `cpu clock throttled`) — si ya está actuando, el sistema se está protegiendo solo, pero hay margen limitado antes de shutdown térmico automático.
6. Como mitigación inmediata si la temperatura sigue subiendo: migrar/detener workloads no críticos (C3/C4) para reducir carga mientras se resuelve la causa física.
7. Tras resolver la causa física, confirmar que la temperatura vuelve a rango normal en reposo y bajo carga simulada.

## Validación de salida

- servicio responde desde la perspectiva del usuario;
- monitoreo vuelve a normal;
- no quedaron jobs/backups rotos;
- cambios manuales están documentados;
- si hubo causa recurrente, existe issue/tarea de remediación (ej. mejorar ventilación del rack antes de sumar más equipos calientes).

## Datos a registrar

```text
Inicio:
Detección:
Impacto:
Causa:
Acciones:
Recuperación:
Duración:
Follow-up:
```
