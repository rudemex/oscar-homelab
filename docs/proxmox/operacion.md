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
pvesh get /nodes/oscar-core/status   # CPU/RAM/uptime del nodo vía API local
```

- verificar versión/kernel;
- revisar errores del sistema;
- comprobar bridges;
- iniciar/validar VMs;
- revisar métricas.

## Autostart de VMs (`onboot`)

**Estado:** las 4 VMs (`haos-18.2`, `core01`, `k3s01`, `devops01`) tienen `onboot: 1`.

Encontrado (2026-09-15): solo `haos-18.2` (Home Assistant) tenía `onboot: 1` seteado. `core01`, `k3s01` y `devops01` no tenían el flag — por default en Proxmox eso es `0` (apagado). Adentro de esas VMs todo estaba bien configurado para autorecuperarse (`docker`/`k3s` habilitados como servicio systemd, contenedores con `restart: unless-stopped`), pero eso no importa si la VM en sí nunca prende: tras un reinicio del host `oscar-core` (corte de luz, reinicio manual, update de kernel), las tres VMs principales se quedaban apagadas hasta encenderlas a mano.

Verificar/corregir:

```bash
qm config <vmid> | grep onboot    # (unset) = no arranca solo
qm set <vmid> --onboot 1
```

No confundir con el orden de arranque (`qm set <vmid> --startup order=X`) — con 3 VMs en el mismo host y sin dependencia dura de boot entre ellas (k3s no depende de que devops01 esté arriba para *arrancar*, solo para pullear imágenes de Nexus en runtime), no hizo falta definir orden, solo que las tres tengan el flag en `1`.

## Nunca

- instalar stacks de aplicación directamente en el host "porque es más rápido";
- usar Proxmox como workstation;
- llenar el datastore sin alertas;
- reiniciar sin saber qué workloads dependen de él.
