---
title: Cloudflare Tunnel + Access
sidebar_position: 14
---

# Cloudflare Tunnel + Access

**Estado:** Objetivo · Acceso remoto  
**Dónde corre:** VM Core o nodo dedicado de conectividad  
**Sizing inicial:** muy bajo para túnel; depende de tráfico  
**Red/puertos:** conexiones salientes; evita inbound port-forward para HTTP  
**Persistencia:** token/credenciales del túnel y configuración

## Rol dentro de O.S.C.A.R.

- publicar una demo web
- acceder a Grafana con identidad
- webhooks de n8n
- evitar abrir puertos del router

## Ejemplo concreto

`grafana.<dominio>` → Cloudflare Access (MFA) → Tunnel → reverse proxy/Grafana interno.

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

Tunnel no convierte automáticamente un servicio en privado. Agregar Access/políticas cuando el hostname no deba ser público.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El servicio en sí es prácticamente stateless. Lo único que hay que respaldar son dos archivos pequeños pero críticos:

- el JSON de credenciales del túnel (`<tunnel-id>.json`) — es un secreto, nunca en el mismo repo Git en texto plano, tratarlo como cualquier otro secreto;
- `config.yml` (reglas de ingress) — sí puede versionarse en Git si no contiene secretos.

Las políticas de Cloudflare Access (identidad, MFA, reglas de quién entra a qué) viven en el dashboard de Cloudflare, no en el host. Hoy no hay backup/export automatizado de esas políticas; queda pendiente resolver esto más adelante, por ejemplo exportándolas vía API/Terraform si se adopta IaC de Cloudflare.

Restore: recrear el túnel desde cero con `cloudflared tunnel create` es rápido si se pierden las credenciales (hay que volver a autorizar DNS). El riesgo real no es "perder el túnel" sino perder la definición de las políticas de Access sin tener dónde reconstruirlas rápido.

## Observabilidad

- estado de la conexión del daemon `cloudflared` (métricas locales en `/metrics`, o el dashboard de Cloudflare Zero Trust);
- latencia agregada reportada por Cloudflare;
- certificado/DNS del hostname público;
- reinicios del proceso/contenedor del daemon;
- logs de errores de conexión del túnel.

## Troubleshooting

- **El hostname público no responde pero el servicio local sí** → túnel caído o DNS mal apuntado en Cloudflare → `cloudflared tunnel info <tunnel>`, revisar logs del daemon; ver [DNS caído](../runbooks/dns-caido.md) si el problema es de resolución.
- **Cloudflare Access no pide autenticación (o rechaza a todos)** → política mal configurada o cambiada manualmente en el dashboard sin registro → revisar la política en Zero Trust → Access, comparar contra la última configuración conocida.
- **El daemon `cloudflared` reinicia en loop** → credenciales del túnel inválidas o revocadas → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), regenerar credenciales con `cloudflared tunnel create` si corresponde.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
