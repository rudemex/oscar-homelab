---
title: Docker - Whoami
sidebar_position: 2
---

# Primer contenedor

Un servicio mínimo permite validar Docker, networking y reverse proxy sin introducir una base de datos.

```yaml
services:
  whoami:
    image: traefik/whoami:v1.11.0
    restart: unless-stopped
    ports:
      - "8080:80"
```

```bash
docker compose up -d
docker compose ps
curl http://localhost:8080
```

## Experimentos

1. cambiar el puerto host a 8081;
2. detener contenedor y ver Uptime Kuma;
3. agregar reverse proxy;
4. eliminar y recrear;
5. verificar que no existe estado que respaldar.
