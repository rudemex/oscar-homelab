---
title: Backup de VMs y LXC
sidebar_position: 5
---

# Backups en Proxmox

Snapshot y backup no son sinónimos.

- **snapshot**: punto rápido para volver atrás, normalmente ligado al mismo storage;
- **backup**: copia recuperable en un storage independiente.

## Política inicial

| Tipo | Frecuencia sugerida | Retención inicial |
|---|---|---|
| C1 | diaria | 7 diarias + 4 semanales |
| C2 | diaria/semanal | según datos |
| C3 | semanal | 4 copias |
| C4 | opcional | recrear desde Git |

Los valores se ajustan cuando conozcamos volumen y NAS.

## Job real ya configurado

**Estado:** Actual — hay un job de backup automático corriendo hoy, verificado en `/etc/pve/jobs.cfg` de `oscar-core`:

```text
vzdump: backup-94c323b5-388e
    schedule mon..fri 00:00
    all 1
    compress zstd
    enabled 1
    mode snapshot
    prune-backups keep-last=5,keep-monthly=1,keep-yearly=6
    storage Backups
```

Corre de lunes a viernes a medianoche, backupea **todas** las VMs/LXC (`all 1`, no una lista puntual) en modo `snapshot`, comprimido `zstd`, hacia el storage `Backups` (`dir`, montado en `/mnt/pve/Backups`, **no** `backup-local` como decía esta página antes — ese nombre nunca existió, era un placeholder que quedó como si fuera real). Retención: últimos 5 + 1 mensual + 6 anuales — más agresiva que la "política inicial" de la tabla de arriba, que quedó como referencia conceptual sin actualizar contra lo que realmente se configuró.

## Comandos de referencia (vzdump)

Backup manual de una VM/LXC puntual, fuera del job programado, en modo `snapshot` (no detiene el guest):

```bash
# backup de una sola VM/LXC (reemplazar <VMID> por el real, ej. 102 = core01)
vzdump <VMID> --storage Backups --mode snapshot --compress zstd

# backup de todas las VMs/LXC, igual que el job programado pero a demanda
vzdump --all --storage Backups --mode snapshot --mailto oscar@example.com
```

El job real de arriba ya cubre el caso de "todas, programado" — estos comandos sirven para un backup puntual fuera de horario (ej. antes de un cambio riesgoso).

Restore desde `vzdump`, primero listando qué hay disponible en el storage:

```bash
pvesm list Backups
qmrestore /mnt/pve/Backups/dump/vzdump-qemu-<VMID>-*.vma.zst 199 --storage local-lvm
```

Usar un VMID distinto (`199` en el ejemplo) para restaurar en aislamiento y validar antes de reemplazar el original — ver [restore drill](#restore-drill).

**Proxmox Backup Server (PBS)** es la opción recomendada cuando el volumen crezca: backups incrementales reales (deduplicados a nivel de bloque) en vez de copias completas repetidas de `vzdump`. Hoy no está desplegado (ver [backlog](../roadmap/backlog.md)); mientras tanto `vzdump` hacia un storage de tipo directorio/NFS cumple el mismo propósito con menos eficiencia.

## Restore drill

Cada trimestre, como mínimo para servicios importantes:

1. elegir un backup;
2. restaurar con nombre/IP aislados;
3. iniciar sin colisionar con producción;
4. validar servicio y datos;
5. documentar tiempo y problemas;
6. destruir restore de prueba.

Un backup que nunca se restauró es una hipótesis.
