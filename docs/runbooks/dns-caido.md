---
title: DNS caído
sidebar_position: 5
---

# DNS caído

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. Probar resolución contra DNS1 y DNS2 por separado.
2. Verificar conectividad IP al resolver.
3. Consultar estado de Pi-hole/resolver.
4. Comprobar upstream DNS.
5. Si un resolver está caído, mantener servicio con el secundario y recuperar sin modificar todos los clientes.
6. Validar resolución interna y externa.

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
