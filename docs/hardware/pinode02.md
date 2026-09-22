---
title: PiNode02
sidebar_position: 5
---

# PiNode02 (Raspberry Pi 3)

**Estado:** Actual — en línea desde 2026-09-21
**Rol:** `monitor01` del [plan de infraestructura](../arquitectura/estado-actual.md): observabilidad de todo O.S.C.A.R. (Prometheus + Grafana + Blackbox Exporter), basado en el enfoque de [Internet-Pi](https://github.com/geerlingguy/internet-pi)
**Acceso:** `ssh pi@192.168.0.214` (clave pública cargada; credenciales en Vaultwarden)

## Por qué existe

Hasta que se instaló, O.S.C.A.R. no tenía ninguna observabilidad con historial: Homepage y Uptime Kuma muestran el estado actual, pero no hay forma de ver cómo evolucionó la CPU, la RAM o la latencia de un servicio a lo largo del tiempo. PiNode02 llena ese hueco sin depender del Dell.

## Hardware

| Dato | Valor |
|---|---|
| Modelo | Raspberry Pi 3 Model B Rev 1.2 (1 GB de RAM, ARM64) |
| Red | Ethernet `eth0` — `192.168.0.214/24` **fija** (cloud-init, `network-config`), MAC `b8:27:eb:be:27:a9` |
| DNS | `192.168.0.213` (AdGuard de `pinode01`) y `1.1.1.1` |
| Sistema | Raspberry Pi OS (Debian 13 "trixie", 64 bits) |
| Arranque | modo consola (sin escritorio), igual que `pinode01` |

## Servicios

| Servicio | Estado | Detalle |
|---|---|---|
| **Prometheus** `v2.55.1` | Activo | `http://192.168.0.214:9090`, retención 15 días. Scrapea `node_exporter` de toda la flota y los chequeos de Blackbox |
| **Grafana** `11.3.1` | Activo | `http://192.168.0.214:3006` (puerto 3006, no 3000: ese lo usa Forgejo en otra VM). Usuario `admin`, contraseña en Vaultwarden. Dashboard provisto: *OSCAR — Infraestructura* |
| **Blackbox Exporter** `v0.25.0` | Activo | `http://192.168.0.214:9115`, chequea HTTP de Homepage, Forgejo, Nexus, AdGuard y el propio `node_exporter` |
| `node_exporter` | Activo | métricas propias en el puerto `9100` |
| Docker `26` + plugin `compose` v2 | Activo | el plugin es el binario oficial de GitHub (checksum verificado); no está en los repos de Debian, y se evitó a propósito agregar el repositorio de Docker |

Puertos escuchando: `22` (SSH), `9090` (Prometheus), `9100` (`node_exporter`), `9115` (Blackbox), `3006` (Grafana).

## Qué mide Prometheus hoy

| Job | Objetivos |
|---|---|
| `node_exporter` | `pinode01`, `pinode02`, `core01`, `devops01`, `k3s01` — CPU, RAM, disco |
| `blackbox_http` | Homepage, Forgejo, Nexus, AdGuard (`pinode01`), el propio `node_exporter` de `pinode02` |

Lista corta a propósito: se amplía cuando el primer dashboard esté validado en el uso real.

## Decisiones y por qué

- **Ansible como control node (2026-09-21).** No existía en el proyecto. Vive en `oscar-gitops/ansible/`: inventario (`pis`, `docker_hosts`, `k3s`, `monitor01`), roles `common`/`node_exporter`/`docker`/`monitoring_stack`, corrido desde esta Mac (no hay un host dedicado todavía). Las contraseñas (`sudo` de las Pi, admin de Grafana) están cifradas con `ansible-vault`, nunca en texto plano en el repo.
- **`docker compose` v2 por binario oficial, no por repo de Docker.** El paquete `docker-compose-plugin` no existe en los repos de Debian trixie (solo Docker.io lo publica en su propio repo, que se evita a propósito en todo el proyecto). Se instala el binario firmado de GitHub como CLI plugin, con checksum verificado en cada corrida.
- **Puerto 3006 para Grafana**, no el 3000 por defecto, para no confundirlo con Forgejo (que usa 3000 en `devops01`, otra VM, pero mismo rango de puertos "conocidos").
- **Gotcha real (2026-09-21): `blackbox-exporter:9115`, no `localhost:9115`.** El primer despliegue de la config de Prometheus decía `replacement: localhost:9115` en el `relabel_config` de Blackbox — dentro de Docker Compose, `localhost` es el propio contenedor de Prometheus, no el de Blackbox. El síntoma fue confuso: el campo `health` de la API de Prometheus decía "up" para esos objetivos (porque medía si el scrape a Blackbox funcionaba, no si el sitio de destino respondía) mientras la métrica real `probe_success` daba `0`. Se corrigió usando el nombre del servicio de Compose.
- **Retención corta (15 días) y una lista corta de objetivos**, mismo criterio que en el resto del proyecto: no self-hostear de más "por si acaso".

## Incidente relacionado (no de esta Pi)

El 2026-09-21/22 el Dell (`oscar-core`) tuvo un cuelgue completo de red (no solo la NIC — ni ARP respondía) durante varias horas. **PiNode02 siguió funcionando sin interrupción**: Prometheus, Grafana y Blackbox no dependen del Dell para correr, aunque sus objetivos ahí (`core01`, `devops01`, `k3s01`, Homepage, Forgejo, Nexus) lógicamente aparecieron caídos en los dashboards durante ese lapso — es la prueba en vivo de por qué vale la pena tener observabilidad fuera del Dell.

## Pendientes

- [ ] Sumar el exporter de Proxmox (`oscar-core`) a Prometheus.
- [ ] Dashboards adicionales (Network, Kubernetes, Home, Services) una vez validado el primero en el uso real.
- [ ] Reserva DHCP en el router para `192.168.0.214` (mismo pendiente que `pinode01`).
- [ ] Documentar el control node de Ansible en su propia página, si crece más allá de este stack.
