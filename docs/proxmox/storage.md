---
title: Storage en Proxmox
sidebar_position: 2
---

# Storage de Proxmox

## Objetivo inicial

Aprovechar los discos existentes sin convertir el diseño temprano en una migración compleja.

Una distribución de referencia:

```text
M.2 1 TB
├── Proxmox
└── VM disks sensibles a I/O

SATA SSD 1 TB
├── volúmenes de datos
├── artefactos
└── staging de backups
```

El backup definitivo no debe vivir únicamente en otro directorio del mismo host.

**Estado real (actualizado 2026-10-15):**

```text
nvme0n1 (M.2, 931.5G, Kingston SNV3S1000G)            interno
├── EFI + boot
└── LVM-thin "pve-data" → storage local-lvm (discos de todas las VMs)

sda (SATA SSD, 1.8T, SanDisk SSD PLUS 2TB)            interno
└── /mnt/pve/Backups → storage "Backups" (job de vzdump, ver backups.md)

sdc (WD Green SATA SSD 1TB, por USB)                  externo
└── /mnt/storage (label BackupsCopia) → segunda copia de los backups, diaria 04:00

sdb (SanDisk SSD PLUS 1TB, por USB)                   externo
└── /mnt/documentos (label Documentos) → reservado para documentos, vacío
```

El SSD SATA de 1 TB original (`FTM1TN325H`) se retiró el 2026-10-13. Los externos se montan por UUID con `nofail` y tienen reglas udev en `/etc/udev/rules.d/99-oscar-external-disks.rules`. Salud, temperatura y alertas de cada disco: ProxMenux Monitor, el panel `#estado` de Discord y `oscar_disks_status` de Hermes.

Storage `Backups` real, agregado así (no `sata-data`/`/mnt/sata-ssd` como decía el ejemplo antes — esos nombres no existen, quedaron como referencia genérica sin actualizar contra lo que se armó):

```bash
pvesm add dir Backups --path /mnt/pve/Backups --content backup
```

## `local` vs `local-lvm`

La instalación estándar de Proxmox crea dos storages sobre el mismo disco de sistema, y es importante no confundirlos:

- **`local`** (tipo *Directory*, `/var/lib/vz`): guarda ISOs, plantillas de contenedor (CT templates), snippets y backups. No aloja discos de VM en uso normal.
- **`local-lvm`** (tipo *LVM-thin*): aloja los discos virtuales de VMs y LXC. Es thin-provisioned — ver [thin provisioning](#thin-provisioning) más abajo.

Ver el estado real con:

```bash
pvesm status
pvesm list local-lvm
```

Para el M.2 (rápido, sensible a I/O) y el SATA SSD (datos/artefactos) descriptos abajo, la práctica es agregar el SATA como un storage adicional en vez de expandir `local-lvm` sobre ambos discos — así una VM puede elegir explícitamente en qué disco físico vive:

```bash
pvesm add dir sata-data --path /mnt/sata-ssd --content images,backup
```

## Qué medir

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
smartctl -a /dev/<disk>
```

También observar en Proxmox:

- uso de datastore;
- I/O delay;
- latencia bajo backup;
- crecimiento mensual.

## Thin provisioning

Permite asignar discos virtuales mayores que el espacio consumido real, pero obliga a monitorear capacidad. Un datastore lleno puede causar fallas en múltiples VMs al mismo tiempo.

## Datos grandes

Nexus, Loki, métricas y backups crecen rápido. Definir políticas de retención antes de que el disco llegue al 95%.

## NAS futuro

Cuando exista NAS, evaluar:

- datastore de backups;
- NFS/SMB para datos compartidos;
- Proxmox Backup Server;
- snapshots del NAS como capa adicional.

No usar un NAS como excusa para eliminar backups off-site.
