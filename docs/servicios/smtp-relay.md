---
title: Relay SMTP (Brevo)
sidebar_position: 27
---

# Relay SMTP

**Estado:** Actual — `boky/postfix` corriendo en `core01`, relay-only hacia Brevo, validado con envío real (`status=sent`, aceptado por Brevo)
**Dónde corre:** Docker Core (`/srv/oscar/apps/smtp-relay/`)
**Sizing inicial:** liviano, contenedor postfix minimal
**Red/puertos:** `25` (SMTP interno, LAN-only — ningún servicio externo debería pegarle directo)
**Persistencia:** ninguna real — sin volúmenes nombrados a propósito (ver "Bug encontrado" abajo)

## Rol dentro de O.S.C.A.R.

Punto único de salida de mail para cualquier servicio del homelab (Forgejo, n8n, lo que sea) — cada app le habla a `core01:25` sin autenticación (confía en la LAN), y el relay reenvía autenticado hacia Brevo con TLS. Evita repetir la credencial de Brevo en el `compose.yaml` de cada servicio.

Se eligió un relay propio en vez de un servidor de correo completo (recibir+enviar) a propósito — ver la discusión de arquitectura que llevó a esta decisión en el historial del proyecto: un servidor de correo completo en un ISP residencial tiene problemas reales de entregabilidad (puerto 25 saliente bloqueado, rangos de IP residencial blocklisteados de fábrica).

## Instalación

`.env`:

```dotenv
RELAYHOST=[smtp-relay.brevo.com]:587
RELAYHOST_USERNAME=<login SMTP de Brevo, formato numerico@smtp-brevo.com>
RELAYHOST_PASSWORD=<SMTP key de Brevo — NO la API key general>
ALLOWED_SENDER_DOMAINS=oscar.home oscarlab.com.ar
```

`compose.yaml`:

```yaml
services:
  smtp-relay:
    image: boky/postfix:latest
    container_name: smtp-relay
    restart: unless-stopped
    ports:
      - "25:25"
    environment:
      - RELAYHOST=${RELAYHOST}
      - RELAYHOST_USERNAME=${RELAYHOST_USERNAME}
      - RELAYHOST_PASSWORD=${RELAYHOST_PASSWORD}
      - ALLOWED_SENDER_DOMAINS=${ALLOWED_SENDER_DOMAINS}
```

```bash
docker compose up -d
```

## Brevo: dos cosas no obvias antes de que ande

1. **API key general ≠ SMTP key.** Brevo separa `xkeysib-...` (API REST general) de `xsmtpsib-...` (específica para SMTP). Usar la primera como `RELAYHOST_PASSWORD` da `535 5.7.8 Authentication failed` — mismo error que una clave directamente mal escrita, sin ninguna pista de que el tipo de clave es el problema.
2. **Lista blanca de IPs.** Brevo bloquea API/SMTP desde IPs no autorizadas — el error es distinto acá, viene con un mensaje explícito (`"unrecognised IP address..."`) solo si se consulta la API REST directamente; el error de SMTP en sí sigue siendo el mismo `535` genérico, sin indicar que es un tema de IP. Se resuelve en `https://app.brevo.com/security/authorised_ips`, agregando la IP pública real de salida de la LAN (verificar con `curl ifconfig.me` desde dentro de la red, no desde donde sea que se esté administrando — pueden ser IPs distintas).

## Bug encontrado: credenciales viejas acumulándose entre reinicios

La imagen `boky/postfix` declara **volúmenes anónimos** para `/etc/postfix`, `/etc/opendkim/keys` y `/var/spool/postfix` (visible con `docker inspect <container> --format '{{json .Mounts}}'`). Docker Compose **no** los recrea en un `docker compose up -d` normal — ni siquiera cuando el container en sí se "Recreate" — solo `docker compose down -v` los elimina.

El entrypoint del contenedor agrega la credencial de `RELAYHOST_PASSWORD` a `/etc/postfix/sasl_passwd` sin limpiar entradas previas. Combinado con el volumen anónimo persistiendo entre recreaciones, cada vez que se cambiaba `RELAYHOST_PASSWORD` en `.env` y se hacía `docker compose up -d`, quedaba una línea **nueva** sumada a las **viejas** en el mismo archivo — nunca reemplazada. `postmap` compila ese archivo a un mapa `lmdb`, y con múltiples entradas para la misma clave (`[smtp-relay.brevo.com]:587`), el resultado no es determinístico: postfix seguía autenticando con una credencial vieja e inválida, mientras el `.env` ya tenía la correcta — de ahí el `535` persistente en múltiples intentos con claves distintas, todas válidas.

**Diagnóstico:** `docker exec smtp-relay cat /etc/postfix/sasl_passwd` — si aparece más de una línea para el mismo host, es este bug.

**Fix aplicado:** `docker compose down -v` (elimina los volúmenes anónimos) seguido de `docker compose up -d` — arranca con `/etc/postfix` completamente limpio, una sola credencial. Si alguna vez hay que rotar `RELAYHOST_PASSWORD` de nuevo, repetir `down -v` + `up -d`, no alcanza con `up -d` solo ni con `restart`.

## Uso desde otros servicios

Cualquier app del homelab que necesite mandar mail apunta a `192.168.0.156:25`, sin autenticación (confía en la LAN, igual que Nexus/Forgejo antes de tener credenciales reales). Ejemplo para Forgejo (no configurado todavía, queda como referencia):

```dotenv
FORGEJO__mailer__ENABLED=true
FORGEJO__mailer__SMTP_ADDR=192.168.0.156
FORGEJO__mailer__SMTP_PORT=25
FORGEJO__mailer__FROM=forgejo@oscar.home
```

## Seguridad

- el puerto 25 no tiene autenticación — es intencional (relay LAN-only), pero significa que cualquier dispositivo de la LAN puede mandar mail "como" O.S.C.A.R.; no exponer este puerto más allá de la LAN bajo ningún concepto;
- `ALLOWED_SENDER_DOMAINS` limita qué dominios de remitente acepta relayear — evita que el relay se use para spoofear remitentes arbitrarios;
- la SMTP key de Brevo es un secreto — vive solo en `.env` en `core01`, nunca en Git.

## Troubleshooting

- **`535 5.7.8 Authentication failed` con una clave que parece correcta** → revisar primero si hay más de una línea en `/etc/postfix/sasl_passwd` (ver "Bug encontrado" arriba) antes de sospechar de la clave o la cuenta de Brevo.
- **La API de Brevo devuelve `401` con mensaje de IP no reconocida** → agregar la IP pública real de la LAN en `https://app.brevo.com/security/authorised_ips`.
- **Todo parece bien configurado y sigue fallando** → generar una clave SMTP nueva desde Brevo (no reusar una vieja, puede haber quedado en un estado raro si se generó mientras la IP todavía estaba bloqueada) y limpiar los volúmenes del contenedor como en el fix de arriba.

## Documentación oficial

- Brevo SMTP: https://developers.brevo.com/docs/send-a-transactional-email
- boky/postfix: https://github.com/bokysan/docker-postfix
