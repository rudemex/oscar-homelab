---
title: PiNode01
sidebar_position: 4
---

# PiNode01 (Raspberry Pi 3)

**Estado:** Actual — en línea desde 2026-09-21
**Rol:** nodo de red y observabilidad fuera del Dell (el `network01` del [plan de infraestructura](../arquitectura/estado-actual.md))
**Acceso:** `ssh pi@192.168.0.213` (clave pública cargada; credenciales en Vaultwarden, ítem "PiNode01 (Raspberry Pi 3) — SSH")

## Por qué existe

Casi toda la resiliencia de O.S.C.A.R. vive en un solo Dell (`oscar-core`): si cae, se van a la vez el acceso remoto, el DNS y el monitoreo, justo cuando más hacen falta. PiNode01 saca de ahí las piezas críticas y livianas para que sobrevivan a una caída del Dell.

## Hardware

| Dato | Valor |
|---|---|
| Modelo | Raspberry Pi 3 Model B Rev 1.2 (1 GB de RAM, ARM64) |
| Almacenamiento | microSD de 64 GB (58,3 GB usables), 11 % usado |
| Red | Ethernet `eth0` — `192.168.0.213` por DHCP, MAC `b8:27:eb:5b:1f:30`. Wi-Fi (`wlan0`) apagado a propósito |
| Alimentación | sin avisos de bajo voltaje (`throttled=0x0`) |
| Sistema | Raspberry Pi OS (Debian 13 "trixie", 64 bits), kernel 6.18.50 |
| Arranque | modo consola (sin escritorio) — ver [decisiones](#decisiones-y-por-qué) |

## Servicios

| Servicio | Estado | Detalle |
|---|---|---|
| SSH | Activo | solo por red; clave `id_rsa` de la Mac cargada. Sigue aceptando contraseña (ver [pendientes](#pendientes)) |
| Tailscale `1.102.4` | Activo | **subnet router** de `192.168.0.0/24` (anunciada y aprobada), `--accept-dns=false`. IP de tailnet `100.102.205.119`. Repositorio oficial de apt, no `curl \| sh` |
| `node_exporter` | Activo | métricas en el puerto `9100` (1640 series), listo para que Prometheus las levante |
| `avahi-daemon` | Activo | mDNS: `pinode01.local` |
| `rpcbind` | Activo (sin uso) | puerto `111` abierto sin necesidad real — candidato a deshabilitar |

Puertos escuchando hoy: `22` (SSH), `9100` (`node_exporter`), `111` (`rpcbind`).

### Tailscale: rol dentro del acceso remoto

PiNode01 es hoy el subnet router **principal**; `core01` quedó como respaldo con la misma ruta aprobada. Detalle y limitaciones en [acceso remoto](../red/acceso-remoto.md).

## Decisiones y por qué

- **Nombre `pinode01`, en minúsculas.** Coherente con `core01`/`k3s01`/`devops01`. El hostname está protegido con `preserve_hostname: true` en `/etc/cloud/cloud.cfg.d/99-pinode-hostname.cfg`: sin eso `cloud-init` lo volvía a `Pi3` (el valor del `user-data` original) en cada arranque.
- **Sin escritorio.** La imagen vino con escritorio; se pasó a `multi-user.target` para liberar RAM (de ~520 MB a ~720 MB disponibles). Volver: `sudo systemctl set-default graphical.target && sudo reboot`.
- **VNC apagado.** La imagen trae `wayvnc` habilitado y escuchando en el `5900` hacia toda la LAN; en un nodo de DNS y VPN es control remoto abierto sin necesidad. También se deshabilitaron `bluetooth` y `packagekit`.
- **Sin kiosco.** Se probó Homepage a pantalla completa (`cage` + Chromium): funcionó, pero come ~350 MB de una Pi de 1 GB, casi lo mismo que queda libre para AdGuard y Tailscale. Se desinstaló y la pantalla táctil se conecta al Dell.
- **Tailscale por repositorio apt firmado** en vez del script de instalación, para tener actualizaciones con `apt`.

## Incidentes del alta (2026-09-21)

- **`cmdline.txt` vacío en la SD.** Sacar la tarjeta en la Mac sin expulsarla corrompió la FAT: `cmdline.txt` quedó en 0 bytes y la Pi no podía arrancar. El contenido original se recuperó de `FSCK0000.REC` (el fragmento que deja la reparación) y se restauró. **Lección:** expulsar siempre la tarjeta desde el Finder. Si se repite, la línea original es `console=serial0,115200 console=tty1 root=PARTUUID=<el de la tarjeta> rootfstype=ext4 fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles ds=nocloud;i=<id> cfg80211.ieee80211_regdom=AR`.
- **SSH no arrancó en el primer boot** aunque el Imager lo pedía (`runcmd: systemctl enable --now ssh`): hubo que habilitarlo a mano desde la consola.
- **"HDCP disabled" en la pantalla.** Es un aviso informativo del display (la Pi 3 no soporta HDCP); indica que el HDMI sí llega. No es un error ni requiere configuración. En cambio, con el driver KMS (`vc4-kms-v3d`) las líneas `hdmi_group`/`hdmi_mode` de `config.txt` se ignoran — la resolución se fuerza con `video=` en `cmdline.txt` si hiciera falta.
- **Touch de la DeskPi 9" no estable.** La Pi lo detectó como `ILITEK-TOUCH` (`222a:0001`, driver `hid_multitouch` presente) pero el enlace USB se reseteaba en bucle y terminó desconectado. Se movió la pantalla al Dell en vez de seguir depurando el cable. Pistas si se retoma: alimentar la pantalla por su Type-C2 con cargador propio (consume hasta 2 A, más de lo que reparte el USB de la Pi 3), cable de datos, y probar sin el teclado en el mismo bus.

## Pendientes

- [ ] **Rotar la contraseña de `pi`**: la actual se reusa en otros servicios y quedó escrita en una conversación. Después, `PasswordAuthentication no` en SSH (solo clave).
- [ ] **IP fija o reserva DHCP para `192.168.0.213`.** Hoy es dinámica; un nodo de DNS/VPN no debe cambiar de dirección (mismo problema que ya hubo con el LXC de AdGuard).
- [ ] **Confirmar el cableado**: el plan lo quiere directo a un puerto del router (no detrás del switch de OSCAR) para sobrevivir a una falla del switch. Hoy no está verificado.
- [ ] **Probar el respaldo de Tailscale**: bajar `tailscaled` un momento en la Pi y confirmar desde el celular con datos móviles que la LAN sigue alcanzable por `core01`.
- [ ] **AdGuard Home** como DNS primario (el del Dell pasa a secundario); el cambio en el DHCP del router va aparte y con backup. Ver [DNS con AdGuard Home](../red/dns-adguard.md).
- [ ] **Uptime Kuma**: migrar con su historial (volumen `/app/data`), no recrearlo.
- [ ] Deshabilitar `rpcbind` (sin uso).
- [ ] Enrolar a Prometheus como target (`pinode01:9100`) cuando exista.
