---
title: Topología lógica
sidebar_position: 4
---

# Topología lógica objetivo

La siguiente topología representa el estado objetivo, no obliga a disponer de todos los componentes desde el día uno.

```mermaid
flowchart LR
  INTERNET((Internet)) --> ONT[ONT fibra]
  ONT --> FW[Firewall / OPNsense]
  FW --> SW[Switch gestionable]
  SW --> AP[Wi-Fi / Archer AX55]
  SW --> PVE[Dell / Proxmox]
  SW --> PI[Raspberry Pi]
  SW --> DVR[DVR Dahua]
  SW --> CLIENTS[Clientes cableados]
  PVE --> VM1[VM Core]
  PVE --> VM2[VM DevOps]
  PVE --> VM3[VM k3s]
```

## Etapa 1 · sin firewall dedicado (estado actual)

Mientras OPNsense no exista, el Archer AX55 sigue siendo gateway y no hay segmentación: todo comparte una sola red plana. La documentación debe permitir una transición ordenada en lugar de forzar una migración prematura.

```mermaid
flowchart LR
  INTERNET((Internet)) --> ONT[ONT fibra]
  ONT --> AX55[Archer AX55<br/>gateway + Wi-Fi]
  AX55 --> SW[Switch no gestionado]
  SW --> PVE[Dell / futuro Proxmox]
  SW --> PI[Raspberry Pi]
  SW --> CLIENTS[Clientes cableados/Wi-Fi]

  classDef flat fill:#3b3,stroke:#333,color:#fff;
  class AX55,SW flat
```

Una sola red significa que todo puede hablarle a todo — es el estado real hoy, no un diseño recomendado.

## Etapa 2 · con OPNsense y VLANs (objetivo)

```mermaid
flowchart LR
  INTERNET((Internet)) --> ONT[ONT fibra]
  ONT --> FW[OPNsense]
  FW -->|trunk 802.1Q| SW[Switch gestionable]
  SW -->|VLAN 10 MGMT| PVE[Dell / Proxmox]
  SW -->|VLAN 20 SERVERS| VMS[VMs / servicios]
  SW -->|VLAN 30 IOT| PI[Raspberry Pi / sensores]
  SW -->|VLAN 40 CCTV| DVR[DVR Dahua]
  SW -->|VLAN 50 CLIENTS| CLIENTS[PCs / móviles]
  AX55[Archer AX55] -.rol AP/mesh.-> SW

  classDef target fill:#26538d,stroke:#333,color:#fff;
  class FW,SW target
```

La viabilidad exacta del modo AP/mesh de los AX55 (como puntos de acceso puros, sin routing propio) debe validarse con su configuración final — no todos los routers de consumo soportan bien un modo "solo AP" con VLANs tageadas.

## Separación lógica objetivo

Un esquema simple de VLAN de referencia:

| VLAN | Nombre | Ejemplo | Uso |
|---:|---|---|---|
| 10 | MGMT | `192.168.10.0/24` | Proxmox, switch, firewall |
| 20 | SERVERS | `192.168.20.0/24` | VMs y servicios |
| 30 | IOT | `192.168.30.0/24` | IoT/Home Assistant |
| 40 | CCTV | `192.168.40.0/24` | DVR/cámaras |
| 50 | CLIENTS | `192.168.50.0/24` | PCs y móviles |
| 60 | GUEST | `192.168.60.0/24` | invitados |
| 70 | LAB | `192.168.70.0/24` | pruebas destructivas |

:::note
Estas subredes son un diseño de referencia. Antes de aplicarlas se debe revisar la red doméstica actual para evitar solapamientos.
:::
