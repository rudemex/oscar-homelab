---
title: Métricas de hosts
sidebar_position: 2
---

# Métricas de infraestructura

## Dell/VMs

- CPU usage/load;
- RAM/swap;
- filesystem;
- I/O y latencia;
- network throughput/errors;
- uptime;
- temperatura si el sensor es accesible.

## Raspberry

Además:

- throttling;
- temperatura;
- Wi-Fi RSSI si aplica;
- undervoltage;
- microSD filesystem.

## Alertas iniciales

Evitar 50 alertas el primer día. Empezar con pocas y accionables:

- host down;
- filesystem > 85%;
- backup fallido;
- DNS sin responder;
- temperatura anormal sostenida;
- UPS en batería/batería baja.
