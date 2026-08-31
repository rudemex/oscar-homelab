---
title: Baseline del host Docker
sidebar_position: 20
---

# Baseline del host Docker

## Estructura por aplicación

```text
/srv/oscar/apps/<app>/
├── compose.yaml
├── .env                # no Git
├── .env.example        # Git
└── README.md
```

Datos grandes pueden ir en `/srv/oscar/data/<app>`.

## Operación estándar

```bash
cd /srv/oscar/apps/<app>
docker compose pull
docker compose config
docker compose up -d
docker compose ps
docker compose logs --tail=100
```

## Upgrade

1. revisar release notes;
2. confirmar backup;
3. cambiar tag en Compose/.env;
4. `docker compose pull`;
5. `docker compose up -d`;
6. validar health;
7. observar logs;
8. rollback al tag anterior si falla.

## Log rotation

Evitar que logs JSON crezcan sin control. Configurar límites del daemon o logging driver según estrategia de Loki.

## Networks

Crear redes por stack cuando Compose lo hace automáticamente. Usar una red compartida solo cuando servicios de stacks distintos realmente deban hablar.

## Puertos

Si un servicio solo será consumido por un reverse proxy en el mismo host, considerar bind a loopback o networking interno en vez de publicar `0.0.0.0` indiscriminadamente.
