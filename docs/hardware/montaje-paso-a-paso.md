---
title: Montaje físico paso a paso
sidebar_position: 6
---

# Montaje físico del rack

Esta secuencia reduce retrabajo y evita cablear definitivamente antes de comprobar espacio, ventilación y conectores.

## 1. Preparar la mesa

Antes de atornillar:

- inventariar tornillos, bandejas y paneles;
- medir profundidad útil;
- ubicar tomas de energía;
- verificar que HDMI/USB/Ethernet de la pantalla alcancen sin tensión;
- presentar el DVR con sus conectores puestos, no solo su carcasa.

## 2. Montaje en seco

Instalar componentes **sin cableado final** en el orden aproximado:

1. pantalla;
2. patch panel;
3. switch;
4. bandeja Dell;
5. bandeja DVR;
6. Raspberry;
7. ventilación/gestión.

Cerrar/abrir cualquier tapa y verificar que cada equipo pueda retirarse.

## 3. Energía

Separar ruta de alimentación y datos cuando sea práctico. Etiquetar fuentes:

```text
PWR-PVE01
PWR-SW01
PWR-DVR01
PWR-LCD01
```

No dejar fuentes pesadas colgando de sus conectores.

## 4. Patch panel

Conectar las bajadas externas al patch panel y testear cada boca antes de poner patch cord.

Registro mínimo:

```text
PP01 -> escritorio
PP02 -> DVR/cámaras
PP03 -> uplink habitación
```

## 5. Patch cords

Patch panel → switch con cables cortos, evitando bucles excesivos. El objetivo es que se vea físicamente qué puerto corresponde a qué patch.

## 6. Prueba térmica

Con el rack armado:

1. medir temperatura ambiente;
2. encender switch/Dell/DVR;
3. dejar estabilizar;
4. registrar temperatura idle;
5. correr carga CPU/IO moderada;
6. registrar temperatura bajo carga;
7. decidir velocidad/posición de ventiladores con datos.

## 7. Foto baseline

Tomar fotos frontal/trasera y guardarlas como referencia de cableado. Actualizarlas después de cambios grandes.
