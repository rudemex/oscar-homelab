---
title: Cableado y patch panel
sidebar_position: 6
---

# Cableado y patch panel

La capa física debe poder entenderse mirando el rack.

## Flujo

```text
Toma / equipo
   ↓
Patch panel
   ↓ patch cord corto
Switch
   ↓
VLAN / servicio
```

## Etiquetado

Usar un identificador estable en ambos extremos:

```text
C01 - Oficina escritorio
C02 - DVR
C03 - AP habitación
C04 - PVE01
```

Mantener una tabla en el inventario:

| Patch | Switch | Destino | VLAN | Velocidad |
|---|---|---|---|---|
| PP01 | SW01-01 | PVE01 | trunk | 1G |
| PP02 | SW01-02 | DVR01 | CCTV | 1G |

## Pruebas

Después de terminar una boca:

1. link up;
2. velocidad negociada correcta;
3. DHCP/DNS;
4. ping gateway;
5. transferencia real si corresponde;
6. registrar puerto.

Un enlace que negocia a 100 Mbps en una red gigabit merece revisión de cable/terminación antes de culpar al software.
