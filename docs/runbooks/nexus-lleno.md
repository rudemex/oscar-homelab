---
title: Nexus lleno
sidebar_position: 15
---

# Nexus lleno (datastore >90%)

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Confirmar el síntoma: ¿pushes/pulls fallando con error de espacio, o solo la alerta de disco disparó preventivamente? Ver [runbook de disco lleno](./disco-lleno.md) para el diagnóstico general del filesystem.
2. Identificar qué repositorio creció: en Nexus UI, `Administration → Repository → Blob Stores`, ver tamaño por blob store (npm-hosted suele crecer más rápido que npm-proxy con una cache razonable).
3. Revisar si hay una política de limpieza (`Cleanup Policies`) configurada y activa — si nunca se configuró, es la causa raíz más probable, no un pico de tráfico puntual.
4. Ejecutar limpieza manual como mitigación inmediata: `Administration → Repository → Cleanup Policies → Run` sobre el repo afectado, y `Administration → System → Task` para correr la tarea de "Compact blob store" después.
5. Si es el proxy de npm el que creció: revisar TTL de cache configurado — cachear indefinidamente versiones que nunca se vuelven a pedir desperdicia espacio.
6. Como mitigación de fondo, definir una política de retención explícita (ej. mantener solo las últimas N versiones publicadas por componente) en vez de dejar crecer sin límite — documentarlo en [Nexus Registry](../devops/nexus-registry.md).
7. Verificar que el pipeline (CI) vuelve a poder hacer push tras liberar espacio.

## Validación de salida

- servicio responde desde la perspectiva del usuario;
- monitoreo vuelve a normal;
- no quedaron jobs/backups rotos;
- cambios manuales están documentados;
- si hubo causa recurrente, existe issue/tarea de remediación (política de cleanup permanente).

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
