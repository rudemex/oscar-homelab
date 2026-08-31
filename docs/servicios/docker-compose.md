---
title: Docker y Docker Compose
sidebar_position: 2
---

# Docker y Docker Compose

**Estado:** Objetivo · Core  
**Dónde corre:** VM `core01` y, cuando convenga, VMs específicas  
**Sizing inicial:** 2 vCPU, 2–4 GB RAM de base; depende de workloads  
**Red/puertos:** Docker daemon no debe publicarse; aplicaciones usan sus propios puertos  
**Persistencia:** bind mounts/volúmenes bajo rutas documentadas

## Rol dentro de O.S.C.A.R.

- ejecutar n8n, Uptime Kuma, dashboards y utilidades
- desplegar APIs Node/NestJS y frontends
- levantar Postgres/Redis para laboratorios
- probar versiones de aplicaciones sin ensuciar el host

## Ejemplo concreto

```yaml
services:
  hello:
    image: traefik/whoami:v1.11.0
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:80"
```

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

No montar `/var/run/docker.sock` en contenedores salvo necesidad clara; equivale a conceder capacidades muy altas sobre el host.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Esta página describe la plataforma en general, no un servicio puntual; el backup se resuelve a nivel de convención, no por contenedor.

Los `compose.yaml` y `.env.example` de cada app ya viven en Git — eso ES su backup de configuración. Lo que realmente hace falta respaldar es el **estado en disco de cada stack**. Siguiendo la convención de [docker-host-baseline.md](./docker-host-baseline.md) (`/srv/oscar/apps/<app>/` y `/srv/oscar/data/<app>`), basta con respaldar ese árbol de directorios completo —por ejemplo con [Restic](./restic.md)— en vez de definir una estrategia distinta para cada contenedor.

El detalle fino (qué servicio necesita un dump de base de datos consistente en vez de una simple copia de archivos) se documenta en la página de cada servicio individual, no acá.

## Observabilidad

- `docker compose ps` mostrando todos los servicios en estado `healthy`;
- uso de disco de `/srv/oscar/data`, para detectar un volumen que crece sin límite;
- reinicios inesperados de contenedores (`docker events`);
- logs de errores por servicio (`docker compose logs`).

## Troubleshooting

**Un contenedor reinicia en loop** → falla de healthcheck o crash al arrancar → revisar `docker compose logs --tail=100 <servicio>` y el runbook [docker-servicio-caido.md](../runbooks/docker-servicio-caido.md).

**Un volumen crece sin control y llena el disco** → falta rotación de logs o de datos temporales dentro del contenedor → revisar `docker system df` y el uso de `/srv/oscar/data`; ver el runbook [disco-lleno.md](../runbooks/disco-lleno.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://docs.docker.com/
