---
title: Estado actual
sidebar_position: 1
---

# Estado actual de O.S.C.A.R.

Esta página es la única fuente de "qué existe de verdad hoy". El resto del sitio describe mayormente **Objetivo** y **Laboratorio** — es fácil, leyendo la doc completa, terminar pensando que hay más construido de lo que realmente hay. Esta página existe para que esa brecha nunca quede implícita.

Se actualiza en cada cambio de fase real (ver [roadmap](../roadmap/roadmap-general.md)), no en cada edición de documentación.

:::caution
Proxmox ya está instalado, con **cuatro VMs/LXC** arriba (`core01`, `devops01`, `k3s01`, más el LXC de AdGuard) y Docker corriendo en tres de ellas. Hay un cluster **k3s con Argo CD** haciendo GitOps real desde Forgejo, y una docena y media de servicios reales entre Docker Compose y k3s — siete de ellos ya publicados en `oscarlab.com.ar` detrás de Cloudflare Access. Todo lo demás del sitio que dice "Objetivo" sigue sin existir — esta página es la línea exacta entre lo uno y lo otro.
:::

## Hardware — existe físicamente

| Componente | Estado | Nota |
|---|---|---|
| Rack GeeekPi RackMate T2 (10", 12U) | Actual | — |
| Dell OptiPlex 7060 Micro (i7 8ª gen, 32 GB RAM, NVMe 1 TB + SATA 1 TB) | Actual | RAM y M.2 ya ampliados (16→32 GB, 512 GB→1 TB). Corriendo Proxmox VE 9.2 como nodo `oscar-core`. |
| 2× Raspberry Pi 3, 3× Pi Zero W | Actual | Sin rol asignado todavía. |
| Router/mesh TP-Link Archer AX55 | Actual | Es el gateway hoy — no hay firewall dedicado. |
| Switch TP-Link TL-SF1008D (8p/100 Mbps) | Actual, marcado para reemplazo | Bloquea VLAN y gigabit real. |
| Patch panel CAT6 12p, pantalla táctil 9", paneles de gestión/ventilación | Actual | Montaje físico, sin uso funcional todavía. |
| UPS + estabilizador | Actual, **no integrado** | Existen pero están fuera del rack, sin conectar ni monitorear — ver [runbook de corte eléctrico](../runbooks/corte-electrico.md). |
| DVR Dahua 4 canales | Actual, **con IP en la LAN** | `192.168.0.224`, interfaz web accesible (HTTP redirige a HTTPS). Es hardware propio del autor, no un requisito de arquitectura. Sin bandeja física propia ni VLAN dedicada todavía — ver [CCTV](../hogar/cctv-dahua.md). |

## Software — corriendo hoy en `oscar-core`

| Componente | Tipo | Estado | Nota |
|---|---|---|---|
| Proxmox VE 9.2.18 | Hypervisor | Actual | Nodo único `oscar-core`, storage `local-lvm` (M.2) + `Backups` (SATA, dir storage). Sano: load bajo, sin swap, sin tareas fallidas. |
| Home Assistant OS 18.2 | VM (vmid 101) | Actual | 2 vCPU / 4 GB / 32 GB disco, instalada vía community-script. Ver [Home Assistant](../servicios/home-assistant.md). |
| AdGuard Home | LXC (vmid 100) | Actual | 2 vCPU / 1 GB (subido de 1 vCPU/512 MB el 2026-09-18, antes de pasarlo a DNS de toda la LAN — margen real, no ajuste forzado por un problema), instalada vía community-script. Reemplaza a Pi-hole — ver [DNS con AdGuard Home](../red/dns-adguard.md). IP estática `192.168.0.93/24` (corregido 2026-09-18, antes `ip=dhcp` — ver incidente abajo). `ratelimit: 300` (antes `20`, causa real del incidente de throughput). |
| `core01` — Ubuntu 24.04 LTS + Docker 29 | VM (vmid 102) | Actual | 2 vCPU / **8 GB** / 60 GB disco (subida de 4→8 GB, el uso real llegó a 91% con 9 contenedores), creada desde cloud image vía Cloud-Init (SSH por clave, sin password). IP estática `192.168.0.156/24` vía `ipconfig0` de Cloud-Init (no DHCP, pese a lo que decía esta página antes). DNS corregido recién (2026-09-16): tenía `8.8.8.8` fijo desde su creación, sin apuntar nunca a AdGuard — ningún contenedor del host podía resolver `*.oscar.home` hasta que Homepage lo necesitó por primera vez. Ahora `192.168.0.93` + `1.1.1.1` de fallback. Ver [crear VM core01](../proxmox/crear-vm-core01.md). |
| `devops01` — Ubuntu 24.04 LTS + Docker 29 | VM (vmid 104) | Actual | 4 vCPU / 8 GB / 60 GB disco, mismo patrón que `core01` (clon del template `9000`, IP estática `192.168.0.151/24` vía Cloud-Init). Corre Forgejo, Nexus y el CI Runner juntos. Ver [Forgejo / Git local](../servicios/forgejo.md). |
| `k3s01` — Ubuntu 24.04 LTS + k3s | VM (vmid 103) | Actual | IP estática `192.168.0.150/24`, mismo patrón de creación que `core01`/`devops01`. Un solo nodo (server+agent), sin HA todavía — eso sigue siendo Objetivo. Corre k3s (con Traefik como ingress controller, viene por defecto) y Argo CD. Ver [Kubernetes y GitOps](../kubernetes/vision-general.md). |
| Argo CD | k3s en `k3s01` | Actual | GitOps real: lee `oscar-gitops` desde Forgejo (`git.oscar.home`, no GitHub — ver la fila de `oscar-gitops` más abajo). Patrón app-of-apps (`root-app`, sync manual por diseño) con dos apps reales debajo: `oscar-led-controller` (namespace `oscar-lab`) y `ci-demo` (namespace `oscar-lab`, sync automático con self-heal). Publicado en `argocd.oscar.home` (Traefik, no NPM). |
| Todas las VMs/LXC | Proxmox | Actual | `onboot: 1` en las cuatro (`haos-18.2`, `core01`, `k3s01`, `devops01`) — encontrado y corregido recién: solo Home Assistant tenía el flag, las otras tres se quedaban apagadas tras un reinicio del host aunque Docker/k3s ya estuvieran bien configurados para autorecuperarse adentro. Ver [Operación de Proxmox](../proxmox/operacion.md#autostart-de-vms-onboot). |
| Forgejo 16.0.4 | Docker en `devops01` | Actual | `/srv/oscar/apps/forgejo/`, `http://git.oscar.home` (sin puerto — vía [Nginx Proxy Manager](../servicios/nginx-proxy-manager.md#proxy-hosts-reales) en `core01`, que proxea a `192.168.0.151:3000`) / SSH `2222`→22 interno, SQLite, auto-registro deshabilitado desde el arranque. Admin creado, credencial en Vaultwarden, monitor en Uptime Kuma. Secrets de Actions a nivel usuario (`NEXUS_USER`, `NEXUS_PASSWORD`, `GITOPS_TOKEN`), heredados por cualquier repo nuevo. Dependencia real: `git.oscar.home` solo resuelve en dispositivos con `/etc/hosts` o DNS apuntado a mano a AdGuard — no es automático en toda la LAN hoy. |
| Nexus 3.96.1 | Docker en `devops01` | Actual | `nexus.oscar.home` (UI/API `8081`), registry Docker en `192.168.0.151:8082`. npm (proxy+hosted+group) y `docker-hosted` creados y verificados, acceso anónimo deshabilitado, monitor en Uptime Kuma, cleanup policy del repo Docker asignada. Usuario dedicado `ci-forgejo` reutilizado tanto para el `docker push` del CI como para el `imagePullSecret` de k3s. Ver [Sonatype Nexus Repository](../servicios/nexus.md). |
| Relay SMTP (Brevo) | Docker en `core01` | Actual | `boky/postfix` relay-only, validado con envío real (`status=sent`). Bug real encontrado y corregido: volúmenes anónimos de la imagen acumulaban credenciales viejas entre reinicios — `docker compose down -v` + `up -d` lo resuelve. Ver [Relay SMTP](../servicios/smtp-relay.md). |
| forgejo-runner 13.1.0 | Docker en `devops01` | Actual | registrado contra Forgejo local, corre jobs en contenedores Docker efímeros. **Validado en tres niveles**: smoke test, pipeline real (`ci-demo`: lint → test → build → push a Nexus), y el loop completo hasta producción (push a `oscar-gitops` → Argo CD detecta y despliega). Ver [CI Runner](../servicios/ci-runner.md). |
| Uptime Kuma | Docker en `core01` | Actual | primer servicio real del stack Docker — `/srv/oscar/apps/uptime-kuma/`. Ver [Uptime Kuma](../servicios/uptime-kuma.md). |
| n8n + PostgreSQL 17 | Docker en `core01` | Actual | `/srv/oscar/apps/n8n/`, secretos (`POSTGRES_PASSWORD`, `N8N_ENCRYPTION_KEY`) generados únicos con `openssl rand`, no reutilizados. La encryption key ya se extrajo y se entregó fuera del chat — pendiente de confirmar que quedó guardada en un gestor de contraseñas. Ver [n8n](../servicios/n8n.md). |
| Vaultwarden 1.37.2 | Docker en `core01` | Actual | `/srv/oscar/apps/vaultwarden/`, puerto publicado solo en `127.0.0.1:8082` (ya no en LAN). Ver [Vaultwarden](../servicios/vaultwarden.md). |
| Homepage v2.3.0 | Docker en `core01` | Actual | `/srv/oscar/apps/homepage/`, puerto 3005, dashboard con links a todos los servicios reales. Ver [Homepage](../servicios/homepage.md). |
| Beszel 0.19.0 | Docker en `core01`, `devops01` y `k3s01` | Actual | un hub (puerto 8090, en `core01`) y **tres agentes** (puerto 45876 cada uno, uno por host) conectados, reportando CPU/RAM/disco en tiempo real de los tres. Ver [Beszel](../servicios/beszel.md). |
| ProxMenux Monitor | systemd en `oscar-core` (no Docker) | Actual | instalado por el autor directo en el hipervisor, `proxmenux-monitor.service`, puerto 8008. Publicado como `monitor.oscarlab.com.ar`. Ver [ProxMenux Monitor](../servicios/proxmenux-monitor.md). |
| Glances | Docker en `core01` | Actual | mide CPU/RAM/disco reales del host para el widget de Homepage — antes ese widget mostraba el uso del propio contenedor de Homepage, no el de `core01`. Ver [Glances](../servicios/glances.md). |
| MySpeed 1.0.9 | Docker en `core01` | Actual | puerto 5216, historial de tests de velocidad de internet, sin autenticación propia todavía. Ver [MySpeed](../servicios/myspeed.md). |
| Portainer 2.21.4 | Docker en `core01` (server) + `devops01` (agente) | Actual | consola de contenedores/logs de los dos hosts en un panel — uso restringido a solo lectura/estado por decisión operativa, no reemplaza los `compose.yaml` versionados en Git. `http://portainer.oscar.home` vía NPM (mismo patrón que `git`/`nexus`, sin HTTPS del lado público). Agregado fuera de `OSCAR_FINAL_INFRASTRUCTURE.md`, no formaba parte del plan de reorganización. Ver [Portainer](../servicios/portainer.md). |
| Nginx Proxy Manager 2.15.1 | Docker en `core01` | Actual | puertos 80/81/443, reverse proxy interno para las apps de Docker Compose (no para las de k3s, que van directo a Traefik — ver [DNS con AdGuard Home](../red/dns-adguard.md#wildcard-oscarhome-para-apps-de-k3s-2026-09-15)). Login real configurado (ya no el de fábrica). Proxy Host real: `git.oscar.home` → `192.168.0.151:3000`. Ver [Nginx Proxy Manager](../servicios/nginx-proxy-manager.md). |
| Cloudflare Tunnel + Access | Docker en `core01` | Actual | túnel conectado, 7 hostnames públicos (`vault`, `n8n`, `kuma`, `home`, `beszel`, `monitor`, `ha` . `oscarlab.com.ar`), cada uno con su propia Access Application y protegido por login (código de un solo uso al email del autor). Ver [Cloudflare Tunnel](../servicios/cloudflare-tunnel.md). |
| Tailscale | `core01` (subnet router) | Actual | `192.168.0.0/24` advertido y aprobado — cualquier dispositivo del tailnet alcanza toda la LAN de casa, no solo `core01`. Ver [ADR-011](./decisiones-arquitectonicas.md#adr-011--tailscale-como-vpn-de-acceso-remoto) y [acceso remoto](../red/acceso-remoto.md). |
| oscar-gitops (origen real) | Forgejo en `devops01` | Actual | ya **no es mirror** — es el repo que lee Argo CD de verdad (`root-app` y las apps debajo apuntan a `http://git.oscar.home/mdelgado/oscar-gitops.git`). GitHub queda como copia secundaria, actualizada a mano. Ver [ADR-012](./decisiones-arquitectonicas.md#adr-012--forgejo-como-mirror-de-solo-lectura-de-oscar-gitops-no-origen) (el título del ADR quedó igual a propósito para no romper otros links que ya apuntaban a él — el contenido de la decisión sí está actualizado a "origen real"). |
| ci-demo | k3s en `k3s01` (namespace `oscar-lab`) | Actual | app mínima (Node.js) que existe para validar el pipeline completo, no para servir tráfico real — cada push a `main` corre lint → test → build → push a Nexus → actualiza el tag en `oscar-gitops` → Argo CD la redespliega sola. Publicada en `ci-demo.oscar.home` (Traefik). Ver [Pipeline de ejemplo](../devops/pipeline-ejemplo.md). |
| oscar-led-controller | k3s en `k3s01` (namespace `oscar-lab`) | Actual, pod `0/1` hoy | refleja el estado de salud de O.S.C.A.R. en una tira LED física conectada a un ESP32 — el pod real puede aparecer `Unhealthy`/`0/1` cuando el ESP32 está físicamente apagado, no es una falla de la infraestructura de k3s. Publicado en `led.oscar.home` (Traefik). |

## Capacidad real (medida, no nominal) — 2026-09-15

`OSCAR_FINAL_INFRASTRUCTURE.md` (raíz del repo, fuente de verdad de arquitectura — reemplazó a un `OSCAR_TARGET_ARCHITECTURE.md` anterior, deprecado y luego eliminado el 2026-09-17) marcaba un posible overcommit de RAM: 32.5 GB asignados nominalmente entre las 4 VMs/LXC contra 32 GB físicos del Dell. Medido de verdad vía `pvesh get .../status/current` (no supuesto por lo asignado), con CPU muestreada 3 veces espaciadas para no confundir un pico momentáneo con la realidad:

| VM/LXC | RAM real | RAM asignada | CPU real | Disco real |
|---|---:|---:|---:|---:|
| `core01` | 3.51 GB | 8 GB (44%) | ~0% (idle) | 24 GB / 58 GB (41%) |
| `k3s01` | 3.29 GB | 8 GB (41%) | ~0% (idle) | 25 GB / 58 GB (43%) |
| `devops01` | 3.43 GB | 12 GB (29%) | ~0% (idle) | 6.2 GB / 58 GB (11%) |
| `haos-18.2` | 1.42 GB | 4 GB (35%) | ~0% (idle) | — |
| AdGuard (LXC) | 74 MB | 512 MB (15%) | ~0% (idle) | 0.82 GB / 1.9 GB |

**Total real: ~11.7 GB usados sobre 32 GB físicos** — el overcommit es solo nominal, hay ~63% de RAM libre en uso real. Storage de Proxmox con el mismo margen: `local-lvm` (NVMe) al 9%, `Backups` (SATA) al 8.85%.

**Hallazgo real (2026-09-15), confirmado por un incidente real tres días después:** `core01`/`devops01`/`k3s01` tienen IP fija de verdad vía Cloud-Init (`ipconfig0`), pero **AdGuard (LXC 100) usaba `ip=dhcp`** — su IP (`192.168.0.93`, hardcodeada en rewrites DNS, Tailscale y varios widgets de Homepage) dependía de que el router siguiera devolviendo la misma IP por DHCP. Quedó anotado como riesgo sin resolver — y se manifestó de verdad.

## Incidente real (2026-09-18): hang de la NIC física, caída de `core01` y AdGuard

A las 18:19 la placa de red física del Dell (`e1000e`) tiró un **"Detected Hardware Unit Hang"** en el kernel de Proxmox (fallo real de hardware/driver, visible en `journalctl -p err`). El bridge (`vmbr0`) y el resto del host siguieron sanos, pero dejó dos guests puntuales inalcanzables por red, sin afectar a `devops01` ni `k3s01`:

- **`core01`**: la VM seguía viva por dentro (el guest agent de Proxmox respondía, `qm agent 102 ping` con éxito, IP interna correcta) — el problema era la interfaz virtual del lado del host (`tap102i0`), que quedó en mal estado tras el hang. Esto tumbó `cloudflared` (dejó de poder llegar al edge de Cloudflare) y con eso `home.oscarlab.com.ar` y el resto de los hostnames públicos — aunque el contenedor de `cloudflared` nunca se reinició, solo perdió conectividad de red. Se resolvió reseteando esa interfaz puntual desde el host (`ip link set tap102i0 down && up`), sin tocar la VM — `cloudflared` reconectó solo apenas volvió la red, sin reiniciar el contenedor.
- **AdGuard (LXC)**: perdió su IP por completo — `ip addr show eth0` no mostraba ninguna dirección IPv4 tras el hang, justo el escenario que el hallazgo de arriba había anticipado. Se resolvió primero forzando una renovación DHCP (`dhclient -v eth0`, recuperó la misma IP) y **después pasándolo a IP estática de verdad** (`pct set 100 -net0 ...,ip=192.168.0.93/24,gw=192.168.0.1,...` + reinicio del contenedor para limpiar el `dhclient` que seguía corriendo) — mismo criterio que las otras 3 VMs, cierra el riesgo que quedó anotado el 15.

**Verificado sano después:** `qm agent`/ping a los 4 hosts, DNS de AdGuard resolviendo `*.oscar.home`, `cloudflared` con conexión registrada en los logs, `home.oscarlab.com.ar` respondiendo `302` (Access) desde afuera.

## Dominio — en uso

`oscarlab.ar` y `oscarlab.com.ar` están registrados (NIC Argentina, pagos — $25.500 y $8.500 ARS respectivamente) y delegados a Cloudflare. `oscarlab.com.ar` es el dominio primario: los 7 servicios reales ya tienen subdominio público protegido por Cloudflare Access — ver [Cloudflare Tunnel](../servicios/cloudflare-tunnel.md).

## Backups — parcialmente resuelto

Ya existe un job `vzdump` automático (lunes a viernes 00:00, `all:1` así que cualquier VM/LXC nueva se suma sola, modo snapshot, comprimido zstd, hacia el storage `Backups`, retención 5 últimos + 1 mensual + 6 anuales) — y ya generó backups reales de la VM 101 y el LXC 100 con status `OK`.

Lo que todavía falta, y es la parte que realmente importa para disaster recovery:

- **Sin copia off-site** — el backup vive en el mismo Dell que respalda. Un fallo del equipo completo (placa, robo, incendio) se lleva la VM *y* su backup juntos — ver [estrategia 3-2-1](../backup-dr/estrategia-321.md).
- **Nunca se probó un restore** — un backup no verificado es una hipótesis.
- **La config del propio Proxmox (`/etc/pve`) no está en este job** — `vzdump` respalda VMs/LXC, no la configuración del hypervisor.

## Lo que NO existe todavía

- Grafana, Prometheus, Loki y el resto del stack de observabilidad dedicado (hoy la única observabilidad real es Uptime Kuma + Beszel + Homepage);
- HA de k3s (más de un nodo) — hoy es un solo nodo, sin tolerancia a caídas;
- red segmentada / VLANs / firewall dedicado (OPNsense);
- copia de backup off-site, restore probado, backup de la config de Proxmox, backup de `core01`/`devops01`/`k3s01` (ver arriba y abajo — el `vzdump` cubre VMs/LXC en general, pero un restore nunca se probó);
- Raspberry Pi 5, NAS, switch gestionable definitivo.

## Próximo paso real

El build no siguió el orden lineal del [roadmap](../roadmap/roadmap-general.md) al pie de la letra — Proxmox y dos servicios del hogar (Fase 7) ya existían antes de que existiera `core01` (Fase 3), el backup local (parte de Fase 4) ya estaba resuelto sin que se instalara nada del medio, y k3s/Argo CD/GitOps (Fase 8) ya está corriendo y en uso real. Eso está bien: el roadmap es una guía de dependencias razonables, no una secuencia obligatoria. Lo que sí falta con prioridad, dado lo que ya hay corriendo:

1. **Confirmar que la `N8N_ENCRYPTION_KEY` quedó guardada en un gestor** (Vaultwarden ya está arriba para esto) — se extrajo del servidor pero la única copia real es la que el usuario guarde.
2. **Completar el primer acceso de Vaultwarden** — el bloqueo de HTTPS ya se resolvió (Cloudflare Tunnel + Access en `vault.oscarlab.com.ar`); falta crear la cuenta real y deshabilitar `SIGNUPS_ALLOWED`.
3. **Copia off-site del backup** — sigue siendo la brecha real de disaster recovery; el backup local ya existe, pero no protege contra la pérdida del Dell completo.
4. **`core01`/`devops01`/`k3s01` todavía no están confirmadas en el job de backup** — el `vzdump all:1` las incluye automáticamente en la próxima corrida programada; verificarlo en la próxima ejecución (lunes a viernes 00:00).
5. Integrar el UPS (ver [backlog](../roadmap/backlog.md)) — más urgente ahora que hay servicios reales con estado (Postgres, Vaultwarden) que un corte de luz podría corromper.

## Por qué esta página existe

El resto de la documentación describe deliberadamente la arquitectura **objetivo** con el mismo nivel de detalle que si ya existiera — eso es intencional (ver [principios](./principios.md)): permite construir sin rediseñar sobre la marcha. El costo de ese enfoque es que un lector nuevo puede confundir "está bien documentado" con "está instalado". Esta página es el antídoto: si no aparece acá como **Actual**, no existe todavía, sin importar cuántas páginas hable de eso.
