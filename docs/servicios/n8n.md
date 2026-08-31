---
title: n8n
sidebar_position: 12
---

# n8n

**Estado:** Objetivo · Automatización  
**Dónde corre:** Docker Core o VM dedicada cuando crezca  
**Sizing inicial:** 2 vCPU, 2–4 GB RAM inicial + PostgreSQL para uso serio  
**Red/puertos:** UI interna; webhooks publicados selectivamente  
**Persistencia:** database, encryption key, workflows y credenciales

## Rol dentro de O.S.C.A.R.

- backups coordinados
- notificaciones de alertas
- inventario automático
- workflows de IA
- integraciones GitHub/GitLab/Home Assistant

## Ejemplo concreto

Workflow: Alertmanager → webhook n8n → obtener contexto de Prometheus → enviar resumen con host, métrica y runbook asociado.

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

La encryption key de n8n es crítica para recuperar credenciales cifradas. Debe respaldarse fuera del contenedor.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Hay que respaldar tres cosas: la base PostgreSQL (workflows, ejecuciones, credenciales cifradas), la encryption key (sin ella las credenciales cifradas son irrecuperables) y la configuración Compose. El procedimiento completo, incluyendo el dump de PostgreSQL paso a paso y un restore drill de 8 pasos, está documentado en [Backup de n8n](../backup-dr/backup-n8n.md); no se duplica acá.

## Observabilidad

- disponibilidad HTTP/webhook;
- ejecuciones de workflow fallidas (n8n las loguea en la UI de Executions);
- conexión a PostgreSQL;
- consumo de CPU/RAM del contenedor;
- reinicios del proceso/contenedor.

## Troubleshooting

- **Un workflow no dispara** → credencial expirada, por ejemplo tras una rotación mal hecha de la encryption key, o webhook mal registrado → revisar ejecuciones fallidas en la UI, verificar que la encryption key no haya cambiado; ver [Rotar un secreto](../runbooks/rotacion-secreto.md) si se sospecha de eso.
- **La UI no responde pero el contenedor está `Up`** → PostgreSQL inaccesible o saturado → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), revisar logs de conexión a la DB.
- **Un webhook público no llega** → ruta no publicada correctamente por el Cloudflare Tunnel, o workflow inactivo → revisar el mapeo de ingress del túnel, confirmar que el workflow esté activado.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://docs.n8n.io/
