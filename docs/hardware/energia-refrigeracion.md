---
title: Energía y refrigeración
sidebar_position: 5
---

# Energía y refrigeración

## Objetivos

- evitar apagados abruptos;
- conocer autonomía real;
- evitar puntos calientes;
- poder apagar cargas no críticas antes que las críticas.

## UPS

El UPS y un estabilizador de tensión [ya existen físicamente](../../inventory/hardware.yaml), pero están fuera del rack y sin conectar — esta sección describe cómo deben quedar integrados, no una compra pendiente. Ver [Fase 1 del roadmap](../roadmap/roadmap-general.md#fase-1--rack-red-y-energía).

La UPS debe alimentar, prioritariamente:

1. ONT;
2. firewall/router;
3. switch;
4. host Proxmox;
5. almacenamiento necesario para shutdown limpio.

Pantallas decorativas o cargas prescindibles pueden quedar fuera si reducen demasiado la autonomía.

## Shutdown ordenado

Objetivo futuro:

```mermaid
flowchart LR
  UPS[UPS batería baja] --> MON[Monitor UPS/NUT]
  MON --> VM[Shutdown VMs]
  VM --> PVE[Shutdown Proxmox]
  PVE --> NAS[Verificar NAS/otros]
```

## Temperatura

Registrar al menos:

- CPU del Dell;
- temperatura de SSD/NVMe si está disponible;
- temperatura interna del rack;
- temperatura ambiente.

La observación vale más que una regla fija: registrar baseline en reposo y bajo carga, y alertar por desviaciones.
