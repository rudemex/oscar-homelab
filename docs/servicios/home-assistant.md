---
title: Home Assistant
sidebar_position: 13
---

# Home Assistant

**Estado:** Actual · Hogar — **VM 106 (`haos-18.3`)** en `oscar-core`, rehecha desde cero el 2026-09-21 (la VM 101 `haos-18.2` se perdió con el SSD SATA de `Backups`, ver [incidente](../arquitectura/estado-actual.md)). Sin configurar todavía: entra el asistente de bienvenida en `http://192.168.0.198:8123`. **IP provisoria**: se reutilizó la MAC de la VM vieja (`02:DC:F8:B9:49:3F`) pero el router asignó `.198` y no la `.195` de antes; Homepage, el hostname `ha.oscarlab.com.ar` del túnel de Cloudflare y el monitor de Kuma siguen apuntando a `.195`. Solución: fijar `192.168.0.195` en Ajustes → Sistema → Red de Home Assistant, o reservar la IP en el router  
**Dónde corre:** VM dedicada en `oscar-core` (no Raspberry Pi todavía — ver [estado actual](../arquitectura/estado-actual.md))  
**Sizing inicial:** 2 vCPU/2–4 GB RAM típico inicial; depende de integraciones  
**Red/puertos:** **puerto 80** interno (no el 8123 típico de otras instalaciones — esta instancia quedó configurada distinto); acceso real vía [Cloudflare Tunnel](./cloudflare-tunnel.md) en `ha.oscarlab.com.ar`  
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
- disponibilidad HTTP del panel (puerto 80 en esta instancia — ver nota arriba);
- consumo de CPU/RAM y tamaño de `home-assistant_v2.db`;
- reinicios del proceso/contenedor.

## Configuración necesaria para el Tunnel

Home Assistant rechaza por defecto cualquier request que declare venir de un proxy (trae headers `X-Forwarded-For`/`X-Forwarded-Proto`, como hace `cloudflared`) si el origen no está en una lista de proxies de confianza — sin esto, `ha.oscarlab.com.ar` daba `400: Bad Request` aunque el túnel y Access estaban perfectamente sanos.

**Ojo con la versión:** en Home Assistant **2026.8+**, esto ya no se configura en `configuration.yaml` — un bloque `http: trusted_proxies: [...]` ahí se ignora en silencio, sin error, lo que hace parecer que "no hizo nada" (así fue acá: quedó bien escrito, pasó `ha core check`, y el 400 siguió igual). El lugar real es la UI:

**Configuración → Sistema → Red → Servidor HTTP → Proxies de confianza** → agregar `192.168.0.156` (`core`, donde corre `cloudflared` con `network_mode: host`).

Si en algún momento se migra a una instalación más vieja que no tenga ese panel en Red, ahí sí correspondería el bloque YAML de arriba — confirmar la versión antes de asumir cuál de los dos caminos aplica.

## Troubleshooting

- **Una integración marca `unavailable`** → dispositivo offline en la VLAN IOT, o token/credencial expirado → verificar conectividad de red hacia el dispositivo, revisar logs de la integración específica.
- **Una automatización no dispara** → condición mal definida o entidad trigger renombrada → revisar el trace de la automatización en Settings → Automations, validar el `entity_id` usado.
- **El panel no responde pero el contenedor está `Up`** → proceso colgado o `home-assistant_v2.db` corrupta/bloqueada → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), revisar logs de arranque.
- **`400: Bad Request` entrando por `ha.oscarlab.com.ar`, pero por LAN funciona bien** → falta el proxy de confianza — ver "Configuración necesaria para el Tunnel" arriba. El log (`docker logs homeassistant`) lo confirma con `A request from a reverse proxy was received from <IP>, but your HTTP integration is not set-up for reverse proxies`.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://www.home-assistant.io/docs/
