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
    all 1
    compress zstd
    enabled 1
    exclude 9000
    fleecing 0
    mode snapshot
    notes-template {{guestname}}
    notification-mode notification-system
    prune-backups keep-last=2,keep-monthly=1,keep-yearly=6
    repeat-missed 0
    schedule mon..fri 00:00
    script /var/lib/vz/snippets/oscar-led-vzdump-hook.sh
    storage Backups
```

(Revisado 2026-10-15.) Corre de lunes a viernes a medianoche y backupea **todas** las VMs/LXC (`all 1`) menos la plantilla `9000`, en modo `snapshot`, comprimido `zstd`, hacia el storage `Backups` (`dir`, `/mnt/pve/Backups`). Retención: últimos 2 + 1 mensual + 6 anuales.

**Disco de backups:** desde el 2026-10-13, `/mnt/pve/Backups` es un **SanDisk SSD Plus de 2 TB** interno por SATA (label `Backups2T`), con mount unit `/etc/systemd/system/mnt-pve-Backups.mount`. Reemplazó al SSD de 1 TB anterior (`FTM1TN325H`, retirado); los 602 GB que había se copiaron y se verificaron por checksum. En reposo está a ~45 °C y bajo carga llegó a 69 °C: conviene que tenga ventilación.

## Segunda copia de los backups (WD Green)

Desde el 2026-10-14, el **WD Green de 1 TB por USB** (label `BackupsCopia`, montado en `/mnt/storage` por fstab con `nofail`) guarda una segunda copia:

- `/usr/local/bin/oscar-backup-copy.sh`, disparado por `oscar-backup-copy.timer` **todos los días a las 04:00** (después del backup y de la limpieza).
- Copia `/mnt/pve/Backups/dump/` a `/mnt/storage/dump/` con `rsync -a --delete`. Si alguno de los dos discos no está montado, o hay un `vzdump` corriendo, no hace nada.
- **Modo automático según espacio:** si todos los backups entran en el 90 % del disco, copia exacta; si no, guarda solo el backup más reciente de cada VM/LXC y borra el resto de la copia.
- Logs: `journalctl -u oscar-backup-copy`.
- El disco tuvo reinicios de enlace USB en una prueba de lectura sostenida (sin errores de datos), por eso es la segunda copia y no la principal. Desde el reinicio del 14/10 no repitió errores.

La alerta `HostDiskCritical` (más del 95 %) también vigila `/mnt/storage`; `HostDiskHigh` (85 %) lo excluye porque está pensado para llenarse hasta el 90 %.

Para consultar el estado: `/backups` en Discord (bot [oscar-discord](../servicios/oscar-discord.md)) o `oscar_disks_status` de Hermes.

### Hookscript: el backup se ve en la tira LED (2026-09-25)

La línea `script` de arriba es un **hookscript de `vzdump`** que refleja el job en el `OscarState` de la [tira LED](../hardware/led-status.md): `backup` al arrancar el job (`job-start`), `healthy` al terminar (`job-end`), `critical` si el job entero aborta (`job-abort`). Cada llamada lleva `|| true` — si la tira no responde, el backup real sigue igual, es puramente cosmético. Habla por IP directa con header `Host` (no por `led.oscar.home`, que depende de la DNS de `network01`).

Se asoció al job por la API, no editando `jobs.cfg` a mano: `pvesh set /cluster/backup/backup-94c323b5-388e --script /var/lib/vz/snippets/oscar-led-vzdump-hook.sh`. El código vive versionado en `oscar-compose/hosts/oscar-core/`.

**Gotcha real: ruta absoluta, no notación de storage.** Con `--script local:snippets/oscar-led-vzdump-hook.sh`, `vzdump` falló con `The hook script ... does not exist` aunque el archivo existía y `pvesh set` había aceptado el valor sin quejarse. La ruta absoluta funcionó tanto con el CLI `vzdump` como con `pvesh create /nodes/oscar-core/vzdump` (la misma API que usa el scheduler).

**Validado con corridas reales de `vzdump`** (VM `apps`, 39,5 GiB, ~40 s, vía `pvesh create /nodes/oscar-core/vzdump`): la tira quedó en `backup` durante todo el backup (observado cada 3 s) y volvió a `healthy` sola al terminar. **Pendiente de confirmar:** la primera corrida programada de verdad (lunes a las 00:00) — se probó por la misma API que usa el scheduler, pero no se observó todavía disparada por `pvescheduler`.

## Comandos de referencia (vzdump)

Backup manual de una VM/LXC puntual, fuera del job programado, en modo `snapshot` (no detiene el guest):

```bash
# backup de una sola VM/LXC (reemplazar <VMID> por el real, ej. 102 = core)
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

### Registro de pruebas

| Fecha | Qué se restauró | Resultado | Tiempos |
|---|---|---|---|
| 2026-10-15 | VM 105 `lab`, backup del 15/10 00:19 (81 GB comprimido, disco de 109 GB) como VM 905 en `local-lvm` | ✅ Arrancó, sistema `running` sin servicios fallidos, datos presentes (`/srv/oscar/apps`), agente QEMU respondiendo | Restauración 14,5 min · arranque 19 s · total ~15 min |

Cómo se hizo, sin chocar con producción:

```bash
qmrestore /mnt/pve/Backups/dump/vzdump-qemu-105-<fecha>.vma.zst 905 --storage local-lvm --unique 1
qm set 905 --name restore-drill-lab --onboot 0 --net0 "<net0 actual>,link_down=1"   # red desconectada
qm start 905 && qm agent 905 ping
qm guest exec 905 -- sh -c 'systemctl is-system-running; systemctl --failed'
qm stop 905 && qm destroy 905 --purge 1 --destroy-unreferenced-disks 1
```

`--unique` regenera la MAC y `link_down=1` evita que la copia tome la IP de la original (la configuración de cloud-init se restaura igual). Referencia para estimar: ~95 MB/s leyendo del disco de backups, así que una VM de 80 GB comprimidos tarda unos 15 minutos.

