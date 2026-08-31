---
title: Grafana no responde
sidebar_position: 14
---

# Grafana no responde

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Confirmar el síntoma desde Uptime Kuma (¿lo detectó como caído o está lento pero responde?) — determina si esto es una caída dura o una degradación.
2. `docker compose ps` en el host de observabilidad: ¿el contenedor está `Up`, reiniciando en loop, o `Exited`?
3. Si está reiniciando: `docker compose logs grafana --tail 100` — causas típicas son datasource inválido en el provisioning, permisos del volumen `grafana-data`, o plugin roto tras un upgrade de versión.
4. Si el contenedor está `Up` pero la UI no responde: revisar CPU/RAM del host (¿el host está saturado por otra causa, no por Grafana?) y latencia — Grafana lento suele ser un datasource (Prometheus/Loki) lento respondiendo consultas, no Grafana en sí.
5. Probar acceso directo al contenedor (`curl http://localhost:3000/api/health` desde el propio host) para descartar problema de reverse proxy/Tunnel en vez de Grafana.
6. Si el volumen de datos está corrupto (raro, pero posible tras un corte eléctrico mal manejado): restaurar desde el backup del provisioning en Git más el último backup del volumen — ver [matriz de backup](../backup-dr/matriz-backup.md).
7. Reiniciar el contenedor solo después de revisar logs, no como primer paso.

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
