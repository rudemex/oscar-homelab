---
title: Restaurar una VM
sidebar_position: 9
---

# Restaurar una VM

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Confirmar backup y fecha objetivo.
2. Restaurar con VMID/nombre aislado si producción aún existe.
3. Evitar IP duplicada.
4. Iniciar en red aislada cuando sea posible.
5. Validar sistema, app y datos.
6. Documentar tiempo y decidir switchover.

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
