---
title: Raspberry Pi
sidebar_position: 3
---

# Raspberry Pi en O.S.C.A.R.

Las Raspberry Pi no compiten con el Dell: complementan la arquitectura.

## Raspberry Pi 3

Casos de uso ideales:

- Pi-hole secundario;
- Home Assistant en instalación pequeña;
- Prometheus exporters;
- Internet-Pi;
- nodo ARM de laboratorio;
- servidor NTP/DNS de contingencia;
- bridge MQTT.

## Raspberry Pi Zero W

Casos de uso:

- sensores;
- telemetría;
- scripts de red;
- display/control auxiliar;
- probes de disponibilidad desde otro punto de la casa;
- pequeñas integraciones GPIO.

No se recomienda usarlas para bases de datos intensivas, builds o almacenamiento pesado.

## Raspberry Pi 5 futura

Con NVMe puede asumir cargas que requieren I/O más confiable que una microSD:

- Home Assistant;
- Docker ARM;
- nodo k3s adicional;
- servicios edge;
- herramientas de red;
- pequeñas cargas de IA/visión compatibles con su capacidad.

## microSD vs SSD/NVMe

La microSD es aceptable para boot, sensores y servicios descartables. Para bases de datos o escrituras frecuentes conviene SSD/NVMe cuando el hardware lo permita.

## Laboratorio sugerido

Convertir una Pi Zero en **probe remota**:

1. instalar un exporter pequeño o script Python;
2. medir ping/DNS/HTTP cada minuto;
3. enviar métricas a Prometheus;
4. mostrar en Grafana si el problema está en Internet, Wi-Fi o en el servidor.
