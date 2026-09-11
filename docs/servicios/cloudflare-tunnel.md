---
title: Cloudflare Tunnel + Access
sidebar_position: 14
---

# Cloudflare Tunnel + Access

**Estado:** Actual — túnel `core01` corriendo y conectado, ingress configurado para 5 servicios, Cloudflare Access habilitado con una Access Application + política por servicio (solo el email del autor, código de un solo uso), y los 5 registros DNS ya publicados y protegidos
**Dónde corre:** `core01` (`/srv/oscar/apps/cloudflared/`), `network_mode: host`
**Sizing inicial:** muy bajo (~20-30 MB RAM)
**Red/puertos:** solo conexiones salientes (QUIC/HTTP2 hacia el edge de Cloudflare); ningún puerto inbound en el router
**Persistencia:** el token del túnel (`TUNNEL_TOKEN` en `.env`) — la configuración de ingress vive en Cloudflare (`config_src: cloudflare`), no en un `config.yml` local

## Rol dentro de O.S.C.A.R.

- publicar Vaultwarden, n8n, Uptime Kuma, Homepage y Beszel sin abrir puertos ni depender de certificados self-signed
- reemplaza el intento anterior con Caddy + `tls internal` para Vaultwarden, que nunca terminó de funcionar bien en el navegador
- acceder con identidad (Cloudflare Access) en vez de VPN para lo administrativo

## Estado real del despliegue

`network_mode: host` es deliberado (mismo criterio que [Beszel](./beszel.md)): así el túnel llega a cada servicio vía `http://localhost:<puerto>` sin importar en qué red Docker viva cada compose por separado.

Ingress configurado (vía API, `config_src: cloudflare`):

| Hostname | Servicio interno |
|---|---|
| `vault.oscarlab.com.ar` | `http://localhost:8082` (Vaultwarden, publicado solo en loopback) |
| `kuma.oscarlab.com.ar` | `http://localhost:3001` |
| `n8n.oscarlab.com.ar` | `http://localhost:5678` |
| `home.oscarlab.com.ar` | `http://localhost:3005` |
| `beszel.oscarlab.com.ar` | `http://localhost:8090` |
| *(catch-all)* | `http_status:404` |

Orden que se siguió (importa para no dejar una ventana pública sin protección): primero se creó la Access Application + política de cada hostname, y **recién después** el registro DNS (`CNAME` → `<tunnel-id>.cfargotunnel.com`, `proxied: true`) — así, en el instante exacto en que cada hostname empezó a resolver, Access ya estaba interceptando. Crear el DNS antes que la política habría dejado el servicio público sin nada delante durante esa ventana.

Cada Access Application usa el método de login por defecto de Cloudflare (código de un solo uso enviado por email) — no hizo falta configurar ningún proveedor de identidad externo, alcanza con la política `include: email == <el único usuario real>`.

Pendiente real: **`kuma.oscarlab.com.ar` y `home.oscarlab.com.ar`** quedaron con la misma política restrictiva que el resto por prolijidad, pero son candidatos a relajar más adelante si se quiere una página de estado o un dashboard público sin login — evaluarlo caso por caso, no por defecto.

## Ejemplo concreto

`vault.oscarlab.com.ar` → Cloudflare Access (MFA) → Tunnel → Vaultwarden interno.

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

Tunnel no convierte automáticamente un servicio en privado. Agregar Access/políticas cuando el hostname no deba ser público.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El servicio en sí es prácticamente stateless. Lo único que hay que respaldar son dos archivos pequeños pero críticos:

- el JSON de credenciales del túnel (`<tunnel-id>.json`) — es un secreto, nunca en el mismo repo Git en texto plano, tratarlo como cualquier otro secreto;
- `config.yml` (reglas de ingress) — sí puede versionarse en Git si no contiene secretos.

Las políticas de Cloudflare Access (identidad, MFA, reglas de quién entra a qué) viven en el dashboard de Cloudflare, no en el host. Hoy no hay backup/export automatizado de esas políticas; queda pendiente resolver esto más adelante, por ejemplo exportándolas vía API/Terraform si se adopta IaC de Cloudflare.

Restore: recrear el túnel desde cero con `cloudflared tunnel create` es rápido si se pierden las credenciales (hay que volver a autorizar DNS). El riesgo real no es "perder el túnel" sino perder la definición de las políticas de Access sin tener dónde reconstruirlas rápido.

## Observabilidad

- estado de la conexión del daemon `cloudflared` (métricas locales en `/metrics`, o el dashboard de Cloudflare Zero Trust);
- latencia agregada reportada por Cloudflare;
- certificado/DNS del hostname público;
- reinicios del proceso/contenedor del daemon;
- logs de errores de conexión del túnel.

## Troubleshooting

- **El hostname público no responde pero el servicio local sí** → túnel caído o DNS mal apuntado en Cloudflare → `cloudflared tunnel info <tunnel>`, revisar logs del daemon; ver [DNS caído](../runbooks/dns-caido.md) si el problema es de resolución.
- **Cloudflare Access no pide autenticación (o rechaza a todos)** → política mal configurada o cambiada manualmente en el dashboard sin registro → revisar la política en Zero Trust → Access, comparar contra la última configuración conocida.
- **El daemon `cloudflared` reinicia en loop** → credenciales del túnel inválidas o revocadas → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), regenerar credenciales con `cloudflared tunnel create` si corresponde.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
