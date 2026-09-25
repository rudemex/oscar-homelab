---
title: Nginx Proxy Manager
sidebar_position: 26
---

# Nginx Proxy Manager

**Estado:** Actual · Infraestructura — corriendo en `core`
**Dónde corre:** Docker Core (`/srv/oscar/apps/nginx-proxy-manager/`)
**Sizing inicial:** liviano
**Red/puertos:** `80` (HTTP), `81` (admin web), `443` (HTTPS)
**Persistencia:** `./data` (config/certs) y `./letsencrypt` (certificados), ambos con volumen

## Rol dentro de O.S.C.A.R.

Reverse proxy interno con UI propia — pensado para enrutar/dar TLS a servicios de la LAN que no necesitan pasar por Cloudflare Tunnel (que ya cubre la publicación pública de todo lo que sí sale a Internet). No reemplaza al Tunnel: son dos capas distintas — el Tunnel publica sin abrir puertos hacia afuera, NPM organiza tráfico *adentro* de la LAN.

:::caution Redundancia a vigilar
Cloudflare Tunnel + Access ya resuelve "publicar sin abrir puertos" para todo lo que sale a Internet. Si NPM termina usándose para lo mismo (exponer algo hacia afuera) en vez de para reverse-proxy puramente interno, hay dos herramientas resolviendo el mismo problema — repasar el [criterio de adopción](./catalogo.md#criterio-de-adopción) si eso pasa.
:::

## Instalación

```bash
mkdir -p /srv/oscar/apps/nginx-proxy-manager/data /srv/oscar/apps/nginx-proxy-manager/letsencrypt
```

`compose.yaml`:

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:${NPM_VERSION}
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      - "80:80"
      - "81:81"
      - "443:443"
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
```

`.env`: `NPM_VERSION=2.15.1`

```bash
docker compose up -d
```

## Primer acceso — hecho

El login de fábrica (`admin@example.com`/`changeme`) ya fue cambiado por una cuenta real (`mdelgado@tresdoce.com.ar`) — quedó documentado acá como "pendiente" bastante después de que dejó de serlo; confirmado al intentar loguearse con las credenciales de fábrica y recibir `"Invalid email or password"`.

## Proxy Hosts reales

| Dominio | Forward a | Nota |
|---|---|---|
| `git.oscar.home` | `http://192.168.0.151:3000` ([Forgejo](./forgejo.md), `devops`) | primer Proxy Host real, creado vía API (`POST /api/nginx/proxy-hosts`) |
| `nexus.oscar.home` | `http://192.168.0.151:8081` ([Nexus](./nexus.md), `devops`, UI/API) | segundo Proxy Host — verificado con `curl` devolviendo `200`. El registry Docker (`:8082`) no pasa por acá, se usa directo por IP (ver [Nexus](./nexus.md)) |

Antes de esto, `git.oscar.home` (rewrite en AdGuard) apuntaba directo a `192.168.0.151` con un nginx standalone corriendo en la propia `devops` haciendo de reverse proxy por hostname — se migró acá para no mantener dos reverse proxies en paralelo (ver la nota de duplicación que existió en el [backlog](../roadmap/backlog.md)). El rewrite de AdGuard para `git.oscar.home` y `nexus.oscar.home` apunta a `192.168.0.156` (`core`, donde corre NPM), no a `192.168.0.151` directo — NPM es quien resuelve a qué backend real mandar cada request.

Las apps que corren en k3s (`led`, `argocd`, `ci-demo`, ...) **no** pasan por acá — tienen su propio reverse proxy (Traefik, nativo de k3s) y resuelven por un wildcard DNS directo a `k3s`, a propósito, para no atar su disponibilidad a que `core`/NPM esté arriba. Ver [DNS con AdGuard Home](../red/dns-adguard.md#wildcard-oscarhome-para-apps-de-k3s-2026-09-15).

## Configuración en Homepage

Hecho — el widget nativo ya está sumado (quedó documentado acá como "pendiente del login" bastante después de que el login ya se había cambiado, mismo patrón de doc-desactualizada-no-infra-real que pasó más de una vez en este proyecto):

```yaml
- Nginx Proxy Manager:
    href: http://192.168.0.156:81
    description: Reverse proxy interno — enruta git.oscar.home y nexus.oscar.home hacia devops
    icon: nginx-proxy-manager.png
    siteMonitor: http://192.168.0.156:81
    widget:
      type: npm
      url: http://192.168.0.156:81
      username: "<TU_EMAIL_ADMIN_NPM>"      # el mismo que usás para loguearte en :81
      password: "<TU_PASSWORD_ADMIN_NPM>"   # cambiar por el real, nunca commitear el valor real
      fields: ["enabled", "disabled", "total"]
```

Comillas recomendadas en `username`/`password`, sobre todo si el email tiene `@`.

## Seguridad

- login de fábrica ya cambiado (ver arriba) — no exponer estas credenciales reales en Git bajo ningún concepto;
- no está publicado por el Tunnel — solo alcanzable dentro de la LAN;
- los puertos 80/443 quedan abiertos en `core` para lo que NPM enrute — repasar qué termina pasando por ahí a medida que se usa.

## Backup y restore

`./data` y `./letsencrypt` tienen toda la config de proxy hosts y certificados — ahora que hay una regla real cargada (`git.oscar.home`), vale la pena respaldarlos; ya no está vacío como cuando se escribió esta página.

## Observabilidad

Pendiente sumar un chequeo en Uptime Kuma sobre el puerto 81.

## Troubleshooting

- **El widget de Homepage no autentica** → confirmar que el usuario/contraseña son los reales y que el email va entre comillas en el YAML.
- **Un Proxy Host devuelve 502/504** → el backend (`forward_host`/`forward_port`) no responde — confirmar que el servicio de destino está `Up` y alcanzable desde `core` antes de sospechar de NPM.

## Documentación oficial

https://nginxproxymanager.com/
