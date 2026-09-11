---
title: Estado actual
sidebar_position: 1
---

# Estado actual de O.S.C.A.R.

Esta página es la única fuente de "qué existe de verdad hoy". El resto del sitio describe mayormente **Objetivo** y **Laboratorio** — es fácil, leyendo la doc completa, terminar pensando que hay más construido de lo que realmente hay. Esta página existe para que esa brecha nunca quede implícita.

Se actualiza en cada cambio de fase real (ver [roadmap](../roadmap/roadmap-general.md)), no en cada edición de documentación.

:::caution
Proxmox ya está instalado y hay dos servicios reales corriendo (abajo). Todo lo demás del sitio que dice "Objetivo" sigue sin existir — esta página es la línea exacta entre lo uno y lo otro.
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
| DVR Dahua 4 canales | Actual, **no integrado** | Es hardware propio del autor, no un requisito de arquitectura — ver [CCTV](../hogar/cctv-dahua.md). |

## Software — corriendo hoy en `oscar-core`

| Componente | Tipo | Estado | Nota |
|---|---|---|---|
| Proxmox VE 9.2.18 | Hypervisor | Actual | Nodo único `oscar-core`, storage `local-lvm` (M.2) + `Backups` (SATA, dir storage). Sano: load bajo, sin swap, sin tareas fallidas. |
| Home Assistant OS 18.2 | VM (vmid 101) | Actual | 2 vCPU / 4 GB / 32 GB disco, instalada vía community-script. Ver [Home Assistant](../servicios/home-assistant.md). |
| AdGuard Home | LXC (vmid 100) | Actual | 1 vCPU / 512 MB, instalada vía community-script. Reemplaza a Pi-hole — ver [DNS con AdGuard Home](../red/dns-adguard.md). |

## Lo que NO existe todavía

- `core01` / Docker Core y cualquier servicio Docker (n8n, Uptime Kuma, Grafana, Nexus, etc.);
- k3s / Argo CD;
- red segmentada / VLANs / firewall dedicado (OPNsense);
- backups automatizados o probados (ni de las VMs/LXC actuales, ni off-site);
- Raspberry Pi 5, NAS, switch gestionable definitivo.

## Próximo paso real

El build no siguió el orden lineal del [roadmap](../roadmap/roadmap-general.md) al pie de la letra — Proxmox y dos servicios del hogar (Fase 7) ya existen antes de que exista `core01` (Fase 3) o backups probados (Fase 4). Eso está bien: el roadmap es una guía de dependencias razonables, no una secuencia obligatoria. Lo que sí falta con prioridad, dado lo que ya hay corriendo:

1. **Backup de lo que ya existe** — ni la VM de Home Assistant ni el LXC de AdGuard tienen backup probado todavía; son los primeros candidatos reales para `vzdump`, no solo teoría.
2. `core01` con Docker, para tener un lugar real donde correr el resto del stack.
3. Integrar el UPS (ver [backlog](../roadmap/backlog.md)) — más urgente ahora que hay dos servicios reales que un corte de luz podría corromper.

## Por qué esta página existe

El resto de la documentación describe deliberadamente la arquitectura **objetivo** con el mismo nivel de detalle que si ya existiera — eso es intencional (ver [principios](./principios.md)): permite construir sin rediseñar sobre la marcha. El costo de ese enfoque es que un lector nuevo puede confundir "está bien documentado" con "está instalado". Esta página es el antídoto: si no aparece acá como **Actual**, no existe todavía, sin importar cuántas páginas hable de eso.
