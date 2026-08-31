---
title: Roadmap general
sidebar_position: 1
slug: /roadmap/roadmap-general
---

# Roadmap de construcción

El roadmap evita instalar componentes fuera de orden.

```mermaid
flowchart LR
  P0[0 · Documentar] --> P1[1 · Rack/Red]
  P1 --> P2[2 · Proxmox]
  P2 --> P3[3 · Core]
  P3 --> P4[4 · Backup/Observability]
  P4 --> P5[5 · DevOps]
  P5 --> P6[6 · k3s/GitOps]
  P6 --> P7[7 · Hogar]
  P7 --> P8[8 · IA]
  P8 --> P9[9 · Hardening/DR]
```

## Fase 0 · Fuente de verdad

- [x] estructura Docusaurus;
- [ ] cerrar inventario real;
- [ ] registrar fotos/diagramas del rack;
- [ ] naming e IP plan;
- [ ] ADR del switch final.

**Gate:** sabemos qué tenemos y qué falta.

## Fase 1 · Rack, red y energía

- montar patch panel;
- instalar switch gigabit gestionable;
- etiquetar puertos;
- medir enlaces;
- organizar energía/ventilación;
- **reubicar y conectar el UPS/estabilizador existente** (no hay que comprar nada — es cableado + configurar NUT, ver [corte eléctrico](../runbooks/corte-electrico.md)); tratarlo como parte de esta fase y no como una mejora futura, porque protege todo lo que se construya después;
- documentar red actual.

**Gate:** todos los enlaces negocian correctamente, el cableado es trazable, y un corte de luz simulado dispara un apagado limpio (no solo teórico) del equipo que esté encendido en ese momento.

## Fase 2 · Proxmox

- backup previo del Dell;
- instalar Proxmox;
- storage;
- bridge;
- template Cloud-Init;
- VM de prueba;
- backup inicial.

**Gate:** una VM puede crearse, respaldarse, destruirse y restaurarse.

## Fase 3 · Core services

- VM Core;
- Docker Compose;
- DNS secundario/estrategia DNS;
- reverse proxy/acceso interno;
- n8n base;
- Uptime Kuma.

**Gate:** servicios tienen health y persistencia documentada.

## Fase 4 · Observabilidad y backup

- Prometheus;
- Grafana;
- exporters;
- alertas mínimas;
- backups automáticos locales;
- **destino off-site resuelto** (aunque sea la opción más simple de [estrategia 3-2-1](../backup-dr/estrategia-321.md)) — no avanzar a Fase 5/6 solo con backup local: hoy todo el homelab vive en un único Dell, y sin una copia fuera de esa caja, un backup "exitoso" en el mismo disco no protege contra la falla que más importa;
- primer restore drill;
- dashboard pantalla 9".

**Gate:** una falla controlada genera señal, se puede recuperar desde backup, y esa recuperación se probó desde la copia off-site al menos una vez (no solo desde la copia local).

## Fase 5 · DevOps

- Nexus;
- Git local o integración elegida;
- runner;
- pipeline de demo;
- image scanning opcional.

**Gate:** commit produce artefacto versionado en registry.

## Fase 6 · Kubernetes/GitOps

- k3s single-node;
- app demo;
- Argo CD;
- repo GitOps;
- observabilidad del cluster;
- backup/rebuild procedure.

**Gate:** un cambio Git despliega y un revert revierte.

## Fase 7 · Hogar

- Home Assistant;
- sensores del rack;
- CCTV segmentado cuando VLAN exista;
- Internet probe;
- automatizaciones útiles.

## Fase 8 · IA

- RAG de documentación;
- herramientas read-only;
- integración de métricas/logs;
- acciones seguras mediante n8n/MCP;
- auditoría.

## Fase 9 · Hardening/DR

- OPNsense y VLAN completas;
- segunda copia off-site;
- secretos maduros;
- restore drills;
- disaster game day;
- revisión de permisos de agentes.
