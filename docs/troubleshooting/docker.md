---
title: Docker
sidebar_position: 3
---

# Docker

```bash
docker compose ps
docker compose logs --tail=200 <service>
docker inspect <container>
docker stats
```

## Síntomas comunes

### Restart loop

Revisar entrypoint, variables, permisos, dependencia DB y healthcheck.

### No conecta a DB

Usar hostname de servicio de Compose, no asumir `localhost`. Dentro del contenedor, `localhost` es el propio contenedor.

### Disco crece

Revisar logs, imágenes huérfanas y volúmenes. No ejecutar prune indiscriminado en un host que contiene datos sin inspeccionar primero.
