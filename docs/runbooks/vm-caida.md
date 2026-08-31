---
title: VM caída
sidebar_position: 3
---

# VM caída

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Identificar VM y criticidad.
2. Verificar si el host Proxmox está sano.
3. Revisar estado, último shutdown y espacio de storage.
4. Iniciar VM si no existe indicio de corrupción.
5. Validar IP, DNS y servicio.
6. Si vuelve a caer, no repetir reinicios indefinidamente: revisar causa raíz.

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
