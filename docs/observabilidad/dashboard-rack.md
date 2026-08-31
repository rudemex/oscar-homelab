---
title: Dashboard de la pantalla 9"
sidebar_position: 3
---

# O.S.C.A.R. Control Center

La pantalla 1280×720 del rack debe mostrar **estado**, no un dashboard que obligue a leer texto diminuto.

## Layout sugerido

```text
┌──────────────────────────────────────────────────────────────┐
│ O.S.C.A.R.                    WAN ●     DNS ●    20:42       │
├───────────────────┬───────────────────┬──────────────────────┤
│ PVE01             │ STORAGE           │ TEMPERATURE          │
│ CPU 22%           │ M2  48%           │ Dell 47°C            │
│ RAM 61%           │ SSD 31%           │ Rack 31°C            │
├───────────────────┼───────────────────┼──────────────────────┤
│ SERVICES          │ NETWORK           │ BACKUP               │
│ 14/14 healthy     │ ↓ 38M ↑ 12M      │ Last ✓ 02:10         │
│ k3s 1/1           │ latency 19ms      │ Restore test ✓       │
├───────────────────┼───────────────────┴──────────────────────┤
│ UPS               │ CCTV                                    │
│ 97% · on-line     │ 4/4 cámaras online                      │
└───────────────────┴──────────────────────────────────────────┘
```

El panel UPS y el panel CCTV solo tienen sentido una vez que exista un UPS ([pendiente de decisión](../../inventory/hardware.yaml)) y el DVR Dahua esté conectado a la red de monitoreo; hasta entonces el dashboard puede mostrar esas dos filas en gris "no disponible" en vez de omitirlas, para dejar explícito que son componentes previstos y no descartados.

## Reglas de UX

- verde/normal no debe dominar la pantalla;
- errores deben ser obvios;
- no más de 8 paneles principales (el layout de arriba usa 8: PVE01, storage, temperatura, servicios, red, backup, UPS, CCTV);
- tipografía legible a distancia;
- refresh moderado;
- sin credenciales ni datos sensibles.
