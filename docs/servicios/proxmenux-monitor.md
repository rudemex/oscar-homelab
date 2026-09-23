---
title: ProxMenux Monitor
sidebar_position: 23
---

# ProxMenux Monitor

**Estado:** Actual · Observabilidad — corriendo en `oscar-core` (el host de Proxmox, no una VM/LXC)
**Dónde corre:** systemd en el propio hipervisor (`proxmenux-monitor.service`), instalado por [ProxMenux](https://github.com/MacRimi/ProxMenux)
**Sizing inicial:** liviano (Flask + Python), sin containerizar
**Red/puertos:** `8008` HTTP interno en `oscar-core` — acceso real vía [Cloudflare Tunnel](./cloudflare-tunnel.md) en `monitor.oscarlab.com.ar`
**Persistencia:** ninguna relevante — es un dashboard de métricas en vivo, sin base de datos propia

## Rol dentro de O.S.C.A.R.

Dashboard web de ProxMenux (toolkit de instalación/administración de Proxmox por menú interactivo) con visibilidad en tiempo real de CPU, RAM, disco y red del hipervisor — sin necesitar terminal. Es un complemento a Beszel/Uptime Kuma, específico del propio Proxmox en vez de los servicios que corren sobre él.

A diferencia del resto del stack de O.S.C.A.R., **no vive en Docker ni en `core`**: se instaló directo en `oscar-core` como parte del toolkit ProxMenux, corriendo como servicio systemd nativo.

## Instalación

ProxMenux (el toolkit completo, no solo el Monitor) se instala con:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/MacRimi/ProxMenux/main/install_proxmenux.sh)"
```

El Monitor se instala automáticamente como parte de esa instalación estándar y queda corriendo como servicio systemd (arranca solo en boot):

```bash
systemctl status proxmenux-monitor
systemctl restart proxmenux-monitor
journalctl -u proxmenux-monitor -n 50
```

## Publicación vía Cloudflare Tunnel

`cloudflared` corre en `core`, no en `oscar-core` — son máquinas distintas en la misma LAN. La regla de ingress del túnel apunta explícitamente a la IP LAN de `oscar-core` (`http://192.168.0.233:8008`), no a `localhost` como el resto de los servicios que sí conviven con `cloudflared` en `core`. Es el único de los seis hostnames publicados con esa particularidad — ver [Cloudflare Tunnel](./cloudflare-tunnel.md).

## Seguridad

- muestra métricas del hipervisor completo — mismo nivel de sensibilidad que Proxmox mismo en términos de qué revela sobre la infraestructura, aunque no permite control (es de solo lectura);
- va detrás de [Cloudflare Access](./cloudflare-tunnel.md) igual que el resto de lo publicado;
- corre con los privilegios del servicio systemd en el propio hipervisor — a diferencia de todo lo demás en O.S.C.A.R., no está aislado en un contenedor.

## Backup y restore

No hay estado propio que respaldar — es un dashboard en vivo. Si se pierde, reinstalar ProxMenux reconstruye el Monitor completo.

## Observabilidad

Disponibilidad HTTP del puerto 8008 alcanza — no es un servicio con estado crítico.

## Troubleshooting

- **El servicio no responde** → `systemctl status proxmenux-monitor` y `journalctl -u proxmenux-monitor -n 50` en `oscar-core` directamente (no hay `docker logs`, no es un contenedor).
- **`monitor.oscarlab.com.ar` no resuelve o da error de Cloudflare** → confirmar que la regla de ingress sigue apuntando a la IP LAN de `oscar-core` y no a `localhost` — ver nota arriba, es la excepción entre los servicios publicados.

## Documentación oficial

https://github.com/MacRimi/ProxMenux
