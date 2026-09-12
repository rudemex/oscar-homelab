---
title: Nginx Proxy Manager
sidebar_position: 26
---

# Nginx Proxy Manager

**Estado:** Actual · Infraestructura — corriendo en `core01`
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

## Primer acceso — pendiente

NPM arranca con un login por defecto (`admin@example.com` / `changeme`) que hay que cambiar entrando a `http://192.168.0.156:81` — hasta que eso no se haga, no hay credenciales reales para sumarle el widget de Homepage (que necesita usuario/contraseña reales, no los de fábrica). Card agregada sin `widget:` por ahora, solo `href` + `siteMonitor`.

## Configuración en Homepage

```yaml
- Nginx Proxy Manager:
    href: http://192.168.0.156:81
    description: Reverse proxy interno — pendiente completar el primer login para sumarle el widget
    icon: nginx-proxy-manager.png
    siteMonitor: http://192.168.0.156:81
```

Una vez creada la cuenta real, sumar:

```yaml
    widget:
      type: npm
      url: http://192.168.0.156:81
      username: "usuario@real.com"
      password: "contraseña real"
```

(comillas recomendadas, sobre todo en el usuario si tiene `@`).

## Seguridad

- **Cambiar el login por defecto es prioritario** — mientras siga en `admin@example.com`/`changeme`, cualquiera en la LAN con la IP puede administrar el proxy;
- no está publicado por el Tunnel — solo alcanzable dentro de la LAN;
- los puertos 80/443 quedan abiertos en `core01` para lo que NPM enrute — repasar qué termina pasando por ahí a medida que se usa.

## Backup y restore

`./data` y `./letsencrypt` tienen toda la config de proxy hosts y certificados — vale la pena respaldarlos una vez que haya reglas reales cargadas (hoy está vacío, recién instalado).

## Observabilidad

Pendiente sumar un chequeo en Uptime Kuma sobre el puerto 81.

## Troubleshooting

- **No puedo entrar con el login de fábrica** → confirmar que se está usando `admin@example.com` / `changeme` en el primer arranque; si ya se cambió, no hay reset sin acceso a los archivos de `./data`.
- **El widget de Homepage no autentica** → confirmar que el usuario/contraseña son los reales (no los de fábrica) y que el email va entre comillas en el YAML.

## Documentación oficial

https://nginxproxymanager.com/
