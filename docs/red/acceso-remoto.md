---
title: Acceso remoto
sidebar_position: 5
---

# Acceso remoto

El objetivo es administrar O.S.C.A.R. sin publicar paneles directamente en Internet.

## Opciones

### VPN

Adecuada para acceso administrativo completo a redes internas. Puede implementarse en OPNsense o mediante una solución overlay.

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
