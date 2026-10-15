---
title: oscar-discord (bot de Discord)
sidebar_position: 12
---

# oscar-discord — bot de Discord de O.S.C.A.R.

**Estado:** Actual (v0.5.0, 2026-10-15).
**Repo:** `projects/oscar-discord` en Forgejo, creado desde Backstage con la plantilla "Nuevo servicio NestJS" (base `templates/nestjs-starter`, discord.js 14.27.0, Postgres propio).
**Dónde corre:** k3s, namespace `oscar-lab`, nodo `apps` (Argo CD app `oscar-discord`, chart en `apps/gitops`, carpeta `apps/oscar-discord`).
**URL interna:** `http://oscar-discord.oscar.home/v1` (Swagger en `/v1/docs`).
**Bot:** usa la Discord Application **O.S.C.A.R.** (`O.S.C.A.R.#1331`), distinta de la de Hermes (`HermesAgent`).

## Para qué está

Es la cara de OSCAR en Discord para todo lo que **no** tiene que pasar por una IA: avisos, aprobaciones, botones de acción, un panel en vivo y comandos fijos. Funciona aunque Hermes esté caído o sin crédito. Reemplazó a los webhooks de Discord del [Notification Broker de n8n](./discord.md) y al formulario de n8n de las aprobaciones de actualizaciones.

## Qué hace

### Tarjetas (`POST /v1/notify`)

- Publica una tarjeta (embed) en un canal del servidor, buscado por **nombre** (`deployments`, `alerts`…): n8n no necesita IDs ni webhooks por canal.
- `level` (`info`, `success`, `warning`, `error`, `progress`) define color e ícono; también `fields`, `footer` y hasta 5 botones de enlace (`links`).
- `key`: si se repite, **edita la misma tarjeta** en vez de mandar otra (una caída y su recuperación, un deploy en curso que termina).
- `resolve: true`: cierra la tarjeta de esa key (sin botones de acción) y libera la key, así el próximo evento arranca una tarjeta nueva.
- `actions` (hasta 4, de un solo uso, solo para los aprobadores):
  - `silence`: crea un silencio real en Alertmanager con los `matchers` dados (`minutes`, por defecto 60).
  - `ack`: marca la tarjeta como vista.
  - `restart`: reinicia un servicio de `RESTART_TARGETS` (ver más abajo).
  Al usarse, la tarjeta suma una nota ("🔕 Silenciada hasta las 15:40 por mexdelgado") y pierde ese botón.

### Aprobaciones (`POST /v1/approvals`)

Publica un pedido con botones **Aprobar / Rechazar** (las etiquetas se pueden cambiar). Solo los usuarios de `DISCORD_APPROVER_IDS` pueden decidir, la decisión se toma una sola vez y se avisa con un `POST` JSON `{approvalId, decision, approved, by, at}` a `callbackUrl` (solo hosts de `CALLBACK_ALLOWED_HOSTS`). Si nadie decide antes de `timeoutMinutes` (24 h por defecto), vence y se avisa `decision: "expired"`. `GET /v1/approvals/:id` devuelve el estado.

Lo usa el workflow de n8n **"OSCAR - tool update"**: el nodo "Pedir aprobación (bot)" manda el pedido con `callbackUrl = $execution.resumeUrl` reescrita a `http://192.168.0.153:5678/…` (la URL pública pasa por Cloudflare Access y el bot no podría entrar), y el nodo Wait espera con `resume: webhook`.

### Panel fijo en `#estado`

Un único mensaje que se edita cada minuto con:

1. **Resumen** (verde/amarillo/rojo): servicios arriba según la status page `oscar` de Uptime Kuma, alertas activas sin silenciar de Alertmanager, Internet (MySpeed) y aprobaciones pendientes.
2. **Servicios**: los monitores de Kuma, los caídos primero.
3. **Máquinas**: CPU/RAM/disco de cada host (node_exporter) y VMs/contenedores encendidos (Proxmox). Más del 85 % se marca con ⚠️.
4. **Discos de oscar-core**: salud, uso y temperatura (ProxMenux Monitor).

Si una fuente no responde, esa sección muestra "sin datos" y el resto se sigue actualizando. Si alguien borra el mensaje, se vuelve a publicar. `#estado` es de solo lectura para `@everyone`.

### Comandos

Respuesta privada (solo la ve quien pregunta), registrados en el servidor de OSCAR al conectarse:

| Comando | Qué muestra |
|---|---|
| `/estado` | El panel completo |
| `/alertas` | Alertas activas (incluidas las silenciadas), con un botón 🔕 por alerta |
| `/backups` | Último backup de cada VM con antigüedad, tamaño y copias; ⚠️ si tiene más de 26 h (las plantillas no cuentan) |
| `/discos` | Salud, uso y temperatura de los discos |
| `/aprobaciones` | Pedidos pendientes, con enlace a cada tarjeta |

### Botón Reiniciar

Solo reinicia lo que está en `RESTART_TARGETS`, con dos capas:

- `docker:<host>/<proyecto>[/<servicio>]`: por el **operador Docker** de ese host (el mismo de Hermes; el bot solo usa `restart`, nunca stop/down). Tokens de core, devops y automation.
- `k8s:<namespace>/<deployment>`: como `kubectl rollout restart` (anotación `restartedAt`), con la ServiceAccount `oscar-discord`, que solo tiene `get`/`patch` de Deployments en `oscar-lab` y `headlamp`. Argo CD no revierte esa anotación.

El mapeo de qué tarjeta lleva el botón vive en n8n: `RESTART_BY_MONITOR` (Format Kuma, por ID de monitor) y `RESTART_BY_URL` (Format Alertmanager, para `ServiceHttpDown`).

## Configuración

| Variable | Origen | Para qué |
|---|---|---|
| `DISCORD_TOKEN`, `API_TOKEN`, `PROXMENUX_TOKEN`, `DOCKER_OPERATOR_TOKEN_*`, `NEXUS_*` | Infisical, proyecto OSCAR Apps, carpeta `/oscar-discord` | Secretos |
| `DISCORD_APPROVER_IDS` | ConfigMap | Quién puede apretar botones |
| `CALLBACK_ALLOWED_HOSTS` | ConfigMap | A dónde se avisa una decisión |
| `ALERTMANAGER_URL`, `PROMETHEUS_URL`, `KUMA_URL`, `KUMA_STATUS_SLUG`, `PROXMENUX_URL` | ConfigMap | Fuentes del panel y del silencio |
| `PANEL_CHANNEL`, `PANEL_INTERVAL_SECONDS` | ConfigMap | Canal del panel (vacío = apagado) |
| `RESTART_TARGETS`, `DOCKER_OPERATOR_CA` | ConfigMap | Botón Reiniciar |
| `POSTGRES_*` | Chart (Postgres dedicado) | Pedidos, botones y tarjetas con key |

Los tokens también están en Vaultwarden ("Discord | Token Bot | O.S.C.A.R."). En n8n, el Broker y el tool update usan la credencial `httpHeaderAuth` **"OSCAR Discord API"**.

## CI/CD

`.forgejo/workflows/ci.yml` usa `platform/ci-shared` `apps-be.yml@v2.1.1`: lint, formato, tests con **100 % de cobertura obligatoria**, build, prueba de humo de la imagen, push a Nexus y tag fijado en gitops. Los secretos de CI (`NEXUS_USER`, `NEXUS_PASSWORD`, `GITOPS_TOKEN`) están a nivel de la organización `projects`, así cualquier proyecto nuevo de Backstage los tiene.

## Trampas encontradas al construirlo (2026-10-15)

- `ci-shared` v2.1.0 seguía autoreferenciándose como `mdelgado/ci-shared` después de la reorganización de organizaciones: ningún consumidor podía expandir el workflow. Se publicó **v2.1.1** y se migraron nestjs-api, ci-demo y led-controller (que además habían perdido sus secretos de CI al cambiar de organización).
- La plantilla de Backstage generaba un `Chart.yaml` inválido si la descripción tenía ":" (corregido en oscar-idp) y apunta los secretos a la carpeta compartida `/ci-demo` de Infisical; una app con secretos propios necesita su carpeta.
- `root-app` de Argo CD sincroniza a mano: una app nueva no aparece sola.
- helmet (del starter) mandaba `upgrade-insecure-requests` y HSTS: por http, Swagger quedaba en blanco. Corregido en el bot y en nestjs-api.
- Forgejo Actions a veces deja una ejecución en "waiting" con el runner libre; un commit vacío la destraba.
- Argo CD tarda unos minutos en tomar un tag nuevo: `kubectl -n argocd annotate application oscar-discord argocd.argoproj.io/refresh=normal --overwrite` lo fuerza.

## Pendientes posibles

- Comandos que actúan (por ejemplo `/vm reiniciar`), pasando por aprobación con botones.
