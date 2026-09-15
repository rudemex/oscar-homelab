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
- **plataforma Git local + CI Runner + registry**: Forgejo 16.0.4 desplegado en `devops01` ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)), admin creado, `http://git.oscar.home` sin puerto vía [Nginx Proxy Manager](../servicios/nginx-proxy-manager.md#proxy-hosts-reales), CI Runner (`forgejo-runner` 13.1.0) **validado end-to-end** con un workflow real, y [Nexus 3.96.1](../servicios/nexus.md) con npm+Docker registry configurados — el pipeline `lint → test → build → push Nexus → GitOps → Argo CD` ya tiene todas sus piezas desplegadas y probadas individualmente, falta encadenarlas en un workflow real de un proyecto propio.
- **Dos reverse proxies en paralelo**: se había armado un nginx standalone en `devops01` porque Nginx Proxy Manager (`core01`) parecía seguir con el login de fábrica — resultó que ya estaba cambiado, la doc estaba desactualizada. Consolidado en NPM, el nginx de `devops01` se bajó.

## Decisiones pendientes

- hardware N100/OPNsense;
- NAS (Raspberry Pi vs equipo dedicado vs comercial);
- gestor de secretos;
- ubicación final de Home Assistant;
- proveedor/backends de IA;
- **acceso remoto tipo VPN**: recomendado Tailscale sobre WireGuard nativo (no depende de que exista OPNsense, sin port-forward, alta en segundos) — falta desplegar, ver [ADR-006](../arquitectura/decisiones-arquitectonicas.md#adr-006--cloudflare-tunnel--access-para-acceso-remoto) y [acceso remoto](../red/acceso-remoto.md);
- **relay SMTP**: salida vía proveedor transaccional free-tier (Brevo/Resend/Mailgun) — falta elegir proveedor y crear la cuenta;
- **AdGuard como DNS de toda la LAN**: pausado — coincidió con una caída real de throughput (600→20 Mbps) sin diagnosticar todavía, ver [DNS con AdGuard Home](../red/dns-adguard.md#incidente-sin-resolver-caída-de-throughput-al-usarlo-como-dns-de-red). Mientras tanto, `*.oscar.home` requiere `/etc/hosts` o DNS configurado a mano por dispositivo (las máquinas de administración ya usaban `/etc/hosts` para `argocd`/`led` desde antes, sin documentar).

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
