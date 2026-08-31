---
title: Firewall y OPNsense
sidebar_position: 3
---

# Firewall con OPNsense

OPNsense forma parte de la arquitectura objetivo como firewall dedicado. No es requisito para empezar con Proxmox.

## Por qué dedicar hardware

Si el firewall corre dentro del único host Proxmox, reiniciar el host corta Internet y complica la recuperación remota. Un appliance N100 dedicado evita esa dependencia.

## Funciones previstas

- gateway WAN;
- reglas inter-VLAN;
- DHCP;
- DNS forwarding/resolution según arquitectura final;
- VPN;
- métricas;
- aliases y grupos de hosts;
- eventualmente IDS/IPS si el hardware y el caso de uso lo justifican.

## Estrategia de migración

1. documentar red actual;
2. instalar OPNsense sin tocar producción;
3. configurar WAN/LAN de prueba;
4. exportar backup de configuración;
5. migrar gateway en una ventana controlada;
6. validar Internet, DNS y Wi-Fi;
7. recién después crear VLAN adicionales.

## Regla de firewall

Las reglas deben describirse por intención:

```text
ALLOW clients -> grafana TCP/3000
ALLOW home-assistant -> iot MQTT/1883
DENY cctv -> internet any
```

No usar reglas `any/any` permanentes para resolver problemas temporales.
