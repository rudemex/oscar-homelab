---
title: Loki
sidebar_position: 10
---

# Loki

**Estado:** Objetivo · Logs  
**Dónde corre:** VM observabilidad o k3s  
**Sizing inicial:** 2+ GB RAM inicial; storage y retención a medir  
**Red/puertos:** API interna  
**Persistencia:** chunks/index de logs

## Rol dentro de O.S.C.A.R.

- logs de contenedores
- logs de k3s
- correlacionar error de app con reinicios
- buscar incidentes por servicio

## Ejemplo concreto

Desde Grafana: filtrar todos los logs de `n8n` durante los cinco minutos alrededor de una alerta.

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

No ingerir logs sin límites. Definir retención, labels de baja cardinalidad y exclusiones.

Evitar loguear secretos o credenciales en texto plano hacia Loki; los logs quedan indexados y accesibles desde Grafana Explore a cualquiera con acceso al datasource.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Mismo criterio que Prometheus: los logs en el filesystem local (chunks) son datos operativos con retención definida, no un archivo maestro irreemplazable. Si el volumen se destruye se pierden los logs viejos, pero el servicio se reconstruye solo. La configuración (`loki-config.yaml`) vive en Git.

Si en el futuro se necesita retención larga de logs por auditoría o compliance, la decisión pendiente es mover el backend de chunks a un object storage (MinIO/S3) y respaldar ese bucket en vez del disco local — esto es una decisión futura, no algo ya resuelto.

## Observabilidad

- endpoint `/ready`;
- tasa de errores de ingestión;
- fallos de flush de chunks a disco;
- uso de disco del volumen de chunks;
- reinicios del contenedor.

## Troubleshooting

- **Logs no aparecen en Grafana Explore** → Promtail/agente no está enviando, o hay mismatch de labels entre la query y los logs → revisar logs del agente de recolección, verificar labels con `{job="..."}` en Explore.
- **Ingesta rechazada con error de rate limit** → volumen de logs supera los límites configurados (`ingestion_rate_mb`, `ingestion_burst_size_mb`) → revisar qué servicio está generando el pico y ajustar límites o filtrar en origen.
- **Loki no arranca / `/ready` no responde** → chunks corruptos o disco lleno en el volumen de persistencia → revisar espacio en disco y logs de arranque. Ver [`disco-lleno.md`](../runbooks/disco-lleno.md) y [`docker-servicio-caido.md`](../runbooks/docker-servicio-caido.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://grafana.com/docs/loki/
