---
title: Backlog técnico
sidebar_position: 2
---

# Backlog

## Prioridad alta (barato/rápido, desbloquea el resto)

- **integrar el UPS/estabilizador existente** al rack (reubicar + NUT) — ya está pagado, es la tarea de menor costo/mayor impacto del backlog, ver [Fase 1 del roadmap](./roadmap-general.md#fase-1--rack-red-y-energía);
- **destino off-site de backup** — no requiere NAS ni hardware nuevo, alcanza con una cuenta de object storage barata; hoy es el mayor riesgo activo porque todo vive en un solo Dell (ver [estrategia 3-2-1](../backup-dr/estrategia-321.md));
- switch >8 puertos definitivo para RackMate T2 (cualquier gigabit gestionable que entre en 10" resuelve esto — no requiere tanta deliberación como las demás decisiones de esta lista).

## Resueltas recientemente

- **RAM del Dell**: ampliada de 16 GB a 32 GB (ambos slots ocupados — sin margen para ampliar más sin reemplazar módulos), y de paso el M.2 de 512 GB a 1 TB (slot único, reemplazo en vez de suma). Desbloquea separar observabilidad en su propia VM — ver [distribución con 32 GB](../hardware/dell-7060.md#distribución-con-32-gb).
- **plataforma Git local + CI Runner + registry**: Forgejo 16.0.4 desplegado en `devops01` ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)), admin creado, `http://git.oscar.home` sin puerto vía [Nginx Proxy Manager](../servicios/nginx-proxy-manager.md#proxy-hosts-reales), y [Nexus 3.96.1](../servicios/nexus.md) con npm+Docker registry configurados — el pipeline `lint → test → build → push Nexus → GitOps → Argo CD` ya está **encadenado y validado end-to-end** con un proyecto real (`ci-demo`): un push a `main` termina en un pod nuevo corriendo en k3s sin intervención manual. Ver [CI Runner](../servicios/ci-runner.md) y [Pipeline de ejemplo](../devops/pipeline-ejemplo.md).
- **Dos reverse proxies en paralelo**: se había armado un nginx standalone en `devops01` porque Nginx Proxy Manager (`core01`) parecía seguir con el login de fábrica — resultó que ya estaba cambiado, la doc estaba desactualizada. Consolidado en NPM, el nginx de `devops01` se bajó.
- **acceso remoto tipo VPN**: [Tailscale](../red/acceso-remoto.md) desplegado — `core01` como subnet router de `192.168.0.0/24`, dispositivo y ruta aprobados. Ver [ADR-011](../arquitectura/decisiones-arquitectonicas.md#adr-011--tailscale-como-vpn-de-acceso-remoto).
- **oscar-gitops migrado a Forgejo como origen real**: se pasó del mirror de solo lectura a origen real — Argo CD (`root-app` y `oscar-led-controller`) lee `repoURL: http://git.oscar.home/mdelgado/oscar-gitops.git`, GitHub queda como copia secundaria sincronizada a mano. Requirió una entrada custom en CoreDNS (`git.oscar.home` no resolvía dentro del cluster) y un Secret de credenciales dedicado (token de solo lectura, no la cuenta admin). Ver [ADR-012](../arquitectura/decisiones-arquitectonicas.md#adr-012--forgejo-como-mirror-de-solo-lectura-de-oscar-gitops-no-origen).
- **relay SMTP**: Brevo + `boky/postfix` en `core01`, validado con envío real. La autenticación fallaba por un bug del contenedor (volúmenes anónimos acumulando credenciales viejas entre reinicios, no un problema de la cuenta de Brevo) — ver [Relay SMTP](../servicios/smtp-relay.md).
- **autostart de VMs tras un reinicio del host**: `core01`, `k3s01` y `devops01` no tenían `onboot: 1` en Proxmox (solo Home Assistant lo tenía) — un reinicio de `oscar-core` las dejaba apagadas hasta encenderlas a mano, aunque Docker/k3s ya estuvieran bien configurados para autorecuperarse adentro. Corregido en las cuatro. Ver [Operación de Proxmox](../proxmox/operacion.md#autostart-de-vms-onboot).
- **wildcard DNS para apps de k3s**: cada Ingress nuevo de Argo CD necesitaba un rewrite manual en AdGuard — reemplazado por un solo `*.oscar.home -> 192.168.0.150` (Traefik), cualquier app nueva resuelve sola. Ver [DNS con AdGuard Home](../red/dns-adguard.md#wildcard-oscarhome-para-apps-de-k3s-2026-09-15).
- **500 falsos en Homepage** (Beszel devops01/k3s01, DVR Dahua): dos causas reales, ninguna era el servicio en sí — `siteMonitor` apuntando al puerto del agente de Beszel en vez del hub, y una incompatibilidad real entre el servidor HTTP del DVR y el parser estricto de Node. Ver [Homepage](../servicios/homepage.md#troubleshooting).
- **Incidente real (2026-09-18): hang de la NIC física del Dell** (`e1000e`, "Detected Hardware Unit Hang") tumbó `core01` (interfaz virtual del host en mal estado, la VM seguía viva por dentro) y le hizo perder la IP al LXC de AdGuard — cortó `home.oscarlab.com.ar` y el resto de hostnames públicos vía `cloudflared`. Resuelto sin reiniciar la VM (reset de la interfaz `tap102i0`); AdGuard pasó a IP estática de una vez, cerrando el riesgo de abajo. Ver [estado actual](../arquitectura/estado-actual.md).
- **Causa raíz del incidente de throughput de AdGuard, diagnosticada**: `ratelimit: 20` por subred — toda la LAN compartía 20 consultas DNS/segundo, se agotaba con varios dispositivos a la vez y las consultas de más se perdían en silencio (no era el ancho de banda real de internet). Confirmado con prueba propia (Python, UDP async, con control): subido a `ratelimit: 300`. Ver [DNS con AdGuard Home](../red/dns-adguard.md#incidente-de-throughput--diagnosticado-2026-09-18).
- **AdGuard activado como DNS de toda la LAN vía DHCP**: con la causa raíz de arriba corregida, se reintentó — router (TP-Link Archer) reparte `192.168.0.93` primario + `1.1.1.1` secundario. Backup de la config del router hecho antes, por las dudas. Validado con tráfico real de un dispositivo (no solo prueba sintética): +397 paquetes UDP durante una sesión de navegación normal, recursos sin moverse de casi cero, bloqueo real de un dominio de tracking confirmado. `*.oscar.home` ya resuelve solo en cualquier dispositivo con DNS automático, sin `/etc/hosts` ni configuración manual. Ver [DNS con AdGuard Home](../red/dns-adguard.md#activado-de-verdad-dhcp-de-red-completa-2026-09-18).
- **`systemd-resolved` de `core01` pegado en `1.1.1.1`**: tras los reinicios de AdGuard del diagnóstico del `ratelimit`, el host había marcado a `192.168.0.93` como no disponible y no volvió a probarlo solo, aunque seguía primero en la config — rompía la resolución de `.oscar.home` para el propio host y para el contenedor de Homepage (`portainer.oscar.home` daba `ENOTFOUND`). Fix: `systemctl restart systemd-resolved` en el host. Ver [DNS con AdGuard Home](../red/dns-adguard.md#incidente-menor-systemd-resolved-de-core01-no-volvía-a-usar-adguard-2026-09-18).
- **Homepage: widgets de recursos reorganizados en un grupo "Monitoreo"**: Proxmox, ProxMenux, Glances y los 3 Beszel estaban repartidos entre "Infraestructura" y "Servicios" sin ningún criterio visible, dando la impresión de que eran 6 copias del mismo dato — en realidad cada uno mide un recorte distinto (hipervisor completo vs. solo `core01` vs. por-VM). Consolidados en un grupo nuevo con una `description` por tarjeta que aclara su alcance real y con qué otra tarjeta se superpone. Ver [Homepage](../servicios/homepage.md#grupo-monitoreo-por-qué-existe).

- **Minecraft y Counter-Strike 2 desplegados**: Minecraft (Java Vanilla) como contenedor en `core01`, jugable en `192.168.0.156:25565`. CS2 en una VM nueva dedicada (`lab01`, vmid 105, 4 vCPU/6 GB), con GSLT real cargado. Cards nuevas en Homepage (grupo "Juegos", widgets `minecraft`/`gamedig` con estado en vivo). Ver [servidores de juegos](../juegos/vision-general.md).
- **AdGuard como DNS de toda la LAN, revertido el mismo día que se activó**: la recurrencia del hang de NIC (ver abajo) tumbó AdGuard intermitentemente mientras toda la casa dependía de él como primario — se sintió como un corte de internet real (caso: `drive.tresdoce.com.ar` inaccesible). Router vuelto al backup de antes del cambio. Ver [rollback documentado](../red/dns-adguard.md#rollback-el-dhcp-wide-se-revirtió-2026-09-18).

## Prioridad alta — pendiente

- **Mitigar el hang recurrente de la NIC física del Dell** (`e1000e`, Intel I219-LM): segunda vez en la misma semana (2026-09-18 dos veces) que tira "Detected Hardware Unit Hang" y deja intermitentemente inalcanzable a `core01`/AdGuard/la gestión del propio Proxmox. Bug conocido y documentado en la comunidad de Proxmox para esta NIC exacta — mitigación investigada y lista para aplicar (deshabilitar TSO/GSO/GRO + EEE por `ethtool`, persistido en `/etc/network/interfaces`), **decidido posponerla** por el usuario, no aplicada todavía. Bloquea reactivar AdGuard como DNS de toda la LAN con confianza — ver el ítem de arriba.

## Decisiones pendientes

- hardware N100/OPNsense;
- NAS (Raspberry Pi vs equipo dedicado vs comercial);
- gestor de secretos;
- ubicación final de Home Assistant;
- proveedor/backends de IA;
- **AdGuard primario real en `network01` (Pi 3)**: hoy el DNS primario sigue siendo el AdGuard del Dell (`192.168.0.93`) y el secundario es `1.1.1.1` (Cloudflare) — son roles provisorios. El diseño real es AdGuard en `network01` (Pi 3) como primario, y el del Dell pasando a secundario — depende de aprovisionar las Raspberry Pi (Fase 2/3/4 del plan de reorganización). La Pi Zero W no tiene rol de DNS — es `edge01` (sensores/GPIO), un error de una versión vieja del plan (`OSCAR_TARGET_ARCHITECTURE.md`, deprecado) que quedó dando vueltas y ya se corrigió.
- **Querylog de AdGuard no se está flusheando a disco**: la resolución real funciona (confirmado de varias formas), pero `querylog.json` no reflejó tráfico real reciente tras los reinicios del servicio del 18/9 — puede afectar las estadísticas de la UI, no la resolución. Sin diagnosticar todavía.

## Mejoras futuras

- Ansible;
- Terraform provider Proxmox;
- Renovate/Dependabot para imágenes y manifests;
- SBOM/Trivy en pipelines;
- Proxmox Backup Server;
- segundo host Proxmox;
- HA k3s;
- PKI interna;
- SSO interno;
- sensores ambientales del rack.
