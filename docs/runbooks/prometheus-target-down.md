---
title: Prometheus target down
sidebar_position: 13
---

# Prometheus target down

## Objetivo

Recuperar el servicio minimizando cambios improvisados y preservando evidencia para causa raíz.

## Procedimiento

1. En Prometheus UI, `Status → Targets`, identificar el/los targets en estado `down` y el último error (`context deadline exceeded`, `connection refused`, etc.).
2. Distinguir si es un target (host/servicio puntual) o varios simultáneos — varios a la vez suele indicar problema de red/VLAN, no del servicio individual.
3. Desde el host de Prometheus, probar alcance directo: `curl -sS http://<target>:<puerto>/metrics`.
4. Si `connection refused`: el exporter/servicio no está corriendo — revisar `systemctl status node_exporter` o el contenedor correspondiente.
5. Si timeout sin respuesta: sospechar de firewall/VLAN entre Prometheus y el target, o el host caído (ver [runbook de VM caída](./vm-caida.md) si aplica).
6. Si el target cambió de IP/hostname: actualizar `prometheus.yml` (o el service discovery correspondiente) y recargar con `curl -X POST http://localhost:9090/-/reload` (requiere `--web.enable-lifecycle`).
7. Confirmar que la alerta asociada (si existe) vuelve a estado normal.

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
