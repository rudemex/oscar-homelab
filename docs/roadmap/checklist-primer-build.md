---
title: Checklist del primer build
sidebar_position: 4
---

# Primer build real de O.S.C.A.R.

## Antes

- [ ] inventario revisado;
- [ ] backup de datos del Dell;
- [ ] switch final o transición planificada;
- [ ] patch panel etiquetado;
- [ ] USB Proxmox preparado;
- [ ] IP/gateway/DNS anotados;
- [ ] acceso a esta documentación desde otro dispositivo.

## Día de Proxmox

- [ ] instalar;
- [ ] update;
- [ ] management accesible;
- [ ] storage sano;
- [ ] crear template;
- [ ] crear `core01`;
- [ ] instalar Docker;
- [ ] deploy whoami;
- [ ] backup de `core01`;
- [ ] restore de prueba.

## Siguiente sesión

- [ ] Uptime Kuma;
- [ ] Prometheus/node exporter;
- [ ] Grafana;
- [ ] n8n;
- [ ] primera alerta;
- [ ] dashboard rack.

No avanzar a k3s si todavía no podemos detectar y recuperar una falla básica en la capa anterior.
