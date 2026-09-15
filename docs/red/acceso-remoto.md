---
title: Acceso remoto
sidebar_position: 5
---

# Acceso remoto

El objetivo es administrar O.S.C.A.R. sin publicar paneles directamente en Internet.

## Opciones

### VPN — Tailscale (Actual)

Desplegado: `core01` corre como **subnet router**, advirtiendo `192.168.0.0/24` — cualquier dispositivo sumado al mismo tailnet puede alcanzar cualquier IP de la LAN de casa, no solo `core01`.

Se prefirió sobre WireGuard nativo por no depender de OPNsense (no desplegado todavía) ni de port-forward en el router — ver [ADR-006](../arquitectura/decisiones-arquitectonicas.md#adr-006--cloudflare-tunnel--access-para-acceso-remoto).

Dos pasos de aprobación separados, ambos manuales por diseño de Tailscale (no hay forma de saltarlos por API sin un auth key pre-generado):
1. **Login del dispositivo** (`tailscale up` imprime una URL de auth — visitarla y aprobar el dispositivo).
2. **Aprobar el subnet route** aparte, en `https://login.tailscale.com/admin/machines` → `core01` → habilitar `192.168.0.0/24` — un dispositivo puede estar "conectado" sin que su ruta esté activa todavía.

**Ojo con el tailnet:** loguearse con un email corporativo (Google Workspace, Microsoft 365) puede unir el dispositivo automáticamente al tailnet de esa organización en vez de crear/usar uno personal — repasar las ACLs de ese tailnet antes de advertir una LAN doméstica completa ahí, porque un tailnet con políticas permisivas puede dejar la red de casa alcanzable para otros dispositivos/personas de la organización.

Instalar el cliente en cada dispositivo desde el que se quiera acceder (laptop, celular) con la misma cuenta — paso manual, no se automatiza desde acá.

**Limitación real conocida:** conectado por Tailscale, se llega por IP a cualquier host de la LAN (`192.168.0.150`, etc.) pero **no** por hostname `*.oscar.home` — ese wildcard solo resuelve contra AdGuard (`192.168.0.93`), y Tailscale no manda las consultas DNS del dispositivo ahí a menos que se configure *Split DNS* en el admin de Tailscale (`login.tailscale.com/admin/dns`, nameserver `192.168.0.93` restringido al dominio `oscar.home`). Se evaluó y se descartó a propósito (2026-09-15): el objetivo de `*.oscar.home` es DNS por nombre dentro de la LAN, no resolver el acceso remoto — ver [DNS con AdGuard Home](./dns-adguard.md#cómo-resuelven-hoy-los-dispositivos). Si en algún momento se quiere que `argocd.oscar.home` (por ejemplo) ande también desde el celular vía Tailscale, ese Split DNS es el camino, simplemente no está activado hoy.

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
