---
title: Migración a red segmentada
sidebar_position: 7
---

# Migración gradual de red

No migramos router, VLAN, Wi-Fi y DNS todos el mismo día.

## Estado A · Red actual

```text
ONT -> Archer AX55 -> switch -> dispositivos
```

Documentar:

```bash
ipconfig /all        # Windows
ip addr; ip route    # Linux
```

Registrar gateway, DHCP range, DNS y subred.

## Estado B · Switch gestionable

Reemplazar el switch 100 Mbps manteniendo **una sola LAN**. Validar primero gigabit y estabilidad.

Gate:

- Dell negocia 1 Gbps;
- cableado estable;
- no se introdujo VLAN todavía.

## Estado C · OPNsense de laboratorio

Conectar OPNsense a una LAN de prueba sin desplazar el router principal. Practicar:

- WAN/LAN;
- DHCP;
- reglas;
- backup/restore de config.

## Estado D · OPNsense gateway

Ventana de cambio:

1. exportar configuraciones actuales;
2. preparar OPNsense offline;
3. mover WAN;
4. conectar LAN al switch;
5. validar cliente cableado;
6. validar DNS;
7. validar Wi-Fi;
8. rollback si el gateway no funciona.

## Estado E · VLAN una por una

Orden sugerido:

1. GUEST;
2. CCTV;
3. IoT;
4. LAB;
5. SERVERS/MGMT.

Mover primero redes con menor blast radius. Nunca migrar administración del firewall y del Proxmox a una VLAN nueva sin una ruta de acceso alternativa.
