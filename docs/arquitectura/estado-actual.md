---
title: Estado actual
sidebar_position: 1
---

# Estado actual de O.S.C.A.R.

Esta página es la única fuente de "qué existe de verdad hoy". El resto del sitio describe mayormente **Objetivo** y **Laboratorio** — es fácil, leyendo la doc completa, terminar pensando que hay más construido de lo que realmente hay. Esta página existe para que esa brecha nunca quede implícita.

Se actualiza en cada cambio de fase real (ver [roadmap](../roadmap/roadmap-general.md)), no en cada edición de documentación.

:::caution
Al momento de escribir esto, **no hay ningún servicio de software corriendo**. Todo lo de abajo es hardware físico. Proxmox todavía no está instalado.
:::

## Hardware — existe físicamente

| Componente | Estado | Nota |
|---|---|---|
| Rack GeeekPi RackMate T2 (10", 12U) | Actual | — |
| Dell OptiPlex 7060 Micro (i7 8ª gen, 16 GB, NVMe 512 GB + SATA 1 TB) | Actual | Todavía sin Proxmox instalado. |
| 2× Raspberry Pi 3, 3× Pi Zero W | Actual | Sin rol asignado todavía. |
| Router/mesh TP-Link Archer AX55 | Actual | Es el gateway hoy — no hay firewall dedicado. |
| Switch TP-Link TL-SF1008D (8p/100 Mbps) | Actual, marcado para reemplazo | Bloquea VLAN y gigabit real. |
| Patch panel CAT6 12p, pantalla táctil 9", paneles de gestión/ventilación | Actual | Montaje físico, sin uso funcional todavía. |
| UPS + estabilizador | Actual, **no integrado** | Existen pero están fuera del rack, sin conectar ni monitorear — ver [runbook de corte eléctrico](../runbooks/corte-electrico.md). |
| DVR Dahua 4 canales | Actual, **no integrado** | Es hardware propio del autor, no un requisito de arquitectura — ver [CCTV](../hogar/cctv-dahua.md). |

## Lo que NO existe todavía

- Proxmox (ni instalado ni configurado);
- cualquier VM o LXC;
- cualquier servicio Docker (n8n, Uptime Kuma, Grafana, Nexus, etc.);
- k3s / Argo CD;
- red segmentada / VLANs / firewall dedicado (OPNsense);
- backups automatizados o probados;
- Raspberry Pi 5, NAS, switch gestionable definitivo.

## Próximo paso real

El [roadmap](../roadmap/roadmap-general.md) está en **Fase 0 · Fuente de verdad**, con la Fase 1 (rack y red) como siguiente. Ver el [checklist del primer build](../roadmap/checklist-primer-build.md) para la secuencia concreta de próximos pasos.

## Por qué esta página existe

El resto de la documentación describe deliberadamente la arquitectura **objetivo** con el mismo nivel de detalle que si ya existiera — eso es intencional (ver [principios](./principios.md)): permite construir sin rediseñar sobre la marcha. El costo de ese enfoque es que un lector nuevo puede confundir "está bien documentado" con "está instalado". Esta página es el antídoto: si no aparece acá como **Actual**, no existe todavía, sin importar cuántas páginas hable de eso.
