---
title: Inventario actual
sidebar_position: 1
---

# Inventario de hardware

Este documento representa el inventario conocido y debe mantenerse alineado con `inventory/hardware.yaml`.

:::note Esto es lo que tengo yo, no lo que hace falta tener
Este es mi inventario real, no una lista de compras. Parte de él está acá por conveniencia personal, no porque la arquitectura de O.S.C.A.R. lo requiera — el caso más claro es el DVR: lo tengo desde antes del proyecto y lo integro al rack para no dejarlo suelto, no porque CCTV sea parte de un homelab mínimo. Para dimensionar tu propio hardware (con otras marcas/modelos), usá [requisitos mínimos](../referencia/requisitos-minimos.md) en vez de replicar esta lista.
:::

## Rack

- GeeekPi RackMate T2, formato 10", 12U.
- Pantalla GeeekPi touch 9", 1280×720, 3U.
- Patch panel CAT6 12 puertos, 0.5U.
- Paneles de gestión de cableado con cepillo.
- Bandejas/estantes RackMate.
- Paneles de ventilación.

## Cómputo principal

### Dell OptiPlex 7060 Micro

- CPU: Intel Core i7 de 8ª generación.
- RAM actual: 16 GB DDR4, con capacidad de ampliación según configuración física.
- M.2: 512 GB.
- SSD SATA: 1 TB.
- Rol objetivo: host Proxmox principal.

### Raspberry Pi

- 2 × Raspberry Pi 3.
- 3 × Raspberry Pi Zero W.
- 2 × Pi Zero con adaptador USB de 4 puertos.
- Pi 5 8 GB: planificada para expansión.

## Red

- Router/mesh: TP-Link Archer AX55.
- Switch actual: TP-Link TL-SF1008D 8 puertos 10/100, marcado para reemplazo.
- ONT de fibra.

## CCTV

- DVR Dahua 4 canales.
- Dimensiones del DVR: 197 × 192 × 41 mm.
- Proyecto de bandeja para rack y balunera de 4 canales.

## Periféricos y energía

- KVM 2×2 para dos PCs y dos monitores.
- UPS y estabilizador fuera del rack.

## Inventario pendiente de cerrar

- modelo final del switch gestionable >8 puertos;
- hardware de firewall OPNsense;
- ampliación definitiva de RAM del Dell;
- NAS y discos;
- Pi 5 y NVMe;
- medición real de consumo eléctrico y térmico.
