---
title: k3s degradado
sidebar_position: 7
---

# k3s degradado

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. `kubectl get nodes -o wide`.
2. `kubectl get pods -A` y localizar Pending/CrashLoop/OOM.
3. `kubectl describe` sobre recurso afectado.
4. Revisar eventos y capacidad del nodo.
5. Validar DNS/storage/Ingress según síntoma.
6. Si Argo gestiona el recurso, corregir Git en vez de parchear permanentemente a mano.

## Validación de salida

- servicio responde desde la perspectiva del usuario;
- monitoreo vuelve a normal;
- no quedaron jobs/backups rotos;
- cambios manuales están documentados;
- si hubo causa recurrente, existe issue/tarea de remediación.

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
