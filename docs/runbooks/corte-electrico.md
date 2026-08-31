---
title: Corte eléctrico / UPS
sidebar_position: 11
---

# Corte eléctrico / UPS

:::caution Estado actual vs. objetivo
El UPS todavía es [decisión pendiente](../../inventory/hardware.yaml) — hoy no existe. Sin UPS, un corte eléctrico es directamente un apagado sucio de `pve01`: no hay autonomía ni aviso previo, y los pasos 1-5 de abajo no aplican hasta que exista el hardware. Mientras tanto, lo único accionable ante un corte es el paso 6 (recuperación al volver la energía) y verificar que Proxmox arrancó sin corrupción de filesystem. Este runbook describe el procedimiento completo para cuando el UPS esté instalado.
:::

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento (con UPS instalado)

1. Confirmar si la UPS está en batería y autonomía.
2. Detener cargas de laboratorio primero.
3. Guardar/terminar jobs sensibles.
4. Apagar VMs según criticidad.
5. Apagar Proxmox de forma limpia antes de batería crítica.
6. Al volver energía, arrancar red/storage antes de workloads y validar servicios.

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
