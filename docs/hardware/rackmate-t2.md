---
title: RackMate T2 y layout
sidebar_position: 4
---

# RackMate T2 12U

El rack es de 10" y 12U. El diseño físico debe priorizar mantenimiento, ventilación y rutas de cable claras por encima de llenar cada U.

## Layout frontal de referencia

```text
U12 ┌──────────────────────────────┐
    │ Pantalla touch           3U │
U10 └──────────────────────────────┘
U9.5│ Patch panel CAT6       0.5U │
U9  │ Switch                  1U │
U8  │ Gestión / shelf         1U │
U7  │ Dell OptiPlex           1U │
U6  │ DVR / bandeja           1U │
U5  │ Raspberry / shelf       1U │
U3  │ Ventilación             2U │
U1  │ Reserva / expansión     1U │
```

Suma: 3 + 0.5 + 1 + 1 + 1 + 1 + 1 + 2 + 1 = **11.5U** sobre un rack de **12U**, dejando 0.5U libre para gestión de cable — no conviene ocupar el 100% del rack desde el diseño inicial. Este dibujo es conceptual. El tamaño real del switch, bandeja DVR, conectores traseros y radios de curvatura puede exigir mover componentes.

## Reglas físicas

- patch panel cerca del switch;
- patch cords cortos y visibles;
- equipos calientes con espacio de respiración;
- entrada de aire limpia y salida no obstruida;
- evitar tensión sobre HDMI, USB, alimentación y RJ45;
- dejar servicio suficiente para retirar una bandeja sin desarmar todo el rack;
- etiquetar ambos extremos de cada cable.

## Cableado

Convención sugerida:

```text
PP01 -> SW01/01 -> Oficina
PP02 -> SW01/02 -> DVR
PP03 -> SW01/03 -> PVE01
...
```

La etiqueta expresa la relación física; la VLAN expresa la relación lógica.
