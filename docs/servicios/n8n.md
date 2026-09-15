---
title: n8n
sidebar_position: 12
---

# n8n

**Estado:** Actual · Automatización — corriendo en `core01`, con PostgreSQL dedicado (no el SQLite por defecto de n8n)
**Dónde corre:** Docker Core (`/srv/oscar/apps/n8n/`)
**Sizing real:** compartiendo `core01` con el resto del stack, sin límites de CPU/RAM propios en el compose — medir antes de fijarlos
**Red/puertos:** `5678` publicado en toda la LAN (`0.0.0.0:5678`, no solo loopback) — no hay bypass de Cloudflare Access para webhooks todavía, ver "Seguridad" abajo
**Persistencia:** volumen nombrado `n8n-data` (workflows, encryption key) + volumen `postgres-data` separado (DB real, no el SQLite embebido)

## Rol dentro de O.S.C.A.R.

- backups coordinados
- notificaciones de alertas
- inventario automático
- workflows de IA
- integraciones GitHub/GitLab/Home Assistant

## Ejemplo concreto

Workflow: Alertmanager → webhook n8n → obtener contexto de Prometheus → enviar resumen con host, métrica y runbook asociado. (Pendiente real — hoy no hay Alertmanager/Prometheus desplegado, ver [observabilidad](../observabilidad/instalacion-stack.md); es el caso de uso objetivo, no uno ya construido.)

## Instalación

```bash
mkdir -p /srv/oscar/apps/n8n
```

`compose.yaml`:

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
      N8N_SECURE_COOKIE: "false"   # sin HTTPS local delante (Cloudflare Tunnel termina el TLS antes)
      GENERIC_TIMEZONE: ${TZ}
      TZ: ${TZ}
    volumes:
      - n8n-data:/home/node/.n8n
    ports:
      - "5678:5678"

volumes:
  postgres-data:
  n8n-data:
```

`.env` (placeholders — nunca commitear los valores reales):

```dotenv
N8N_VERSION=2.38.7
POSTGRES_VERSION=17
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=<TU_PASSWORD_AQUI>
N8N_ENCRYPTION_KEY=<GENERAR_CON_openssl_rand_-hex_32>
TZ=America/Argentina/Buenos_Aires
```

```bash
docker compose up -d
```

## Checklist de despliegue

- [x] hostname y ubicación decididos (`core01`, `n8n.oscarlab.com.ar` vía Cloudflare Tunnel);
- [x] imagen/versión fijada (`2.38.7` n8n, `17` postgres), sin tags flotantes;
- [x] puertos documentados (`5678`);
- [x] volumen/persistencia definida (`n8n-data` + `postgres-data`, ambos nombrados);
- [x] `.env.example` sin secretos en Git — los reales viven solo en `core01`;
- [x] credenciales reales fuera de Git (Vaultwarden);
- [ ] backup definido antes de cargar datos importantes — el procedimiento está documentado ([Backup de n8n](../backup-dr/backup-n8n.md)) pero no hay un cron/automatización real corriéndolo todavía;
- [x] healthcheck o monitor de disponibilidad (Uptime Kuma, "n8n (core01)");
- [ ] métricas/logs incorporados — pendiente del stack de observabilidad;
- [ ] procedimiento de actualización y rollback documentado.

## Seguridad

La encryption key de n8n es crítica para recuperar credenciales cifradas. Debe respaldarse fuera del contenedor.

**Gap pendiente:** hoy `n8n.oscarlab.com.ar` no tiene ninguna ruta de bypass de Cloudflare Access documentada — ver el detalle en [Cloudflare Tunnel + Access](./cloudflare-tunnel.md#estado-real-del-despliegue). Si algún workflow depende de un webhook público real (por ejemplo el de Alertmanager del ejemplo de abajo), hoy quedaría bloqueado por el login OTP de Access antes de llegar a n8n.

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
