---
title: Eclipse Mosquitto MQTT
sidebar_position: 15
---

# Eclipse Mosquitto MQTT

**Estado:** Laboratorio / Hogar  
**Dónde corre:** Raspberry Pi o VM Core  
**Sizing inicial:** muy bajo para uso doméstico  
**Red/puertos:** 1883/8883 según TLS  
**Persistencia:** configuración, passwords/certs y persistencia si se usa

## Rol dentro de O.S.C.A.R.

- sensores Pi Zero
- Home Assistant
- telemetría ambiental
- eventos del rack

## Ejemplo concreto

Pi Zero publica `oscar/rack/temperature`; Home Assistant y un exporter consumen el tópico.

## Checklist de despliegue

- [ ] hostname y ubicación decididos;
- [ ] imagen/versión fijada, evitando tags flotantes en servicios importantes;
- [ ] puertos documentados;
- [ ] volumen/persistencia definida;
- [ ] `.env.example` sin secretos en Git;
- [ ] credenciales reales fuera de Git;
- [ ] backup definido antes de cargar datos importantes;
- [ ] healthcheck o monitor de disponibilidad;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado.

## Seguridad

No permitir anonymous publish en una red no confiable. Definir ACL por tópico para dispositivos.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Con `persistence true`, Mosquitto guarda mensajes retenidos y suscripciones en `mosquitto.db`, pero es estado de bajo valor: los dispositivos IoT vuelven a publicar su último estado al reconectarse.

No vale la pena backup dedicado. Si se pierde `mosquitto.db`, el broker arranca vacío y se repuebla solo en minutos a medida que los dispositivos reportan.

## Observabilidad

Laboratorio/hogar de bajo valor operativo: no se justifica alertar ni definir SLO. Alcanza con verificar manualmente que el contenedor esté arriba y que los dispositivos estén publicando (por ejemplo, suscribiéndose a `#` con `mosquitto_sub`).

## Troubleshooting

**Un dispositivo no puede conectar** → ACL/usuario mal configurado, o puerto bloqueado entre VLANs → revisar `mosquitto.conf` y las reglas de firewall entre la VLAN IOT y donde corre el broker.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://mosquitto.org/documentation/
