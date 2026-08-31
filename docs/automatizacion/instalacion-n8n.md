---
title: Instalar n8n
sidebar_position: 4
---

# n8n paso a paso

Para una instalación persistente preferimos n8n + PostgreSQL, evitando depender de una DB embebida cuando los workflows empiecen a importar.

## 1. Directorio

```bash
mkdir -p /srv/oscar/apps/n8n
cd /srv/oscar/apps/n8n
```

## 2. `.env`

```dotenv
N8N_VERSION=CHANGE_ME_STABLE
POSTGRES_VERSION=CHANGE_ME_STABLE
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=CHANGE_ME
N8N_ENCRYPTION_KEY=GENERATE_A_LONG_RANDOM_VALUE
TZ=America/Argentina/Buenos_Aires
```

La encryption key debe respaldarse en un lugar seguro. Sin ella, recuperar la DB puede no alcanzar para recuperar credenciales cifradas.

## 3. Compose conceptual

```yaml
services:
  postgres:
    image: postgres:${POSTGRES_VERSION}
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n:
    image: docker.n8n.io/n8nio/n8n:${N8N_VERSION}
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: ${POSTGRES_DB}
      DB_POSTGRESDB_USER: ${POSTGRES_USER}
      DB_POSTGRESDB_PASSWORD: ${POSTGRES_PASSWORD}
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
      GENERIC_TIMEZONE: ${TZ}
      TZ: ${TZ}
    volumes:
      - n8n-data:/home/node/.n8n
    ports:
      - "127.0.0.1:5678:5678"

volumes:
  postgres-data:
  n8n-data:
```

## 4. Inicio

```bash
docker compose config
docker compose up -d
docker compose logs -f n8n
```

## 5. Reverse proxy

Publicar la UI solo en LAN/VPN/Access. Si se necesitan webhooks externos, exponer rutas necesarias mediante reverse proxy/tunnel y configurar la URL pública de n8n correctamente.

## 6. Primer workflow

Crear un Schedule Trigger que consulte un endpoint de prueba y guarde/mande resultado. Luego exportarlo como JSON sanitizado si queremos mantenerlo de referencia.

## 7. Backup

Respaldar:

- PostgreSQL con dump consistente;
- `N8N_ENCRYPTION_KEY` por separado;
- configuración/Compose;
- volumen `.n8n` según versión/features.

## 8. Restore test

Restaurar DB y key en una instancia aislada y comprobar que los workflows y credenciales pueden abrirse.
