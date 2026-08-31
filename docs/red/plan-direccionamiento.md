---
title: Plan de direccionamiento
sidebar_position: 1
---

# Plan de direccionamiento

El direccionamiento definitivo debe cerrarse **antes** de crear decenas de IP estáticas.

## Principios

- gateways con `.1`;
- infraestructura en rango bajo reservado;
- DHCP para clientes;
- reservations DHCP para equipos conocidos cuando sea práctico;
- IP fija dentro del guest solo si el servicio realmente lo requiere;
- nombres DNS como interfaz habitual, no memorizar IPs.

## Ejemplo futuro con VLAN

| VLAN | Subred | Gateway | DHCP sugerido |
|---:|---|---|---|
| 10 MGMT | `192.168.10.0/24` | `.1` | `.100-.199` |
| 20 SERVERS | `192.168.20.0/24` | `.1` | limitado |
| 30 IOT | `192.168.30.0/24` | `.1` | `.100-.240` |
| 40 CCTV | `192.168.40.0/24` | `.1` | reservations |
| 50 CLIENTS | `192.168.50.0/24` | `.1` | `.100-.240` |
| 60 GUEST | `192.168.60.0/24` | `.1` | dinámico |
| 70 LAB | `192.168.70.0/24` | `.1` | dinámico |

## Naming DNS

Ejemplos:

```text
pve01.oscar.home
sw01.oscar.home
grafana.oscar.home
n8n.oscar.home
argocd.oscar.home
ha.oscar.home
```

Evitar usar `.local` como dominio propio por posibles conflictos con mDNS. El dominio interno exacto se decide antes de producción.
