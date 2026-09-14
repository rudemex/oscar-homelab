---
title: Forgejo / Git local
sidebar_position: 5
---

# Forgejo / Git local

**Estado:** Actual — Forgejo 16.0.4 corriendo en `devops01`, sano (`/api/healthz` en pass), admin creado
**Dónde corre:** VM `devops01` (vmid 104), `/srv/oscar/apps/forgejo/`
**Sizing real de la VM:** 4 vCPU / 8 GB RAM / 60 GB disco — más grande que el 1-2 GB de ADR-010 a propósito, para dejar margen al runner de Forgejo Actions que va a compartir la misma VM
**Red/puertos:** `http://git.oscar.home` (sin puerto — nginx en `:80` hace de reverse proxy hacia `:3000` interno, ver "Reverse proxy" abajo), `git.oscar.home:2222` SSH (Git) — el 22 del host lo ocupa el sshd de la VM, así que Forgejo escucha SSH en 2222 hacia afuera aunque el contenedor lo sirva en el 22 interno
**Persistencia:** SQLite + repos + attachments + config, todo en `/srv/oscar/data/forgejo` (bind mount, container corre `/data`)
**Dependencia real:** todo lo anterior asume que el dispositivo que accede tiene su DNS apuntado a AdGuard (`192.168.0.93`) — ver "Nota sobre AdGuard" más abajo, no es DNS de toda la red hoy.

## Rol dentro de O.S.C.A.R.

- mirror de repositorios importantes
- repositorios privados del homelab
- GitOps completamente local
- practicar hooks y flujos de PR

## Instalación

VM creada por clon del template `9000` (ver [Templates y Cloud-Init](../proxmox/templates-cloud-init.md)):

```bash
qm clone 9000 104 --name devops01 --full
qm resize 104 scsi0 60G
qm set 104 --cores 4 --memory 8192
qm set 104 --ipconfig0 ip=192.168.0.151/24,gw=192.168.0.1
qm start 104
```

Setup base (paquetes, Docker) igual que [core01](../proxmox/crear-vm-core01.md), sin repetirlo acá.

`.env`:

```dotenv
FORGEJO_VERSION=16.0.4
FORGEJO_HTTP_PORT=3000
FORGEJO_SSH_PORT=2222
FORGEJO_DOMAIN=192.168.0.151
FORGEJO_ROOT_URL=http://192.168.0.151:3000/
```

`compose.yaml`:

```yaml
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:${FORGEJO_VERSION}
    container_name: forgejo
    restart: unless-stopped
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      FORGEJO__database__DB_TYPE: sqlite3
      FORGEJO__server__DOMAIN: ${FORGEJO_DOMAIN}
      FORGEJO__server__ROOT_URL: ${FORGEJO_ROOT_URL}
      # SSH_PORT es el puerto anunciado en las URLs de clone (host); SSH_LISTEN_PORT
      # es el puerto interno del contenedor (22) — el host 22 ya lo usa el sshd de la VM.
      FORGEJO__server__SSH_DOMAIN: ${FORGEJO_DOMAIN}
      FORGEJO__server__SSH_PORT: ${FORGEJO_SSH_PORT}
      FORGEJO__server__SSH_LISTEN_PORT: "22"
      # Sin autoregistro público desde el día 1 (mismo criterio que Vaultwarden
      # SIGNUPS_ALLOWED=false) — el admin se crea por el instalador inicial o por CLI,
      # no depende de esta bandera.
      FORGEJO__service__DISABLE_REGISTRATION: "true"
    volumes:
      - /srv/oscar/data/forgejo:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "${FORGEJO_HTTP_PORT}:3000"
      - "${FORGEJO_SSH_PORT}:22"
```

SQLite en vez de Postgres a propósito: mismo criterio de sizing que Vaultwarden, no se justifica un motor de DB separado para uso personal.

```bash
docker compose up -d
```

## Primer acceso

Hecho: cuenta admin creada por el instalador web (SQLite, sin tocar el resto de los defaults), credencial guardada en Vaultwarden y rotada después de haber pasado por chat en algún momento del proceso — no quedó ninguna contraseña real en este repo ni en el historial de Git.

Pendiente de validar: clonar un repo de prueba por SSH contra `ssh://git@git.oscar.home:2222/<usuario>/<repo>.git` para confirmar el puerto 2222 antes de depender de él para algo real.

## Reverse proxy — Nginx Proxy Manager

`http://git.oscar.home:3000` funcionaba, pero con puerto en la URL. Primer intento: un nginx standalone propio en `devops01` (network_mode: host, rutéo por hostname en el puerto 80) — funcionó, pero dejaba dos reverse proxies corriendo en paralelo en el homelab, porque [Nginx Proxy Manager](./nginx-proxy-manager.md) ya existía en `core01` sin usarse (login de fábrica sin cambiar en ese momento). Al confirmar que el login de NPM ya había sido cambiado —quedó desactualizado en su propia página, no en la realidad— se migró: el nginx standalone se bajó (`docker compose down` en `devops01`) y el Proxy Host quedó armado en NPM en su lugar. El detalle del Proxy Host, credenciales y troubleshooting vive en [Nginx Proxy Manager](./nginx-proxy-manager.md#proxy-hosts-reales), no se repite acá.

Cambio de arquitectura real: `git.oscar.home` (rewrite en AdGuard) ahora apunta a **`192.168.0.156`** (`core01`, donde corre NPM), no a `192.168.0.151` (`devops01`, donde corre Forgejo) — NPM es el frente, Forgejo es el backend (`forward_host: 192.168.0.151`, `forward_port: 3000`). `FORGEJO_ROOT_URL` sigue en `http://git.oscar.home/`, sin cambios — el hostname que ve el usuario es el mismo, solo cambió qué máquina lo atiende primero.

## Nota sobre AdGuard (dependencia real de `git.oscar.home`)

AdGuard (`192.168.0.93`) sigue arriba y respondiendo bien, pero **no es el DNS de toda la LAN** — no hay DHCP apuntándolo (se evitó a propósito: hacerlo DNS de red completa coincidió con una caída real de throughput, 600→20 Mbps, causa todavía sin diagnosticar). El método real usado en las máquinas de administración es una entrada en `/etc/hosts` (`192.168.0.156 git.oscar.home`), no el DNS del sistema — ver [Cómo resuelven hoy las máquinas de administración](../red/dns-adguard.md#cómo-resuelven-hoy-las-máquinas-de-administración). No es automático para cualquiera que se conecte a la LAN.

## Pendiente real

- **Migrar `oscar-gitops`** (hoy en GitHub) a Forgejo como origen o mirror — decisión de producto separada, no bloquea tener Forgejo corriendo.
- **CI Runner (Forgejo Actions)** — la VM ya tiene RAM/CPU de sobra reservada para esto (ver "Sizing real" arriba), pero el runner en sí todavía no está desplegado.
- **Diagnosticar la caída de velocidad de AdGuard** (ver nota arriba) — hasta resolverlo, `git.oscar.home` sigue dependiendo de configurar DNS a mano por dispositivo.
- **Acceso remoto** — hoy Forgejo es LAN-only (`git.oscar.home` solo resuelve dentro de la red), correcto para esta etapa. Si en algún momento hace falta clonar/pushear desde afuera, la vía elegida es VPN (Tailscale, ver [backlog](../roadmap/backlog.md#decisiones-pendientes)) para SSH/administración, no exponer Forgejo directo por Cloudflare Tunnel — y si igual se decide exponer HTTP público, el SSH del puerto 2222 quedaría LAN/VPN-only de todas formas (tunelear TCP crudo es bastante más trabajo que el ingress HTTP simple que ya usan los otros 7 servicios).

## Ejemplo concreto

Ejemplo: repo `oscar-gitops` con manifests k3s; Argo CD observa el repo y sincroniza aplicaciones internas.

## Checklist de despliegue

- [x] hostname y ubicación decididos (`devops01`, `git.oscar.home` vía AdGuard);
- [x] imagen/versión fijada, evitando tags flotantes en servicios importantes (`16.0.4`);
- [x] puertos documentados (3000 HTTP, 2222 SSH externo → 22 interno);
- [x] volumen/persistencia definida (`/srv/oscar/data/forgejo`);
- [x] `.env.example` sin secretos en Git — no aplica todavía: nada de esto vive en un repo Git, solo en la VM;
- [x] credenciales reales fuera de Git (admin creado, credencial en Vaultwarden, rotada tras pasar por chat);
- [ ] backup definido antes de cargar datos importantes (`forgejo dump`, ver abajo — no automatizado todavía);
- [x] healthcheck o monitor de disponibilidad (`/api/healthz` responde `pass`; falta sumarlo a Uptime Kuma);
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado.

## Seguridad

La plataforma Git es Forgejo ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)). GitOps ya está acoplado a Git en general (Argo CD sincroniza desde `oscar-gitops`), no a Forgejo específicamente — migrar de `oscar-gitops` en GitHub a un mirror/origen en Forgejo es un paso de despliegue posterior, no un cambio de arquitectura.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Forgejo trae un comando de backup integrado, `forgejo dump`, que genera un único archivo comprimido con la base de datos, los repositorios Git completos, LFS y la configuración (`app.ini`) en un solo paso consistente. Es el mecanismo recomendado en vez de copiar directorios a mano.

Ese archivo debe salir del host inmediatamente: es una copia completa del código fuente que aloja el servidor Git interno.

Restore: `forgejo dump` genera un artefacto pensado para restaurarse en una instancia nueva siguiendo la guía oficial de "restore from dump". El restore debe probarse al menos una vez con un dump real; no asumir que funciona.

## Observabilidad

- endpoint `/api/healthz`;
- uso de disco del árbol de repositorios (crece con el tiempo, especialmente con LFS);
- jobs de Actions fallando, si se usa CI integrado;
- disponibilidad HTTP/SSH;
- reinicios del proceso/contenedor.

## Troubleshooting

- **`git push` falla con timeout** → disco lleno o proceso Forgejo sin memoria → ver [Disco lleno](../runbooks/disco-lleno.md), revisar espacio del volumen de repos y logs del contenedor.
- **`/api/healthz` no responde pero el contenedor está `Up`** → DB inaccesible o proceso colgado → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), revisar logs de conexión a la base.
- **Un `forgejo dump` falla o queda incompleto** → falta de espacio temporal en disco durante el dump, o LFS muy grande para el timeout configurado → ver [Backup fallido](../runbooks/backup-fallido.md), revisar espacio libre y logs del dump.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://forgejo.org/docs/
