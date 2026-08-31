---
title: Corte eléctrico / UPS
sidebar_position: 11
---

# Corte eléctrico / UPS

:::caution Estado actual vs. objetivo
El UPS y el estabilizador **existen físicamente**, pero hoy están fuera del rack, sin dedicar a `pve01` y sin salida de monitoreo (NUT/USB) conectada — ver [inventario](../../inventory/hardware.yaml). Hasta que se reubiquen y conecten, un corte eléctrico sigue siendo un apagado sucio de `pve01`: no hay autonomía ni aviso automático de "batería baja" para disparar los pasos 1-5. Priorizar la integración (reubicar + conectar NUT) es de las tareas más baratas del roadmap — es hardware que ya está pagado, solo falta cablear y configurar software. Mientras tanto, lo único accionable ante un corte es el paso 6 (recuperación al volver la energía) y verificar que Proxmox arrancó sin corrupción de filesystem.
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
