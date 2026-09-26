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

**Estado:** las 4 VMs (`haos-18.2`, `core`, `k3s`, `devops`) tienen `onboot: 1`.

Encontrado (2026-09-15): solo `haos-18.2` (Home Assistant) tenía `onboot: 1` seteado. `core`, `k3s` y `devops` no tenían el flag — por default en Proxmox eso es `0` (apagado). Adentro de esas VMs todo estaba bien configurado para autorecuperarse (`docker`/`k3s` habilitados como servicio systemd, contenedores con `restart: unless-stopped`), pero eso no importa si la VM en sí nunca prende: tras un reinicio del host `oscar-core` (corte de luz, reinicio manual, update de kernel), las tres VMs principales se quedaban apagadas hasta encenderlas a mano.

Verificar/corregir:

```bash
qm config <vmid> | grep onboot    # (unset) = no arranca solo
qm set <vmid> --onboot 1
```

No confundir con el orden de arranque (`qm set <vmid> --startup order=X`) — con 3 VMs en el mismo host y sin dependencia dura de boot entre ellas (k3s no depende de que devops esté arriba para *arrancar*, solo para pullear imágenes de Nexus en runtime), no hizo falta definir orden, solo que las tres tengan el flag en `1`.

## Servicios y scripts propios del host (2026-09-25)

Todo esto corre **en el host** `oscar-core` (no en una VM), versionado en `oscar-compose/hosts/oscar-core/`, y existe para reflejar el estado real en la [tira LED](../hardware/led-status.md):

| Pieza | Qué hace |
|---|---|
| `oscar-led-boot.service` | al bootear el Dell, `booting` cuando la tira responde (detalle abajo) |
| `oscar-led-night.timer` / `oscar-led-day.timer` | 23:00 `healthy` → `night`, 07:00 `night` → `healthy` (hora del host, `America/Argentina/Buenos_Aires`); solo entre esos dos estados, nunca pisa `critical`/`backup`/`maintenance` ni un modo a mano |
| `/usr/local/sbin/oscar-maintenance` | envuelve un comando con `maintenance` → `healthy` (también con error o Ctrl-C; no pisa un estado cambiado por otro; propaga el código de salida). Uso: `oscar-maintenance apt-get -y dist-upgrade`, `oscar-maintenance ansible-playbook site.yml`, o `start`/`end` a mano para trabajo físico en el rack |
| hookscript de `vzdump` | `backup` durante el job de backup, ver [Backups](./backups.md) |

Mientras la tira está en `maintenance`, `kuma-led-bridge` y `monitor01-watchdog` no levantan `critical`. Para cambiar los horarios de `night`, editar `OnCalendar=` en `/etc/systemd/system/oscar-led-{night,day}.timer` y `systemctl daemon-reload`. Limitación conocida: si de noche hay un incidente y se resuelve, el bridge de Kuma devuelve la tira a `healthy` (no a `night`) hasta el siguiente cambio de horario.

### `oscar-led-boot.service`

`oscar-led-boot.service`, habilitado en `multi-user.target`. Refleja el arranque del Dell en la [tira LED](../hardware/led-status.md) — espera (hasta 20 min, cada 10 s) a que la API de la tira responda, reproduce `booting` y, si nadie tomó la tira mientras tanto, la asienta en `healthy`. Vive en el host y no en k3s porque el `oscar-led-controller` corre adentro de k3s, que arranca *después* del host: no puede avisar de su propio arranque. Script en `/usr/local/sbin/oscar-led-boot.sh`, unidad en `/etc/systemd/system/`, ambos versionados en `oscar-compose/hosts/oscar-core/`. `Type=simple` a propósito: un `oneshot` bloquearía `multi-user.target` durante toda la espera.

Si en algún momento un reinicio del host demora de más en dar el "listo", esta unidad **no** es la causa (corre en paralelo, no bloquea nada) — se puede ver con `journalctl -u oscar-led-boot.service`.

## Nunca

- instalar stacks de aplicación directamente en el host "porque es más rápido";
- usar Proxmox como workstation;
- llenar el datastore sin alertas;
- reiniciar sin saber qué workloads dependen de él.
