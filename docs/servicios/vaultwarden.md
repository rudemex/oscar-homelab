---
title: Vaultwarden
sidebar_position: 20
---

# Vaultwarden

**Estado:** Actual · Seguridad — corriendo en `core01`
**Dónde corre:** Docker Core (`/srv/oscar/apps/vaultwarden/`)
**Sizing inicial:** ~100 MB RAM, prácticamente sin CPU
**Red/puertos:** `8087` HTTP interno — sin dominio/TLS todavía, solo LAN
**Persistencia:** base de datos SQLite + adjuntos, en `./data`

## Rol dentro de O.S.C.A.R.

Servidor compatible con el protocolo de Bitwarden (reimplementación en Rust, mucho más liviano que el Bitwarden oficial self-hosted). Se usa con cualquier cliente oficial de Bitwarden (extensión de navegador, apps móviles, CLI) apuntando a este servidor en vez de a bitwarden.com.

Existe puntualmente para resolver un problema real detectado durante la construcción de O.S.C.A.R.: reutilización de la misma contraseña entre Proxmox y el router. Un gestor de contraseñas propio elimina la excusa de "es más fácil reutilizar".

## Instalación

```bash
mkdir -p /srv/oscar/apps/vaultwarden/data
```

`.env`:

```dotenv
VAULTWARDEN_VERSION=1.37.2
DOMAIN=http://localhost:8087
SIGNUPS_ALLOWED=true
ADMIN_TOKEN=CHANGE_ME_OPENSSL_RAND_BASE64_48
```

`compose.yaml`:

```yaml
services:
  vaultwarden:
    image: vaultwarden/server:${VAULTWARDEN_VERSION}
    restart: unless-stopped
    environment:
      DOMAIN: ${DOMAIN}
      SIGNUPS_ALLOWED: ${SIGNUPS_ALLOWED}
      ADMIN_TOKEN: ${ADMIN_TOKEN}
      WEB_VAULT_ENABLED: "true"
    volumes:
      - ./data:/data
    ports:
      - "8087:80"
```

```bash
docker compose up -d
```

## Primer acceso

1. Entrar a `http://<IP-de-core01>:8087`, crear la primera cuenta real (email + master password — la master password nunca se comparte, ni siquiera con quien administra el servidor).
2. **Apenas exista esa cuenta, poner `SIGNUPS_ALLOWED=false`** en `.env` y `docker compose up -d` de nuevo — sin esto, cualquiera con la URL puede crearse una cuenta.
3. Instalar la extensión/app oficial de Bitwarden en cada dispositivo, y en "Self-hosted environment" apuntar a la URL de arriba en vez de bitwarden.com.

## Seguridad

- **`SIGNUPS_ALLOWED=false` después del primer usuario** es el punto más importante — ver arriba.
- `ADMIN_TOKEN` da acceso al panel `/admin` (gestión de usuarios, configuración global) — tratarlo como cualquier otro secreto crítico, nunca en Git.
- Hoy corre sin TLS propio, solo accesible en LAN — no exponer este puerto a Internet tal cual. Antes de cualquier acceso remoto real, esto necesita HTTPS (Cloudflare Tunnel u otro reverse proxy con certificado), porque WebAuthn/passkeys y algunas integraciones de Bitwarden requieren HTTPS o `localhost` estricto.
- La master password del usuario **nunca** se puede recuperar si se pierde — a diferencia de una cuenta normal, no hay "olvidé mi contraseña" real: perderla significa perder acceso a todo lo guardado. Vale la pena escribirla en un lugar físico seguro (no digital) como respaldo de último recurso.

## Backup y restore

Todo el estado vive en `./data`: la base SQLite (`db.sqlite3`) con las contraseñas cifradas y los archivos adjuntos. El cifrado es de extremo a extremo (la master password nunca sale del cliente), así que un backup del directorio `data/` es seguro de mover/almacenar aunque el destino no sea 100% confiable — igual conviene tratarlo como sensible por defecto.

```bash
docker compose exec vaultwarden sh -c "tar -czf /data/vw-backup.tar.gz -C /data --exclude=vw-backup.tar.gz ."
docker compose cp vaultwarden:/data/vw-backup.tar.gz ./vw-backup-$(date +%F).tar.gz
```

Restore: detener el contenedor, reemplazar `./data` por el contenido del backup, iniciar de nuevo.

## Observabilidad

- disponibilidad HTTP del puerto 8087;
- tamaño de `./data` (crece lento, solo con adjuntos grandes);
- logs del contenedor por intentos de login fallidos repetidos (fuerza bruta).

## Troubleshooting

- **No se puede crear la primera cuenta** → `SIGNUPS_ALLOWED` no está en `true`, o el contenedor no arrancó → revisar `.env` y `docker compose logs vaultwarden`.
- **El cliente Bitwarden dice "servidor no compatible" o falla el login** → URL del `DOMAIN` mal configurada, o falta HTTPS para alguna función específica (passkeys) → confirmar que `DOMAIN` en `.env` coincide con la URL real usada desde el cliente.
- **Olvidaste la master password** → no hay recuperación real sin haberla anotado en otro lado; es una limitación de diseño (cifrado end-to-end), no un bug.
