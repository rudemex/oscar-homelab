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

## Comandos de referencia (vzdump)

Backup manual de una VM/LXC puntual, en modo `snapshot` (no detiene el guest) hacia un storage de backup ya definido en Proxmox:

```bash
# backup de una sola VM/LXC
vzdump 101 --storage backup-local --mode snapshot --compress zstd

# backup de todas las VMs/LXC marcadas para backup, con notificación
vzdump --all --storage backup-local --mode snapshot --mailto oscar@example.com
```

En producción esto se programa como job desde **Datacenter → Backup** en la UI (o `/etc/pve/jobs.cfg`), no ejecutando `vzdump` a mano cada vez — la UI genera el mismo comando por debajo.

Restore desde `vzdump`, primero listando qué hay disponible en el storage:

```bash
pvesm list backup-local
qmrestore /mnt/pve/backup-local/dump/vzdump-qemu-101-*.vma.zst 199 --storage local-lvm
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
