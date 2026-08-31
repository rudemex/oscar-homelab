---
title: Proxmox inaccesible
sidebar_position: 2
---

# Proxmox inaccesible

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Confirmar si falla solo la UI o también ping/SSH.
2. Probar gateway y switch para descartar red general.
3. Revisar link físico/LED/puerto del switch.
4. Si SSH funciona, revisar servicios Proxmox y espacio de disco.
5. Si el host está congelado, documentar síntomas antes de forzar reinicio cuando sea posible.
6. Después de recuperar, validar todas las VMs y revisar logs previos al incidente.

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
