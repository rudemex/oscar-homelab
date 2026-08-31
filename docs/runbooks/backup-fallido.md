---
title: Backup fallido
sidebar_position: 8
---

# Backup fallido

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Identificar job, origen y destino.
2. Revisar espacio y conectividad del destino.
3. Leer error del último intento.
4. Corregir causa y ejecutar un retry controlado.
5. Validar integridad/check si la herramienta lo soporta.
6. No marcar resuelto hasta confirmar una copia válida.

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
