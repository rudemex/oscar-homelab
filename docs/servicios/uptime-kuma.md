---
title: Uptime Kuma
sidebar_position: 11
---

# Uptime Kuma

**Estado:** Actual · Disponibilidad — corriendo en `core01`  
**Dónde corre:** Docker Core  
**Sizing inicial:** 1 vCPU, 512 MB–1 GB RAM  
**Red/puertos:** 3001 interno  
**Persistencia:** DB/configuración y monitores

## Rol dentro de O.S.C.A.R.

- HTTP checks
- ping
- TCP port checks
- DNS checks
- status page interna

## Monitores reales configurados

9 monitores HTTP, chequeo cada 60s, apuntando a la IP LAN real de cada servicio (no al hostname público) para medir el backend directo y no depender de Cloudflare Access en el camino — cubre todo lo que el inventario marca como "Actual" excepto Kuma mismo (ver "nadie vigila al vigilante" más abajo):

| Monitor | URL | Nota |
|---|---|---|
| n8n | `http://192.168.0.156:5678/healthz` | endpoint de salud dedicado, más preciso que chequear la UI |
| Homepage | `http://192.168.0.156:3005` | — |
| Beszel hub | `http://192.168.0.156:8090` | — |
| ProxMenux Monitor | `http://192.168.0.233:8008` | en `oscar-core`, no en `core01` |
| Vaultwarden | `https://vault.oscarlab.com.ar/alive` | endpoint de salud dedicado (liviano, no carga toda la app); solo escucha en `127.0.0.1` en `core01` así que se mide vía el dominio público — necesitó otro bypass de Access (`/alive`, igual patrón que `/identity`/`/api`/`/notifications`/`/icons`) porque si no Cloudflare lo interceptaba antes de llegar |
| Proxmox | `https://192.168.0.233:8006` | con `ignoreTls` (certificado self-signed) |
| AdGuard Home | `http://192.168.0.93:80` | LXC 100 |
| Home Assistant | `http://192.168.0.195:80` | VM 101 — **no** el 8123 típico de otras instalaciones; esta usa el puerto 80, se descubrió por error al asumir el default |
| Cloudflare Tunnel | `http://192.168.0.156:20241/ready` | endpoint de salud propio de `cloudflared`, expuesto porque corre en `network_mode: host` |

Se armaron vía la API de socket.io (paquete `uptime-kuma-api`, no la REST API — Kuma no tiene una para crear monitores, el API Key propio de Kuma solo sirve para el endpoint de métricas de Prometheus, no para esto).

## Status page

Existe una status page en `/status/oscar` con los 9 monitores agrupados en "Servicios" — no es solo para verla directamente, es lo que consume el [widget de Uptime Kuma en Homepage](./homepage.md#widgets-nativos-datos-en-vivo-en-la-tarjeta): ese widget lee de una status page (por `slug`), no de la lista de monitores directo.

Nota técnica si se vuelve a tocar por API: la librería `uptime-kuma-api` (v1.x) tiene un bug de compatibilidad con Kuma 2.5.4 en `save_status_page()` (falla por una key `incident` que esta versión del servidor ya no devuelve) — hubo que armar el payload a mano y llamar `saveStatusPage` directo por socket.io. Un detalle no obvio ahí: **python-socketio necesita una `tuple` para mandar múltiples argumentos posicionales, no una `list`** — pasar una lista hace que el servidor reciba todo el array como un solo parámetro (`slug`), y falla con `"No slug?"`.

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
