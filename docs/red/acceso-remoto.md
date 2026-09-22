---
title: Acceso remoto
sidebar_position: 5
---

# Acceso remoto

El objetivo es administrar O.S.C.A.R. sin publicar paneles directamente en Internet.

## Opciones

### VPN — Tailscale (Actual)

Desplegado con **dos subnet routers** que advierten `192.168.0.0/24`: [`pinode01`](../hardware/network.md) (Raspberry Pi 3, IP de tailnet `100.102.205.119`) y `core01` anuncian la misma ruta y las dos están aprobadas (2026-09-21). Tailscale usa **uno solo a la vez** y pasa al otro si el activo se cae; **no hay prioridad configurable ni vuelta automática** ("failback"): quien queda activo después de una caída sigue activo aunque el otro vuelva. Para saber cuál está activo: `tailscale status --json` y mirar `PrimaryRoutes` en cada equipo. Cualquier dispositivo sumado al mismo tailnet puede alcanzar cualquier IP de la LAN de casa, no solo la de los routers.

La razón de sumar `pinode01`: con un solo router en `core01`, una caída del Dell dejaba sin acceso remoto justo cuando más hacía falta. **Respaldo validado (2026-09-21):** con `tailscale down` en `pinode01`, la ruta pasó a `core01` en menos de 30 s y desde el celular con datos móviles se siguió cargando Homepage (`http://192.168.0.156:3005/`). Al volver a subir `pinode01` la ruta **se quedó en `core01`** (sin failback), y así quedó.

Se prefirió sobre WireGuard nativo por no depender de OPNsense (no desplegado todavía) ni de port-forward en el router — ver [ADR-006](../arquitectura/decisiones-arquitectonicas.md#adr-006--cloudflare-tunnel--access-para-acceso-remoto).

Dos pasos de aprobación separados, ambos manuales por diseño de Tailscale (no hay forma de saltarlos por API sin un auth key pre-generado):
1. **Login del dispositivo** (`tailscale up` imprime una URL de auth — visitarla y aprobar el dispositivo).
2. **Aprobar el subnet route** aparte, en `https://login.tailscale.com/admin/machines` → `core01` → habilitar `192.168.0.0/24` — un dispositivo puede estar "conectado" sin que su ruta esté activa todavía.

**Ojo con el tailnet:** loguearse con un email corporativo (Google Workspace, Microsoft 365) puede unir el dispositivo automáticamente al tailnet de esa organización en vez de crear/usar uno personal — repasar las ACLs de ese tailnet antes de advertir una LAN doméstica completa ahí, porque un tailnet con políticas permisivas puede dejar la red de casa alcanzable para otros dispositivos/personas de la organización.

Instalar el cliente en cada dispositivo desde el que se quiera acceder (laptop, celular) con la misma cuenta — paso manual, no se automatiza desde acá.

**Limitación real conocida:** conectado por Tailscale, hay ruta de red por IP a cualquier host de la LAN, pero las **apps web de k3s no responden por IP**: `http://192.168.0.150/` devuelve `404` porque es Traefik, y Traefik solo contesta a los hostnames de sus Ingress (`argocd.oscar.home`, etc.). Ese `404` es la confirmación de que la ruta anda (se llegó a Traefik), no un fallo. Las apps de Docker Compose con puerto propio sí cargan por IP (`http://192.168.0.156:3005/`, Homepage, verificado desde el celular por `pinode01`). Tampoco se llega por hostname `*.oscar.home` — ese wildcard solo resuelve contra AdGuard (`192.168.0.93`), y Tailscale no manda las consultas DNS del dispositivo ahí a menos que se configure *Split DNS* en el admin de Tailscale (`login.tailscale.com/admin/dns`, nameserver `192.168.0.93` restringido al dominio `oscar.home`). Se evaluó y se descartó a propósito (2026-09-15): el objetivo de `*.oscar.home` es DNS por nombre dentro de la LAN, no resolver el acceso remoto — ver [DNS con AdGuard Home](./dns-adguard.md#cómo-resuelven-hoy-los-dispositivos). Si en algún momento se quiere que `argocd.oscar.home` (por ejemplo) ande también desde el celular vía Tailscale, ese Split DNS es el camino, simplemente no está activado hoy.

### Cloudflare Tunnel + Access

Útil para exponer aplicaciones HTTP seleccionadas sin inbound port-forward. El túnel debe complementarse con políticas de identidad cuando la aplicación sea administrativa.

### SSH

SSH solo debe exponerse a redes de administración o a través de VPN/bastion. Preferir claves y deshabilitar password login cuando sea viable.

## Clasificación por servicio

| Servicio | Acceso remoto sugerido |
|---|---|
| Proxmox | VPN / red MGMT |
| OPNsense | VPN / LAN MGMT |
| Grafana | VPN o Access |
| n8n | VPN o Access; webhooks públicos solo los necesarios |
| aplicación demo pública | Tunnel/reverse proxy |
| Argo CD | VPN o Access |

## Regla

Publicar un hostname no debe ser equivalente a conceder acceso.
