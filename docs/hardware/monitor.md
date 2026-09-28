---
title: monitor
sidebar_position: 5
---

# monitor (Raspberry Pi 3)

**Estado:** Actual — en línea desde 2026-09-21. **Renombrada de `pinode02` a `monitor` el 2026-09-22** (ver
`REORGANIZACION_RACK.md`, raíz del repo) — mismo hardware, mismo rol, solo cambió el
nombre. A diferencia de [`network`](./network.md), esta Pi **no tenía** la protección `preserve_hostname` de
cloud-init contra el rename; se agregó en el mismo momento (`/etc/cloud/cloud.cfg.d/99-pinode-hostname.cfg`).
**Rol:** observabilidad de todo O.S.C.A.R. (Prometheus + Grafana + Blackbox Exporter), basado en el enfoque de [Internet-Pi](https://github.com/geerlingguy/internet-pi)
**Acceso:** `ssh pi@192.168.0.214` (clave pública cargada; credenciales en Vaultwarden)

## Por qué existe

Hasta que se instaló, O.S.C.A.R. no tenía ninguna observabilidad con historial: Homepage y Uptime Kuma muestran el estado actual, pero no hay forma de ver cómo evolucionó la CPU, la RAM o la latencia de un servicio a lo largo del tiempo. `monitor` llena ese hueco sin depender del Dell.

## Hardware

| Dato | Valor |
|---|---|
| Modelo | Raspberry Pi 3 Model B Rev 1.2 (1 GB de RAM, ARM64) |
| Red | Ethernet `eth0` — `192.168.0.214/24` **fija** (cloud-init, `network-config`), MAC `b8:27:eb:be:27:a9` |
| DNS | `192.168.0.213` (AdGuard de `network`) y `1.1.1.1` |
| Sistema | Raspberry Pi OS (Debian 13 "trixie", 64 bits) |
| Arranque | modo consola (sin escritorio), igual que `network` |

## Servicios

| Servicio | Estado | Detalle |
|---|---|---|
| **Prometheus** `v2.55.1` | Activo | `http://192.168.0.214:9090`, retención 15 días. Scrapea `node_exporter` de toda la flota y los chequeos de Blackbox |
| **Grafana** `11.3.1` | Activo | `http://192.168.0.214:3006` (puerto 3006, no 3000: ese lo usa Forgejo en otra VM). Usuario `admin`, contraseña en Vaultwarden. Dashboard provisto: *OSCAR — Infraestructura* |
| **Blackbox Exporter** `v0.25.0` | Activo | `http://192.168.0.214:9115`, chequea HTTP de Homepage, Forgejo, Nexus, AdGuard y el propio `node_exporter`. Módulo ICMP (monitor de Internet) desplegado el 2026-09-28 |
| `node_exporter` | Activo | métricas propias en el puerto `9100` |
| Docker `26` + plugin `compose` v2 | Activo | el plugin es el binario oficial de GitHub (checksum verificado); no está en los repos de Debian, y se evitó a propósito agregar el repositorio de Docker |
| **Uptime Kuma** `2.5.4` | Activo (2026-09-22) | migró desde [`network`](./network.md) — 21 monitores + historial, ver [migración](../servicios/uptime-kuma.md#migración-a-monitor-2026-09-22). UI `:3001` |

Puertos escuchando: `22` (SSH), `9090` (Prometheus), `9100` (`node_exporter`), `9115` (Blackbox), `3006` (Grafana), `3001` (Uptime Kuma).

## Qué mide Prometheus hoy

| Job | Objetivos |
|---|---|
| `node_exporter` | `network`, `monitor`, `core`, `devops`, `k3s` — CPU, RAM, disco |
| `blackbox_http` | Homepage, Forgejo, Nexus, AdGuard (`network`), el propio `node_exporter` de `monitor` |
| `blackbox_icmp` | `1.1.1.1`/`8.8.8.8` — monitor de Internet, dos resolutores distintos para que la caída de uno solo no se lea como "se cayó Internet" |
| `speedtest` | exporter en `core` (ver nota abajo), scrapeado cada 30 min — una medición real de ancho de banda no tiene sentido pedirla más seguido |
| `pve` | `prometheus-pve-exporter` en el propio hipervisor `oscar-core` (`192.168.0.233:9221`, fuera de este inventario de Ansible — Proxmox no tiene Docker, se instaló vía `pipx` + `systemd` directo por SSH). Token de API dedicado (`root@pam!pve-exporter`, rol `PVEAuditor`, solo lectura), no reutiliza el token `homepage` existente |

Todos desplegados el 2026-09-28, junto con el dashboard *OSCAR — Proxmox* y dos paneles de Speedtest sumados a *OSCAR — Infraestructura* (descarga/subida y ping/jitter). El job `pve` usa el mismo patrón multi-target que `blackbox_http`/`blackbox_icmp`: `__address__` apunta al exporter, el nodo real a consultar viaja como query param (`cluster=1&node=1`).

**Por qué el throughput de Internet no se mide desde esta Pi:** la Pi 3 tiene Ethernet limitado a ~100Mbps (comparte bus con USB 2.0). El internet real de OSCAR es 600Mb simétrico — medir desde acá reportaría un techo falso. El Speedtest exporter corre en `core` (NIC gigabit); esta Pi solo grafica el dato.

## Decisiones y por qué

- **Ansible como control node (2026-09-21).** No existía en el proyecto. Vive en `oscar-gitops/ansible/`: inventario (`pis`, `docker_hosts`, `k3s`), roles `common`/`node_exporter`/`docker`/`monitoring_stack`, corrido desde esta Mac (no hay un host dedicado todavía). Las contraseñas (`sudo` de las Pi, admin de Grafana) están cifradas con `ansible-vault`, nunca en texto plano en el repo. **Actualizado 2026-09-22:** el grupo de rol `monitor01` (alias de esta Pi) se eliminó del inventario — con el hostname físico ya llamándose `monitor`, la variable de vault pasó de `group_vars/monitor01/` a `host_vars/monitor/`, autocargada sin grupo intermedio.
- **`docker compose` v2 por binario oficial, no por repo de Docker.** El paquete `docker-compose-plugin` no existe en los repos de Debian trixie (solo Docker.io lo publica en su propio repo, que se evita a propósito en todo el proyecto). Se instala el binario firmado de GitHub como CLI plugin, con checksum verificado en cada corrida.
- **Puerto 3006 para Grafana**, no el 3000 por defecto, para no confundirlo con Forgejo (que usa 3000 en `devops`, otra VM, pero mismo rango de puertos "conocidos").
- **Gotcha real (2026-09-21): `blackbox-exporter:9115`, no `localhost:9115`.** El primer despliegue de la config de Prometheus decía `replacement: localhost:9115` en el `relabel_config` de Blackbox — dentro de Docker Compose, `localhost` es el propio contenedor de Prometheus, no el de Blackbox. El síntoma fue confuso: el campo `health` de la API de Prometheus decía "up" para esos objetivos (porque medía si el scrape a Blackbox funcionaba, no si el sitio de destino respondía) mientras la métrica real `probe_success` daba `0`. Se corrigió usando el nombre del servicio de Compose.
- **Retención corta (15 días) y una lista corta de objetivos**, mismo criterio que en el resto del proyecto: no self-hostear de más "por si acaso".
- **`prometheus-pve-exporter` fuera de Ansible, directo por SSH (2026-09-28).** Corre en el propio hipervisor `oscar-core`, que no tiene Docker y no está en el inventario de Ansible (es bare-metal Proxmox, no una VM/Pi gestionada). Se instaló vía `apt install pipx` + `pipx install prometheus-pve-exporter` (venv aislada, sin pelearse con el Python del sistema) y un `systemd` unit propio (`prometheus-pve-exporter.service`, puerto `9221`), mismo patrón que los otros servicios del host (`oscar-poweroff.service`, `oscar-led-boot.service`). El rol `speedtest_exporter` nuevo de Ansible (`core`, que sí está en el inventario vía el grupo `speedtest_host`) y el resto de `monitoring_stack` (acá, en `monitor`) sí se aplicaron por Ansible normalmente.
- **Token de API dedicado para el exporter de Proxmox**, no el token `homepage` que ya usa el widget de Homepage. `root@pam!pve-exporter`, rol `PVEAuditor` (Datastore/Mapping/Pool/SDN/Sys/VM Audit — todo de solo lectura), ACL en `/`. Un token por consumidor, mismo criterio ya establecido para el token `homepage`.

## Incidente relacionado (no de esta Pi)

El 2026-09-21/22 el Dell (`oscar-core`) tuvo un cuelgue completo de red (no solo la NIC — ni ARP respondía) durante varias horas. **Esta Pi siguió funcionando sin interrupción**: Prometheus, Grafana y Blackbox no dependen del Dell para correr, aunque sus objetivos ahí (`core`, `devops`, `k3s`, Homepage, Forgejo, Nexus) lógicamente aparecieron caídos en los dashboards durante ese lapso — es la prueba en vivo de por qué vale la pena tener observabilidad fuera del Dell.

## Pendientes

- [x] **Sumar el exporter de Proxmox (`oscar-core`) a Prometheus** (2026-09-28).
- [x] **Desplegar el Speedtest exporter en `core` y Blackbox ICMP acá** (2026-09-28).
- [x] **Uptime Kuma migrado desde `network`** (2026-09-22).
- [ ] Dashboards adicionales (Network, Kubernetes, Home, Services) una vez validado el primero en el uso real.
- [ ] Con Beszel/ProxMenux Monitor/MySpeed ya comparables en Grafana (dashboards *Infraestructura* y *Proxmox*), decidir con el usuario, herramienta por herramienta, cuál se retira — ver [REORGANIZACION_RACK.md](https://github.com/rudemex/oscar-homelab/blob/develop/REORGANIZACION_RACK.md), sección "Observabilidad". Conviene dejar pasar un tiempo real corriendo en paralelo antes de decidir, no comparar el mismo día del despliegue.
- [ ] Reserva DHCP en el router para `192.168.0.214` (mismo pendiente que `network`).
- [ ] Documentar el control node de Ansible en su propia página, si crece más allá de este stack.
