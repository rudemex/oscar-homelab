---
title: Portainer
sidebar_position: 28
---

# Portainer

**Estado:** Actual — Portainer CE 2.21.4 corriendo en `core01` (server), Agent en `devops01`, ambos endpoints conectados y sanos
**Dónde corre:** server en Docker Core (`/srv/oscar/apps/portainer/`), agente en `devops01` (`/srv/oscar/apps/portainer-agent/`)
**Sizing inicial:** liviano, sin límites propios en el compose
**Red/puertos:** `http://portainer.oscar.home` (vía [Nginx Proxy Manager](./nginx-proxy-manager.md#proxy-hosts-reales) en `core01`, que proxea a `192.168.0.156:9443`) — igual que `git.oscar.home`/`nexus.oscar.home`, sin HTTPS del lado público (NPM habla HTTPS con Portainer del otro lado, eso es interno); `9000`/`9443` siguen respondiendo directo por IP también. Agente en `devops01:9001`.
**Persistencia:** volumen nombrado `portainer-data` (usuarios, configuración de endpoints) — sin datos de aplicación real, todo reconstruible

## Por qué existe, y su límite de uso deliberado

No estaba en `OSCAR_TARGET_ARCHITECTURE.md` — se sumó aparte porque no había ninguna forma de ver contenedores/logs de `core01` y `devops01` en un solo lugar sin saltar de SSH en SSH. Ni Beszel ni Uptime Kuma ni el futuro Grafana cubren eso: son observabilidad de métricas/disponibilidad, no una consola de contenedores.

**Regla de uso, a propósito:** Portainer acá es **solo para mirar** — estado de contenedores, logs, reinicios puntuales de algo que se colgó. Toda la config real (qué imagen, qué puerto, qué volumen) sigue viviendo en los `compose.yaml` versionados en Git, igual que siempre. No se despliegan ni editan stacks desde la UI de Portainer — si algo se cambia ahí en vez de en Git, la próxima vez que alguien mire el repo pensando que es la fuente de verdad, no va a coincidir con la realidad. Es una decisión de disciplina operativa, no una restricción técnica (es la misma cuenta admin la que podría hacerlo) — vale la misma lógica que ya se aplicó con Portainer en el resto del proyecto: todo reproducible desde Git.

## Instalación

`compose.yaml` del server (`core01`):

```yaml
services:
  portainer:
    image: portainer/portainer-ce:${PORTAINER_VERSION}
    container_name: portainer
    restart: unless-stopped
    ports:
      - "9000:9000"
      - "9443:9443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer-data:/data

volumes:
  portainer-data:
```

`.env`: `PORTAINER_VERSION=2.21.4`

`compose.yaml` del agente (`devops01`):

```yaml
services:
  portainer-agent:
    image: portainer/agent:${PORTAINER_VERSION}
    container_name: portainer-agent
    restart: unless-stopped
    ports:
      - "9001:9001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
```

```bash
docker compose up -d
```

## Primer acceso

Portainer exige crear la cuenta admin dentro de una ventana corta después del primer arranque, o se autobloquea. Se hizo por API en vez de por UI (mismo resultado, sin depender de tener el navegador a mano justo en ese momento):

```bash
curl -sk -X POST https://<IP-core01>:9443/api/users/admin/init \
  -H "Content-Type: application/json" \
  -d '{"Username":"<TU_USUARIO>","Password":"<TU_PASSWORD_AQUI>"}'
```

Credencial real generada con `openssl rand`, guardada en Vaultwarden — no quedó en ningún archivo ni en este repo.

**Registrar los dos endpoints** (uno por comando, con el JWT de `/api/auth`):

```bash
# core01 — el propio socket local del server, vía type=1
curl -sk -X POST https://<IP-core01>:9443/api/endpoints \
  -H "Authorization: Bearer $TOKEN" \
  -F "Name=core01" -F "EndpointCreationType=1"

# devops01 — vía el agente remoto, type=2
curl -sk -X POST https://<IP-core01>:9443/api/endpoints \
  -H "Authorization: Bearer $TOKEN" \
  -F "Name=devops01" -F "EndpointCreationType=2" \
  -F "URL=tcp://<IP-devops01>:9001" \
  -F "TLS=true" -F "TLSSkipVerify=true" -F "TLSSkipClientVerify=true"
```

**Gotcha real:** registrar el agente con `TLS=true` sin `TLSSkipVerify=true` falla con `x509: certificate is valid for <IP-interna-del-contenedor>, not <IP-del-host>` — el certificado autofirmado del agente está armado para su IP interna de Docker, no para la IP LAN del host. El agente igual viaja cifrado, solo no valida el hostname del cert — razonable para un endpoint interno de la LAN, no se expondría así a Internet.

## Rol dentro de O.S.C.A.R.

- consola de contenedores/logs de `core01` + `devops01` en un solo lugar
- diagnóstico rápido (por qué está reiniciando esto, qué logs tiene) sin SSH
- explícitamente no reemplaza `compose.yaml` en Git como fuente de verdad

## Checklist de despliegue

- [x] hostname y ubicación decididos (`core01` server, `devops01` agente);
- [x] imagen/versión fijada (`2.21.4`, no `latest`);
- [x] puertos documentados (`9000`/`9443` server, `9001` agente);
- [x] volumen/persistencia definida (`portainer-data`);
- [x] credenciales reales fuera de Git (admin creado por API, password en Vaultwarden);
- [x] monitor de disponibilidad — sumado a Uptime Kuma (`Portainer (core01)`);
- [ ] no expuesto públicamente — hoy solo accesible por IP en la LAN, no tiene entrada en Cloudflare Tunnel a propósito (panel de administración con acceso a Docker socket, mismo criterio que Nexus/NPM);
- [ ] backup — no aplica en el sentido tradicional (sin datos de aplicación real), pero si se pierde `portainer-data` hay que re-registrar los endpoints a mano.

## Seguridad

El socket de Docker montado (`/var/run/docker.sock`) le da a quien tenga acceso a Portainer control total sobre los contenedores del host — mismo riesgo que cualquier herramienta que monte el socket. Por eso no está publicado por Cloudflare Tunnel ni tiene Access delante: solo alcanzable desde la LAN.

## Troubleshooting

- **Registrar un endpoint de agente falla con error de certificado** → ver el gotcha en "Primer acceso" — usar `TLSSkipVerify=true`.
- **La cuenta admin quedó bloqueada** → Portainer exige crear el admin dentro de una ventana corta tras el primer arranque; si se pasó, hay que borrar el volumen `portainer-data` y arrancar de cero (se pierde la config de endpoints, hay que re-registrarlos).
- **`https://portainer.oscar.home` tira `SSL routines: tlsv1 unrecognized name`** → el Proxy Host en NPM se creó sin certificado (`ssl_forced: false`, igual que el resto de los `*.oscar.home`), así que el puerto 443 de NPM no tiene ningún server block TLS para ese hostname — el cliente manda SNI, nginx no encuentra coincidencia, corta la conexión. Usar `http://` (puerto 80), no `https://`, del lado público — NPM habla HTTPS con Portainer del otro lado igual, eso no depende del esquema que usa el cliente.
- **Homepage no resuelve ningún `*.oscar.home` desde sus propios chequeos (`siteMonitor`)** → encontrado al agregar esta misma tarjeta: `core01` nunca tuvo su DNS apuntado a AdGuard (`/etc/netplan/50-cloud-init.yaml` tenía `8.8.8.8` fijo desde que se creó la VM, ver [crear VM core01](../proxmox/crear-vm-core01.md)) — a diferencia de `devops01`, que sí se corrigió esta sesión (ver [gotcha de DNS del CI Runner](./ci-runner.md)). Ningún contenedor de `core01` podía resolver `git.oscar.home`/`nexus.oscar.home`/`portainer.oscar.home` hasta corregir el DNS del host (`nameservers: [192.168.0.93, 1.1.1.1]` en el netplan + `netplan apply`) — no había aparecido antes porque ninguna tarjeta de Homepage usaba esos hostnames en su `siteMonitor`, todas apuntaban por IP.
