---
title: Servicio Docker caído
sidebar_position: 6
---

# Servicio Docker caído

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. `docker compose ps` para estado.
2. Revisar logs recientes.
3. Validar healthcheck y dependencias (DB/DNS/storage).
4. Comprobar disco/memoria del host.
5. Reiniciar solo si la causa no indica corrupción o problema persistente.
6. Validar endpoint y abrir issue si se repite.

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
