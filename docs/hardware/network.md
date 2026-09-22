---
title: network
sidebar_position: 4
---

# network (Raspberry Pi 3)

**Estado:** Actual — en línea desde 2026-09-21. **Renombrada de `pinode01` a `network` el 2026-09-22** (ver
`REORGANIZACION_RACK.md`, raíz del repo) — mismo hardware, mismo rol, solo cambió el
nombre.
**Rol:** nodo de red y observabilidad fuera del Dell (host `network` del [plan de infraestructura](../arquitectura/estado-actual.md))
**Acceso:** `ssh pi@192.168.0.213` (clave pública cargada; credenciales en Vaultwarden, ítem "network (Raspberry Pi 3) — SSH", antes "PiNode01")

## Por qué existe

Casi toda la resiliencia de O.S.C.A.R. vive en un solo Dell (`oscar-core`): si cae, se van a la vez el acceso remoto, el DNS y el monitoreo, justo cuando más hacen falta. `network` saca de ahí las piezas críticas y livianas para que sobrevivan a una caída del Dell.

## Hardware

| Dato | Valor |
|---|---|
| Modelo | Raspberry Pi 3 Model B Rev 1.2 (1 GB de RAM, ARM64) |
| Almacenamiento | microSD de 64 GB (58,3 GB usables), 11 % usado |
| Red | Ethernet `eth0` — `192.168.0.213/24` **fija** (NetworkManager, método `manual`; gateway `192.168.0.1`, DNS `192.168.0.213` (su propio AdGuard) y `1.1.1.1`), MAC `b8:27:eb:5b:1f:30`. Hoy conectada al **switch** de OSCAR, no directo al router. Wi-Fi (`wlan0`) apagado a propósito |
| Alimentación | sin avisos de bajo voltaje (`throttled=0x0`) |
| Sistema | Raspberry Pi OS (Debian 13 "trixie", 64 bits), kernel 6.18.50 |
| Arranque | modo consola (sin escritorio) — ver [decisiones](#decisiones-y-por-qué) |

## Servicios

| Servicio | Estado | Detalle |
|---|---|---|
| SSH | Activo | solo por red; clave `id_rsa` de la Mac cargada. Sigue aceptando contraseña (ver [pendientes](#pendientes)) |
| Tailscale `1.102.4` | Activo | **subnet router** de `192.168.0.0/24` (anunciada y aprobada), `--accept-dns=false`. IP de tailnet `100.102.205.119`. Repositorio oficial de apt, no `curl \| sh` |
| `node_exporter` | Activo | métricas en el puerto `9100` (1640 series), listo para que Prometheus las levante |
| **AdGuard Home** `v0.107.79` | Activo | DNS en `192.168.0.213:53` y UI en `:3000`, ~68 MB de RAM. Config nueva (rate limit 300, rewrites de `*.oscar.home`). Detalle en [DNS con AdGuard Home](../red/dns-adguard.md#adguard-home-en-pinode01-2026-09-21). El router **no** lo reparte por DHCP todavía (decisión firme, ver `REORGANIZACION_RACK.md`) |
| **Uptime Kuma** `2.5.4` | ⚠️ Migra a [`monitor`](./monitor.md) | copia migrada de la de `core01` (21 monitores, historial), en Docker; UI `:3001`. Pasa a `monitor` como parte de la reorganización — ver [Uptime Kuma](../servicios/uptime-kuma.md#segunda-instancia-en-pinode01-2026-09-21) |
| `cloudflared` `2026.9.1` | Activo | conector de un **túnel propio**, en Docker con `network_mode: host`; token en `/srv/oscar/apps/cloudflared/.env` (`600`, no está en Git). Publica solo lo que vive en la Pi (`kuma.oscarlab.com.ar` → `localhost:3001`, hasta que Kuma migre a `monitor`). ~30 MB de RAM |
| Docker `26.1.5` + Compose `2.26.1` | Activo | solo para Kuma; usuario `pi` en el grupo `docker` |
| `avahi-daemon` | Activo | mDNS: `network.local` |
| `rpcbind` | Activo (sin uso) | puerto `111` abierto sin necesidad real — candidato a deshabilitar |

Puertos escuchando hoy: `22` (SSH), `53` (DNS, UDP/TCP), `3000` (UI de AdGuard), `3001` (Uptime Kuma, hasta que migre), `9100` (`node_exporter`), `111` (`rpcbind`).

RAM con todo corriendo: ~440 MB en uso y ~460 MB disponibles (incluye caché). Es el margen que queda; conviene no sumar mucho más a esta Pi 3.

### Tailscale: rol dentro del acceso remoto

`network` y `core01` anuncian la misma ruta y las dos están aprobadas; Tailscale usa una a la vez y conmuta si la activa cae, **sin volver sola** a la anterior. El respaldo se probó el 2026-09-21 (ver [acceso remoto](../red/acceso-remoto.md)); tras la prueba quedó activa `core01`. Detalle y limitaciones en [acceso remoto](../red/acceso-remoto.md).

## Decisiones y por qué

- **Nombre `network`, en minúsculas** (antes `pinode01`, renombrada 2026-09-22 — ver [convención de nombres](../referencia/naming.md)). El hostname está protegido con `preserve_hostname: true` en `/etc/cloud/cloud.cfg.d/99-pinode-hostname.cfg`: sin eso `cloud-init` lo revierte en cada arranque (esa protección ya existía desde el alta original, por eso el rename de 2026-09-22 no necesitó tocarla acá — sí hizo falta agregarla en `monitor`, que no la tenía).
- **Sin escritorio.** La imagen vino con escritorio; se pasó a `multi-user.target` para liberar RAM (de ~520 MB a ~720 MB disponibles). Volver: `sudo systemctl set-default graphical.target && sudo reboot`.
- **VNC apagado.** La imagen trae `wayvnc` habilitado y escuchando en el `5900` hacia toda la LAN; en un nodo de DNS y VPN es control remoto abierto sin necesidad. También se deshabilitaron `bluetooth` y `packagekit`.
- **Sin kiosco.** Se probó Homepage a pantalla completa (`cage` + Chromium): funcionó, pero come ~350 MB de una Pi de 1 GB, casi lo mismo que queda libre para AdGuard y Tailscale. Se desinstaló y la pantalla táctil se conecta al Dell.
- **Sin rotación de credenciales (decisión 2026-09-21).** La contraseña de `pi` y el token del túnel no se rotan aunque hayan quedado escritos en una conversación: se considera un entorno de red doméstica seguro. Queda anotado como decisión explícita, no como pendiente olvidado.
- **Tailscale por repositorio apt firmado** en vez del script de instalación, para tener actualizaciones con `apt`.

## Incidentes del alta (2026-09-21)

- **`cmdline.txt` vacío en la SD.** Sacar la tarjeta en la Mac sin expulsarla corrompió la FAT: `cmdline.txt` quedó en 0 bytes y la Pi no podía arrancar. El contenido original se recuperó de `FSCK0000.REC` (el fragmento que deja la reparación) y se restauró. **Lección:** expulsar siempre la tarjeta desde el Finder. Si se repite, la línea original es `console=serial0,115200 console=tty1 root=PARTUUID=<el de la tarjeta> rootfstype=ext4 fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles ds=nocloud;i=<id> cfg80211.ieee80211_regdom=AR`.
- **SSH no arrancó en el primer boot** aunque el Imager lo pedía (`runcmd: systemctl enable --now ssh`): hubo que habilitarlo a mano desde la consola.
- **"HDCP disabled" en la pantalla.** Es un aviso informativo del display (la Pi 3 no soporta HDCP); indica que el HDMI sí llega. No es un error ni requiere configuración. En cambio, con el driver KMS (`vc4-kms-v3d`) las líneas `hdmi_group`/`hdmi_mode` de `config.txt` se ignoran — la resolución se fuerza con `video=` en `cmdline.txt` si hiciera falta.
- **Touch de la DeskPi 9" no estable.** La Pi lo detectó como `ILITEK-TOUCH` (`222a:0001`, driver `hid_multitouch` presente) pero el enlace USB se reseteaba en bucle y terminó desconectado. Se movió la pantalla al Dell, donde tras cambiar el USB quedó estable: era un tema de **corriente** del puerto (ver [Dell 7060](./dell-7060.md#pantalla-táctil-con-homepage-2026-09-21)). Pistas si se retoma: alimentar la pantalla por su Type-C2 con cargador propio (consume hasta 2 A, más de lo que reparte el USB de la Pi 3), cable de datos, y probar sin el teclado en el mismo bus.

## Pendientes

- [ ] *(opcional)* SSH solo por clave: `PasswordAuthentication no`. Ya entra por clave desde la Mac; es endurecimiento, no urgente.
- [x] **IP fija** (2026-09-21): `192.168.0.213/24` configurada en la propia Pi con `nmcli` (mismo problema que ya hubo con el LXC de AdGuard, que usaba DHCP).
- [ ] **Reserva DHCP en el router** para la MAC `b8:27:eb:5b:1f:30` → `192.168.0.213`. La IP fija en la Pi no le avisa al router: si `.213` está dentro de su rango de reparto, podría entregársela a otro equipo y generar un conflicto.
- [ ] **Mover al router**: hoy está en el switch. El plan la quiere conectada **directo a un puerto del router** para sobrevivir también a una falla del switch de OSCAR. Se hace después, con la IP ya fija no cambia nada al mover el cable.
- [x] **Probar el respaldo de Tailscale** (2026-09-21): con `tailscale down` en la Pi la ruta pasó a `core01` y el celular con datos móviles siguió llegando a Homepage. Sin failback automático.
- [x] **AdGuard Home** instalado (2026-09-21), con config nueva.
- [ ] Repartirlo como DNS primario por DHCP del router — **decisión firme: no reactivar** (ver `REORGANIZACION_RACK.md`, sección "AdGuard"), aunque la causa raíz del incidente de velocidad ya está corregida. Sigue opt-in por dispositivo.
- [ ] Restaurar las listas de bloqueo del AdGuard viejo si se recupera el disco.
- [x] **Uptime Kuma** migrado con su historial (2026-09-21), en paralelo.
- [x] **Corte de Kuma a esta Pi** (2026-09-21, como `pinode01`): Homepage (widget y siteMonitor) repuntado, Kuma de `core01` detenido (volumen conservado como respaldo) y `kuma.oscarlab.com.ar` en un túnel propio de la Pi. Ver [Uptime Kuma](../servicios/uptime-kuma.md).
- [ ] **Migrar Uptime Kuma a `monitor`** (parte de la reorganización: una sola instancia de Kuma, vive en `monitor` junto al resto de la observabilidad) — exportar/importar su SQLite y repuntar el `cloudflared` dedicado.
- [ ] Deshabilitar `rpcbind` (sin uso).
- [x] Enrolar a Prometheus como target (`network:9100`, ya scrapeado desde `monitor`).
