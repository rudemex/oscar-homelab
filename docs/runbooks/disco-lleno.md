---
title: Disco lleno
sidebar_position: 4
---

# Disco lleno

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Identificar filesystem/datastore exacto.
2. No borrar archivos al azar.
3. Detectar top consumers y crecimiento reciente.
4. Revisar logs, imágenes, blobs, backups temporales y retención.
5. Liberar espacio seguro o ampliar storage.
6. Ajustar alerta/retención para evitar recurrencia.

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
