---
title: Home Assistant
sidebar_position: 1
---

# Home Assistant

Home Assistant conecta el homelab con sensores y automatizaciones domésticas.

## Casos O.S.C.A.R.

- temperatura del rack;
- consumo/estado UPS si hay integración;
- presencia/estado de dispositivos;
- cámaras/RTSP cuando sea compatible;
- control de ventilación;
- notificaciones.

## Ejemplo de automatización

```text
SI rack_temperature > warning durante 5 min
  -> notificar
SI rack_temperature > critical durante 3 min
  -> encender ventilación máxima
  -> notificar crítico
```

La acción de apagar servidores automáticamente por temperatura se evalúa recién después de validar sensores, falsos positivos y procedimiento seguro.
