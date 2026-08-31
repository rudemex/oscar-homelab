---
title: Argo CD OutOfSync
sidebar_position: 12
---

# Argo CD OutOfSync

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. `argocd app get <app>` o revisar en la UI qué recursos difieren (`Diff`).
2. Distinguir dos casos: (a) alguien aplicó un cambio manual con `kubectl` que Argo todavía no revirtió, o (b) el repo Git tiene un cambio que Argo no pudo aplicar (error de sync).
3. Si es (a): decidir si el cambio manual es válido. Si lo es, llevarlo a Git y hacer commit; si no, dejar que Argo lo revierta con `argocd app sync <app>`.
4. Si es (b): `argocd app get <app> --show-operation` para ver el error del último sync; corregir el manifiesto en Git, no parchear el cluster a mano.
5. Revisar si hay un `SyncWindow` o `Health Check` personalizado bloqueando la reconciliación.
6. Confirmar que `selfHeal`/`prune` estén configurados como se espera — si `selfHeal: false`, un drift puede quedar OutOfSync indefinidamente hasta un sync manual, lo cual puede ser intencional.
7. Tras corregir, `argocd app sync <app>` y validar `Healthy`/`Synced`.

## Validación de salida

- servicio responde desde la perspectiva del usuario;
- monitoreo vuelve a normal;
- no quedaron jobs/backups rotos;
- cambios manuales están documentados y, si eran válidos, ya están en Git (no solo aplicados a mano);
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
