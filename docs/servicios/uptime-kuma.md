---
title: Uptime Kuma
sidebar_position: 11
---

# Uptime Kuma

**Estado:** Actual · Disponibilidad — única instancia, corriendo en `monitor` desde 2026-09-22 (ver [migración a `monitor`](#migración-a-monitor-2026-09-22)). Historia previa: `core` → `pinode01` (2026-09-21) → `monitor` (2026-09-22).  
**Dónde corre:** Docker Core  
**Sizing inicial:** 1 vCPU, 512 MB–1 GB RAM  
**Red/puertos:** 3001 interno  
**Persistencia:** DB/configuración y monitores

## Segunda instancia en `pinode01` (2026-09-21)

Se levantó una copia en [`pinode01`](../hardware/network.md) para sacar el monitoreo del Dell (si `oscar-core` cae, Kuma cae con él justo cuando hace falta). **Migración, no recreación:** se sacó una instantánea consistente de la base con `VACUUM INTO` (sin parar el Kuma de `core`), se verificó el hash al copiarla y se levantó la misma versión `2.5.4`.

| Dato | Valor |
|---|---|
| Ubicación | `pinode01`, `/srv/oscar/apps/uptime-kuma/` (`compose.yaml` + `data/` como bind mount), Docker `26.1.5` |
| Acceso | `http://192.168.0.213:3001`, mismas credenciales que la instancia de `core` |
| Consumo | ~140 MB de RAM en régimen (los primeros minutos, con los 21 monitores arrancando a la vez, la CPU de la Pi 3 llega al 100 %) |
| DNS de la Pi | `192.168.0.213` (su propio AdGuard) y `1.1.1.1`, para que los monitores de `*.oscar.home` resuelvan |

**Validado:** 21 monitores en ambas instancias, el **mismo estado** en cada uno (19 arriba, 2 abajo: `AdGuard Home (LXC 100)` y `Home Assistant (VM 101)`, los dos afectados por la falla del SSD `sda`) y el historial conservado (2 183 latidos del monitor #1 en 30 días contra 2 192 en `core`).

**Corte hecho (2026-09-21): Kuma vive solo en `pinode01`.** Homepage (widget `uptimekuma` y `siteMonitor`) apunta a `http://192.168.0.213:3001`; el Kuma de `core` quedó **detenido** (`docker compose stop`, el volumen `uptime-kuma_uptime-kuma-data` se conserva unos días como respaldo antes de borrarlo). El hostname público `kuma.oscarlab.com.ar` (con su política de Cloudflare Access, que va atada al hostname) sigue publicado.

**Túnel propio para la Pi, no un segundo conector del de `core`.** Las rutas de un túnel son compartidas por todos sus conectores: sumar la Pi al túnel de `core` haría que Cloudflare mandara a la Pi parte del tráfico de `vault`/`n8n`/`home`/`beszel`, que apuntan a `localhost` de `core` (y Vaultwarden solo escucha en `127.0.0.1:8082`). Por eso la Pi tiene su **propio túnel** (`pinode01`) con su conector y, así, `kuma.oscarlab.com.ar` sobrevive a una caída del Dell. Un hostname pertenece a un solo túnel: la ruta `kuma` se borra del túnel de `core` y se crea en el de la Pi (`http://localhost:3001`).

Durante la migración, la ruta de `core` para Kuma estuvo apuntando a `http://192.168.0.213:3001` (no a `localhost:3001`, que era el Kuma detenido).

**Corrección (2026-09-22): el "túnel propio" del párrafo de arriba nunca enrutó `kuma.oscarlab.com.ar` en la práctica.** Al revisar la configuración real por la API de Cloudflare para la migración de abajo, se encontró que el registro DNS de `kuma.oscarlab.com.ar` siempre apuntó al túnel de `core` (`ace28107-...`), con un ingress rule `service: http://192.168.0.213:3001` — es decir, el tráfico público pasó todo este tiempo por el conector de `core`, proxeando por LAN hacia la Pi, **no** por el túnel dedicado `pinode01` (que existe registrado en Cloudflare pero con `config: null`, sin ingress rules). La resiliencia real ante una caída del Dell para este hostname público **no estaba dada** como se documentó originalmente.

**Resuelto de verdad (2026-09-23):** con el Dell habiendo tumbado el host completo por tercera vez ese mismo día (ver [estado actual](../arquitectura/estado-actual.md)), se movió el ingress real de `kuma.oscarlab.com.ar` al túnel `pinode01` (ingress nuevo `http://192.168.0.214:3001`, DNS repuntado al `tunnel-id` de la Pi, entrada vieja borrada de `core`) — ahora si el Dell cuelga, `kuma.oscarlab.com.ar` sigue respondiendo. Detalle completo en [Cloudflare Tunnel](./cloudflare-tunnel.md#segundo-túnel-pinode01-con-uso-real-2026-09-23).

## Migración a `monitor` (2026-09-22)

Segunda migración, mismo patrón que la de `core`→`pinode01`: parar el contenedor, empaquetar `data/` (`tar.gz`, checksum SHA-256 verificado en origen/Mac/destino), copiar a `monitor` (192.168.0.214), levantar la misma versión `2.5.4`. Motivo: consolidar toda la observabilidad (Prometheus, Grafana, Blackbox, y ahora Kuma) en un solo host, según la arquitectura de `REORGANIZACION_RACK.md` — "una única instancia de Uptime Kuma... vive en `monitor`".

| Dato | Valor |
|---|---|
| Ubicación | `monitor`, `/srv/oscar/apps/uptime-kuma/` (mismo `compose.yaml`, `data/` como bind mount) |
| Acceso | `http://192.168.0.214:3001` |
| Verificado | contenedor `healthy`, monitores e historial presentes en los logs de arranque (mismos IDs que antes, ej. Monitor #7 `AdGuard Home`, #10 `Home Assistant`) |

**Actualizado en el mismo movimiento:**
- Homepage (widget `uptimekuma` y `siteMonitor`): `192.168.0.213:3001` → `192.168.0.214:3001` (`services.yaml`, backup dejado en el host como `services.yaml.bak-kuma-migration-2026-09-22`).
- El ingress rule real de `kuma.oscarlab.com.ar` en el túnel de `core` (ver corrección arriba): `http://192.168.0.213:3001` → `http://192.168.0.214:3001`, vía API de Cloudflare.

**`network` (antes `pinode01`) queda detenido, no borrado**: `docker compose stop`, datos conservados en `/srv/oscar/apps/uptime-kuma/data/` unos días como respaldo antes de decidir si se borran.

## Rol dentro de O.S.C.A.R.

- HTTP checks
- ping
- TCP port checks
- DNS checks
- status page interna

## Monitores reales configurados

21 monitores HTTP (2026-09-20: 14 previos + 7 nuevos), chequeo cada 60s, apuntando a la IP LAN real de cada servicio (no al hostname público) para medir el backend directo y no depender de Cloudflare Access en el camino — cubre todo lo que el inventario marca como "Actual" excepto Kuma mismo (ver "nadie vigila al vigilante" más abajo). Argo CD y los servicios nuevos ya están en la tabla y en la status page (resuelto 2026-09-20); el del LED está fuera de la status page a propósito, ver la tabla.

| Monitor | URL | Nota |
|---|---|---|
| n8n | `http://192.168.0.153:5678/healthz` | en `automation` (migrado 2026-09-23), endpoint de salud dedicado, más preciso que chequear la UI |
| Homepage | `http://192.168.0.156:3005` | — |
| Beszel hub | `http://192.168.0.156:8090` | — |
| ProxMenux Monitor | `http://192.168.0.233:8008` | en `oscar-core`, no en `core` |
| Vaultwarden | `https://vault.oscarlab.com.ar/alive` | endpoint de salud dedicado (liviano, no carga toda la app); en `services` desde el 2026-09-23 (antes `core`), se sigue midiendo vía el dominio público — necesitó otro bypass de Access (`/alive`, igual patrón que `/identity`/`/api`/`/notifications`/`/icons`) porque si no Cloudflare lo interceptaba antes de llegar |
| Proxmox | `https://192.168.0.233:8006` | con `ignoreTls` (certificado self-signed) |
| AdGuard Home | `http://192.168.0.93:80` | LXC 100 |
| Home Assistant | `http://192.168.0.195:80` | VM 101 — **no** el 8123 típico de otras instalaciones; esta usa el puerto 80, se descubrió por error al asumir el default |
| Cloudflare Tunnel | `http://192.168.0.156:20241/ready` | endpoint de salud propio de `cloudflared`, expuesto porque corre en `network_mode: host` |
| Forgejo | `http://192.168.0.151:3000/api/healthz` | en `devops`, no en `core`; medido por IP+puerto igual que el resto, no por `git.oscar.home` |
| Nexus | `http://192.168.0.151:8081/service/rest/v1/status` | en `devops`; sin monitor para el CI Runner (`forgejo-runner`) — no expone ningún endpoint HTTP propio sin sumarle config de métricas aparte |
| Portainer | `http://portainer.oscar.home` | vía NPM, como el resto de los `*.oscar.home` |
| oscar-led-controller | `http://led.oscar.home/health` | en k3s; **fuera de la status page a propósito**: da `503` mientras el ESP32 esté apagado y dejaría un "down" permanente en el widget de Homepage |
| Argo CD | `http://argocd.oscar.home` | en k3s (Traefik) |
| Infisical | `http://192.168.0.151:8085/api/status` | en `devops`, por IP+puerto (2026-09-20) |
| Headlamp | `http://headlamp.oscar.home` | en k3s (2026-09-20) |
| SearXNG | `http://searxng.oscar.home/healthz` | en `services` desde el 2026-09-23 (antes k3s, namespace `oscar-ai`) — misma URL, resuelve distinto (NPM en vez de Traefik) |
| DocuSeal | `http://docuseal.oscar.home` | en `services` (2026-09-23), instalado sin cuenta admin todavía |
| ci-demo | `http://ci-demo.oscar.home` | en k3s (2026-09-20) |
| Nginx Proxy Manager | `http://192.168.0.156:81` | UI de administración (2026-09-20) |
| MySpeed | `http://192.168.0.156:5216` | (2026-09-20) |
| Glances | `http://192.168.0.156:61208` | (2026-09-20) |

Los servidores de juegos (Minecraft, CS2) no tienen monitor a propósito: están apagados por defecto y saldrían siempre en rojo. Los monitores de servicios en k3s usan el hostname `*.oscar.home` (Kuma corre en `monitor`, que resuelve `*.oscar.home` vía el AdGuard de `network`); los de Docker siguen por IP+puerto.

Se armaron vía la API de socket.io (paquete `uptime-kuma-api`, no la REST API — Kuma no tiene una para crear monitores, el API Key propio de Kuma solo sirve para el endpoint de métricas de Prometheus, no para esto).

## Status page

Existe una status page en `/status/oscar` con los 11 monitores agrupados en "Servicios" — no es solo para verla directamente, es lo que consume el [widget de Uptime Kuma en Homepage](./homepage.md#widgets-nativos-datos-en-vivo-en-la-tarjeta): ese widget lee de una status page (por `slug`), no de la lista de monitores directo.

Notas técnicas si se vuelve a tocar por API (`uptime-kuma-api` v1.x contra este Kuma 2.5.4, hay más de un bug de compatibilidad de versión):

- **`add_monitor()` falla con `NOT NULL constraint failed: monitor.conditions`** — esta versión del servidor exige una columna `conditions` que la librería todavía no expone como parámetro. Workaround: armar el dict a mano con `api._build_monitor_data(...)`, agregar `data['conditions'] = []`, y llamar `api._call('add', data)` directo en vez de `api.add_monitor()`.
- **`get_status_page()`/`save_status_page()` fallan con `KeyError: 'incident'`** — la librería espera una key `incident` (objeto singular) que este servidor ya no devuelve; la API pública (`GET /api/status-page/<slug>`) ahora manda `incidents` (array, en plural). Workaround: no usar `save_status_page()`, armar el payload a mano leyendo `publicGroupList`/`config` de esa misma respuesta REST y llamar `api._call('saveStatusPage', (slug, config, icon, publicGroupList))` directo.
- **`saveStatusPage` responde `"Invalid array"`** si el `config` no incluye `domainNameList` — la respuesta REST de arriba no siempre trae esa key; agregarla a mano (`config.setdefault('domainNameList', [])`) antes de guardar.
- **`python-socketio` necesita una `tuple` para mandar múltiples argumentos posicionales, no una `list`** — pasar una lista hace que el servidor reciba todo el array como un solo parámetro (`slug`), y falla con `"No slug?"`.

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

Un monitor dentro del mismo host no detecta que el host entero desapareció desde la perspectiva externa. Agregar probe en Raspberry mejora cobertura.

Los canales de notificación (tokens de Telegram, webhooks, credenciales SMTP) quedan guardados dentro de `kuma.db`; tratar ese archivo como secreto, no solo como backup.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Caso opuesto al resto de los servicios de observabilidad: acá el estado es crítico y no recreable. Toda la configuración de monitores, historial de uptime, canales de notificación y status pages vive en un único archivo SQLite, `/app/data/kuma.db`. Perderlo significa recrear a mano cada monitor y cada integración de notificaciones.

Backup: copiar `kuma.db` con el contenedor detenido, o usar la función nativa Settings → Backup, que exporta un JSON con monitores y notificaciones — más liviano que copiar la DB completa, pero sin el historial de uptime.

Restore: detener el contenedor de la instancia nueva, reemplazar `kuma.db`, iniciar.

Nota aparte: Uptime Kuma no puede alertar sobre su propia caída, así que necesita un chequeo externo independiente (un segundo monitor liviano, o un servicio externo tipo Healthchecks.io en el laboratorio de IA/automatización) — ver "Seguridad" arriba.

## Observabilidad

Uptime Kuma no tiene un endpoint de salud útil para auto-monitoreo (ver "Backup y restore" y "Seguridad" arriba: nadie vigila al vigilante desde adentro). En su lugar:

- Docker healthcheck verificando que el proceso esté arriba;
- que `kuma.db` no esté corrompido (tamaño 0 o error de apertura);
- un monitor externo independiente que confirme que Kuma mismo responde;
- reinicios inesperados del contenedor.

## Troubleshooting

- **Monitor marca down pero el servicio responde manualmente** → timeout muy corto, o Kuma está en una VLAN sin ruta al servicio monitoreado → ajustar timeout/intervalo del monitor, verificar reachability desde el propio host de Kuma.
- **No llegan notificaciones aunque el monitor cambió de estado** → canal de notificación mal configurado (token vencido, webhook incorrecto) o notificación no asociada al monitor → probar el canal con el botón de test en Settings → Notifications, confirmar que esté vinculado al monitor.
- **Uptime Kuma no arranca / `kuma.db` corrupta** → corte eléctrico o kill del contenedor durante una escritura → restaurar desde el último backup de `kuma.db`; si no hay backup reciente, reconstruir monitores desde el export JSON de Settings → Backup si existe. Ver [`docker-servicio-caido.md`](../runbooks/docker-servicio-caido.md) y [`backup-fallido.md`](../runbooks/backup-fallido.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://github.com/louislam/uptime-kuma/wiki
