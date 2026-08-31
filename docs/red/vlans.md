---
title: VLAN y segmentación
sidebar_position: 2
---

# VLAN y segmentación

Las VLAN no se agregan para hacer el diagrama más complejo; se agregan cuando permiten expresar una política de confianza.

## Matriz objetivo simplificada

| Origen | Destino | Regla general |
|---|---|---|
| MGMT | todos | permitido administrativamente |
| CLIENTS | SERVERS | solo servicios publicados |
| IOT | CLIENTS | denegado por defecto |
| IOT | Internet | permitido según necesidad |
| CCTV | Internet | denegado salvo requisito explícito |
| CCTV | NVR/HA | permitido selectivamente |
| GUEST | LAN | denegado |
| LAB | producción | denegado por defecto |

```mermaid
flowchart LR
  MGMT((MGMT))
  SERVERS((SERVERS))
  CLIENTS((CLIENTS))
  IOT((IOT))
  CCTV((CCTV))
  GUEST((GUEST))
  LAB((LAB))
  WAN((Internet))

  MGMT -->|admin| SERVERS
  MGMT -->|admin| CLIENTS
  MGMT -->|admin| IOT
  MGMT -->|admin| CCTV
  CLIENTS -->|solo publicados| SERVERS
  IOT -.->|denegado| CLIENTS
  IOT -->|según necesidad| WAN
  CCTV -->|selectivo| SERVERS
  CCTV -.->|denegado salvo excepción| WAN
  GUEST -.->|denegado| SERVERS
  LAB -.->|denegado por defecto| SERVERS

  linkStyle 5,8,9,10 stroke:#c0392b,stroke-dasharray:4 3
```

Flechas sólidas = permitido; punteadas rojas = denegado por defecto. El diagrama es una simplificación de la tabla de arriba — la tabla manda si hay diferencia.

## Cuándo implementarlas

Se requieren tres piezas coherentes:

1. firewall/router que entienda 802.1Q;
2. switch gestionable con VLAN;
3. AP capaz de mapear SSID a VLAN si queremos segmentación Wi-Fi.

Si falta una de estas piezas, documentar el diseño pero no crear una segmentación a medias que después sea difícil de diagnosticar.

## Trunk vs access

- **access/untagged**: dispositivo final que pertenece a una VLAN;
- **trunk/tagged**: enlace que transporta varias VLAN, por ejemplo firewall ↔ switch o switch ↔ host Proxmox.

## Proxmox

El bridge de Proxmox puede ser VLAN-aware para entregar redes diferentes a distintas VMs. Esto permite mantener un solo enlace físico si la NIC y el switch lo soportan.
