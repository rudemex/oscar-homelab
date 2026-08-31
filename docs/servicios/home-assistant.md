---
title: Home Assistant
sidebar_position: 13
---

# Home Assistant

**Estado:** Objetivo · Hogar  
**Dónde corre:** Raspberry Pi 5 futura o VM dedicada  
**Sizing inicial:** 2 vCPU/2–4 GB RAM típico inicial; depende de integraciones  
**Red/puertos:** 8123 interno; acceso remoto protegido  
**Persistencia:** configuración, DB, add-ons e integraciones

## Rol dentro de O.S.C.A.R.

- automatización doméstica
- sensores del rack
- UPS/energía
- CCTV/RTSP si aplica
- alertas de temperatura

## Ejemplo concreto

Automatización: si temperatura del rack supera umbral, encender ventilación y notificar; si sigue subiendo, alertar criticidad.

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

Separar automatizaciones domésticas críticas de experimentos de IA no supervisados.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El estado vive en el directorio `/config`: `configuration.yaml`, automations, scripts, y el registro de entidades/dispositivos en `.storage/*.json`, más el histórico en `home-assistant_v2.db` (SQLite por defecto, suficiente a esta escala).

Home Assistant trae un mecanismo de backup nativo (Settings → System → Backups) que genera un `.tar` con todo `/config` de forma consistente sin detener el servicio. Ese archivo debe copiarse fuera del host — no alcanza con que quede en el mismo disco.

Restore: subir el `.tar` a una instancia nueva desde el propio asistente de restore de HA, o restaurar manualmente el volumen `/config` y reiniciar.

Si en el futuro se agregan integraciones con estado externo (cámaras RTSP, MQTT), esas integraciones se reconfiguran solas al restaurar `/config`; no hace falta backup aparte.

## Observabilidad

- entidades marcadas `unavailable` (indica integración o dispositivo caído);
- automatizaciones fallidas en el logbook;
- disponibilidad HTTP del panel (puerto 8123);
- consumo de CPU/RAM y tamaño de `home-assistant_v2.db`;
- reinicios del proceso/contenedor.

## Troubleshooting

- **Una integración marca `unavailable`** → dispositivo offline en la VLAN IOT, o token/credencial expirado → verificar conectividad de red hacia el dispositivo, revisar logs de la integración específica.
- **Una automatización no dispara** → condición mal definida o entidad trigger renombrada → revisar el trace de la automatización en Settings → Automations, validar el `entity_id` usado.
- **El panel no responde pero el contenedor está `Up`** → proceso colgado o `home-assistant_v2.db` corrupta/bloqueada → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), revisar logs de arranque.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://www.home-assistant.io/docs/
