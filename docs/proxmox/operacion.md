---
title: Operación y updates
sidebar_position: 6
---

# Operación de Proxmox

## Antes de actualizar

- revisar backups recientes;
- comprobar espacio libre;
- leer release notes si cambia versión mayor;
- registrar VMs críticas activas;
- evitar actualizar mientras corre un backup pesado.

## Rutina mensual

```bash
apt update
apt list --upgradable
apt full-upgrade
```

Después de actualizar:

```bash
pveversion                 # confirmar versión de Proxmox VE tras el upgrade
uname -r                   # confirmar kernel activo (puede requerir reboot si cambió)
journalctl -p err -b       # errores del boot actual
ip -br a show vmbr0        # bridge sigue arriba
qm list                    # estado de las VMs tras el reinicio, si hubo
pvesh get /nodes/pve01/status   # CPU/RAM/uptime del nodo vía API local
```

- verificar versión/kernel;
- revisar errores del sistema;
- comprobar bridges;
- iniciar/validar VMs;
- revisar métricas.

## Nunca

- instalar stacks de aplicación directamente en el host "porque es más rápido";
- usar Proxmox como workstation;
- llenar el datastore sin alertas;
- reiniciar sin saber qué workloads dependen de él.
