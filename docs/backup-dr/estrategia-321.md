---
title: Estrategia 3-2-1
sidebar_position: 1
---

# Backup 3-2-1

Objetivo conceptual:

- **3** copias de los datos importantes;
- **2** medios/ubicaciones diferentes;
- **1** copia off-site.

:::caution Estado actual vs. objetivo
El diagrama y la tabla de abajo describen el **target state**. Hoy O.S.C.A.R. **no tiene NAS** (figura como "decisión pendiente" en el [backlog](../roadmap/backlog.md)) ni copia off-site automatizada. Sin NAS, el esquema real disponible es: disco activo (M.2) + SSD SATA del mismo host como segunda copia local + una copia off-site manual (ej. subida cifrada a un proveedor de object storage). Esto **no cumple 3-2-1** todavía porque las dos primeras copias comparten el mismo host físico — un fallo del Dell completo (placa, fuente, robo) se lleva ambas. Tratar esta limitación como riesgo activo, no como detalle menor, hasta que exista una segunda ubicación física real.
:::

## O.S.C.A.R. — target state

```mermaid
flowchart LR
  PROD[Datos activos] --> LOCAL[Backup local/NAS]
  PROD --> VM[Backup VM/PBS]
  LOCAL --> OFF[Off-site cifrado]
```

No todo merece la misma política. Un manifiesto Kubernetes en Git puede recrearse; las fotos, DB o claves únicas no.

## O.S.C.A.R. — estado actual (sin NAS)

```mermaid
flowchart LR
  PROD[Datos activos · M.2] --> LOCAL[Copia local · SATA SSD, mismo host]
  LOCAL --> OFF[Off-site cifrado · manual]
```

Riesgo explícito: `PROD` y `LOCAL` están en el mismo chasis. Mitigación mínima mientras no haya NAS: priorizar que la copia `OFF` (off-site) exista y se verifique, aunque las primeras dos copias no estén en medios separados.

## Clasificación

| Dato | Método |
|---|---|
| config Git | remoto Git + clone local |
| VM | Proxmox backup |
| PostgreSQL | dump consistente + backup |
| n8n | DB + encryption key |
| Home Assistant | backup propio + copia externa |
| Nexus | config/blob backup + retención |
| métricas | puede ser recreable según retención |

## Destino off-site

**Decision Pending.** Candidatos razonables para un homelab doméstico, en orden de simplicidad: object storage compatible con S3 (ej. Backblaze B2 o similar, cifrado antes de subir con `restic`/`rclone crypt`), o un segundo equipo físico en otra ubicación (casa de un familiar, trabajo) sincronizado periódicamente. No se fija un proveedor hasta decidir presupuesto y volumen real de datos a respaldar.
