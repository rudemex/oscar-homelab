---
title: Instalar Home Assistant
sidebar_position: 4
---

# Home Assistant paso a paso

La forma final depende de dónde se aloje:

- **Home Assistant OS en VM**: experiencia completa y aislada;
- **Raspberry Pi 5**: futuro equipo dedicado;
- contenedor: válido, pero algunas capacidades/add-ons difieren.

Para O.S.C.A.R. preferimos HA OS en VM o Pi dedicada cuando se busque un servicio doméstico estable.

## VM conceptual

1. descargar imagen oficial compatible;
2. importar/crear VM según guía vigente;
3. asignar 2 vCPU y 2–4 GB RAM iniciales;
4. NIC en red IoT/servers según diseño;
5. arrancar;
6. acceder a onboarding;
7. crear usuario;
8. configurar backup.

## Integración del rack

Primeras entidades útiles:

- sensor de temperatura;
- estado UPS;
- disponibilidad de hosts;
- MQTT;
- consumo eléctrico si existe medidor.

## Primera automatización segura

Solo notificación por temperatura. No apagar hardware automáticamente hasta validar meses de lecturas y umbrales.

## Backup

Crear backup nativo y copiarlo fuera de la instancia. Probar restore antes de incorporar automatizaciones domésticas importantes.
