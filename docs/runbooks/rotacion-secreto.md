---
title: Rotar un secreto
sidebar_position: 10
---

# Rotar un secreto

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Identificar todos los consumidores.
2. Crear secreto nuevo.
3. Actualizar consumidores de forma controlada.
4. Validar funcionamiento.
5. Revocar secreto anterior.
6. Buscar exposición en logs/Git y limpiar según procedimiento.

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
