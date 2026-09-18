---
title: DNS con AdGuard Home
sidebar_position: 4
---

# DNS con AdGuard Home

**Estado:** Actual — corriendo como LXC (`vmid 100`, tag `adblock;community-script`) en `oscar-core`, instalado vía el script comunitario de [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/). Desde el 2026-09-18 **es el DNS de toda la LAN de verdad**: el router (TP-Link Archer, DHCP propio — `dhcp.enabled: false` en AdGuard, no se usa su DHCP interno) reparte `192.168.0.93` como DNS primario y `1.1.1.1` como secundario a cualquier dispositivo con DNS automático. La caída de throughput que había hecho revertir esto una vez ya está diagnosticada y corregida (ver más abajo) — no fue un problema de capacidad ni de red, fue un `ratelimit` de AdGuard configurado demasiado bajo para el volumen de toda una casa.

Reemplaza a Pi-hole en el rol de DNS/adblock de O.S.C.A.R. — cubre lo mismo (bloqueo por DNS, resolución de nombres locales, visibilidad de consultas) con una UI que a algunos les resulta más cómoda y con DNS-over-HTTPS/TLS nativo si se necesita salir cifrado hacia el resolver upstream. La elección fue simplemente cuál instaló el script comunitario primero — no hay una razón técnica fuerte para preferir uno sobre otro a esta escala; si en algún momento se quiere volver a Pi-hole, el rol y el diseño de abajo aplican igual.

## Diseño recomendado

Evitar que toda la casa dependa de un único resolver. El objetivo es tener dos instancias cuando la arquitectura madure — hoy solo existe la primera:

```text
DNS1 -> AdGuard Home (LXC 100, oscar-core) — actual
DNS2 -> segunda instancia (Pi o LXC separado) — objetivo, no instalada
```

## Qué hace hoy

- bloqueo de dominios de tracking/publicidad vía listas;
- resolución de nombres locales (`*.oscar.home`) apuntando a servicios internos a medida que se crean;
- log de consultas DNS por cliente, útil para ver qué dispositivo pide qué.

## Qué no hace por sí solo

AdGuard Home no reemplaza firewall, autenticación ni filtrado TLS. Bloquear un dominio por DNS tampoco impide que un cliente alcance la IP directamente si la conoce — es una capa de higiene, no un control de seguridad fuerte.

## Backup y restore

La configuración completa (listas, clientes, DNS rewrites, log) vive en `/opt/AdGuardHome/` dentro del LXC — específicamente `AdGuardHome.yaml` (config) y la carpeta `data/` (estadísticas, que no valen la pena respaldar) . Backup real:

```bash
# desde oscar-core, respaldando la config del LXC 100
pct exec 100 -- tar -czf /tmp/adguard-backup.tar.gz -C /opt/AdGuardHome AdGuardHome.yaml
pct pull 100 /tmp/adguard-backup.tar.gz ./adguard-backup-$(date +%F).tar.gz
```

Restore: copiar el `.tar.gz` de vuelta, extraer sobre `/opt/AdGuardHome/AdGuardHome.yaml` en una instancia nueva, reiniciar el servicio (`systemctl restart AdGuardHome`).

Como LXC completo, también entra en el backup regular de Proxmox (`vzdump`) — ver [backups en Proxmox](../proxmox/backups.md#comandos-de-referencia-vzdump). Eso alcanza para la mayoría de los casos; el backup de archivo de arriba sirve para restaurar solo la config sin recrear todo el contenedor.

## Seguridad

- la UI de administración (puerto 3000 por defecto) no debe exponerse fuera de la LAN — ver [exposición a Internet](../seguridad/exposicion-internet.md);
- cambiar las credenciales por defecto del panel apenas se instala;
- si se configura DNS-over-HTTPS/TLS hacia el resolver upstream, guardar esa configuración en el backup de arriba (no es sensible por sí sola, pero es tediosa de recrear).

## Validación

```bash
nslookup grafana.oscar.home <IP-del-LXC-100>
nslookup example.com <IP-del-LXC-100>
```

Registrar latencia, errores y volumen de consultas en observabilidad una vez que exista el stack de Prometheus/Grafana — ver [runbook de DNS caído](../runbooks/dns-caido.md) si el resolver deja de responder.

## Incidente de throughput — diagnosticado (2026-09-18)

Configurar el router para repartir AdGuard por DHCP a toda la LAN había coincidido con una caída real de velocidad, 600→20 Mbps — se revirtió esa configuración y quedó anotado sin investigar a fondo (Fase 0 del plan de reorganización). Ya se diagnosticó la causa real.

**Causa real: `ratelimit: 20` en la config de AdGuard, agrupado por subred (`ratelimit_subnet_len_ipv4: 24`) — toda la LAN comparte un límite de 20 consultas DNS por segundo.** Con AdGuard como DNS de un solo dispositivo, 20/s nunca se nota. Con toda la red apuntando ahí (varios dispositivos, cada carga de página disparando 10-30 consultas de golpe por los distintos dominios de CDN/trackers/fuentes), el límite se superaba todo el tiempo — las consultas por encima del límite se descartan en silencio (sin respuesta, sin log, no llegan ni al query log), lo que hace que todo *se sienta* lentísimo aunque el ancho de banda real de internet nunca haya bajado.

**Cómo se confirmó** (con un script Python propio usando sockets UDP async — un primer intento con `dig` en background desde bash dio falsos positivos/negativos por contención de procesos del lado del cliente, se descartó tras fallar igual contra `1.1.1.1` como control):

| Prueba | Resultado |
|---|---|
| 40 consultas simultáneas contra `1.1.1.1` (control) | 40/40 — el método de prueba es válido |
| 40 consultas simultáneas contra AdGuard con `ratelimit: 300` | 40/40 |
| 40 consultas simultáneas contra AdGuard con `ratelimit: 20` (valor original) | 19/40 — el resto se pierde sin respuesta |

**Fix aplicado:** `ratelimit` subido de `20` a `300` (holgado para una LAN doméstica, sigue protegiendo contra abuso real). Config real hoy:

```yaml
dns:
  ratelimit: 300
  ratelimit_subnet_len_ipv4: 24
```

## Activado de verdad: DHCP de red completa (2026-09-18)

Con la causa raíz corregida, se activó — dejó de ser una decisión pendiente. Antes de tocar el router:

- **Backup de la config del router** (TP-Link Archer, `System Tools → Backup & Restore → Backup`) — hecho, guardado por el usuario, para poder hacer rollback si hiciera falta. El panel del router es una SPA (Vue.js) con login encriptado por RSA del lado del cliente, sin API documentada — el cambio se hizo a mano por la UI, no por script, a propósito (no hay forma segura de automatizarlo sin herramienta de navegador).
- **Cambio real**: `Advanced → Network → DHCP Server` — DNS primario `192.168.0.93`, DNS secundario `1.1.1.1` (fallback real si AdGuard se cae, ya que el DNS secundario propio del plan de reorganización — `dns02` en la Pi Zero W — todavía no existe).
- Recursos del LXC subidos antes del cambio, con margen real: 2 vCPU / 1 GB (antes 1 vCPU / 512 MB).

**Validado con tráfico real, no solo pruebas sintéticas** (un dispositivo real — Mac del usuario — renovando DHCP y navegando normal):

- El DHCP reparte bien lo configurado — confirmado con `ipconfig getpacket en0` mostrando `domain_name_server: {192.168.0.93, 1.1.1.1}`.
- **Gotcha real encontrado en el camino**: el Mac de prueba tenía DNS fijado a mano (`8.8.8.8`) en **dos** servicios de red distintos (`Wi-Fi` y, más sorprendente, un adaptador `USB 10/100/1000 LAN 4` sin uso real pero con prioridad más alta en el orden de servicios de macOS) — un override manual en cualquiera de los dos gana por sobre el DNS que reparte el DHCP, sin ningún error visible. Hubo que limpiar los dos (`networksetup -setdnsservers <servicio> Empty`) para que el sistema realmente usara lo nuevo. Si un dispositivo "no toma" el DNS nuevo del router, esta es la primera causa a revisar — no asumir que el router está mal configurado.
- Con el override limpio: `doubleclick.net` resolvió `0.0.0.0` (bloqueado por el filtro de AdGuard) — confirmación real de que el tráfico pasa por ahí, no solo que el DNS "apunta bien" en teoría.
- Durante una sesión de navegación normal: **+397 paquetes UDP entrantes** al LXC (medido en `/proc/net/snmp`), CPU y RAM sin moverse de prácticamente cero (81 MB de 1 GB). La carga real de un dispositivo navegando es insignificante para los recursos asignados — nunca fue un problema de capacidad.
- **Pendiente, no bloqueante**: el querylog persistente (`/opt/AdGuardHome/data/querylog.json`) no se actualizó con las consultas reales de esta prueba, solo con pruebas sintéticas anteriores — la resolución en sí funciona (confirmado por las tres formas de arriba), pero el archivo de log parece no estar flusheando a disco después de los reinicios del servicio de hoy. Revisar si persiste — puede afectar las estadísticas que se ven en la UI de AdGuard, no la resolución real.

Mientras se sigue de cerca la primera semana de uso real (rollout gradual — cada dispositivo lo toma recién al renovar su lease DHCP, no todos de golpe), cada dispositivo que necesite `*.oscar.home` puntualmente sigue teniendo dos formas de resolverlo sin depender de que el DNS de red esté sano:

## Wildcard `*.oscar.home` para apps de k3s (2026-09-15)

Los rewrites de AdGuard pasaron de una entrada por hostname a esto:

```yaml
rewrites:
  - domain: git.oscar.home
    answer: 192.168.0.156      # NPM (core01) — apps en Docker Compose
    enabled: true
  - domain: nexus.oscar.home
    answer: 192.168.0.156
    enabled: true
  - domain: portainer.oscar.home
    answer: 192.168.0.156
    enabled: true
  - domain: '*.oscar.home'
    answer: 192.168.0.150      # Traefik (k3s01) — todo lo que corre en k3s
    enabled: true
```

Motivo: cada app nueva desplegada vía Argo CD (`led`, `argocd`, `ci-demo`, y las que vengan) ya trae su propio `Ingress` en Traefik — el único paso manual que faltaba era agregar el rewrite en AdGuard cada vez. Con el wildcard, cualquier `Ingress` nuevo con host `<lo-que-sea>.oscar.home` resuelve solo, sin tocar AdGuard de nuevo. Los dominios explícitos (`git`, `nexus`, que van a `192.168.0.156`, no a k3s01) siguen ganando por especificidad — confirmado con `dig`, no es una suposición sobre cómo prioriza AdGuard.

Deliberadamente **no** se unificó bajo NPM (ej. `*.oscar.home` → NPM → Traefik): Traefik ya es un reverse proxy completo con routing por host nativo de k3s, meter NPM en el medio sería un proxy delante de otro resolviendo lo mismo, y ataría la disponibilidad de las apps de k3s a que `core01`/NPM esté arriba — hoy son capas independientes (Docker y k3s), a propósito.

## Cómo resuelven hoy los dispositivos

**Wildcard + DNS del dispositivo apuntado a `192.168.0.93`** (+ fallback `1.1.1.1`) es ahora la opción más práctica para cualquier app de k3s — con el wildcard de arriba, resuelve *cualquier* `*.oscar.home` sin mantener una lista a mano y sin tocar nada de nuevo cuando se agrega una app. Sigue dependiendo de que AdGuard esté arriba y manda todo el tráfico DNS del dispositivo por él.

**`/etc/hosts` por hostname puntual** sigue siendo válido para `git.oscar.home`/`nexus.oscar.home`/`portainer.oscar.home` (no cubiertos por el wildcard) o si no se quiere depender de AdGuard en absoluto — apuntan a `192.168.0.156` (NPM en `core01`), no a `devops01` directo, desde que se migraron detrás de NPM:

```text
192.168.0.156 git.oscar.home
192.168.0.156 nexus.oscar.home
192.168.0.156 portainer.oscar.home
```

**Descartado a propósito: Tailscale Split DNS.** Resolvería lo mismo para cualquier dispositivo del tailnet sin configurar DNS a mano en cada uno, incluido el acceso remoto desde el celular — pero el objetivo acá es explícitamente **DNS por nombre dentro de la LAN, no acceso desde afuera**, así que no aporta nada sobre el wildcard de arriba para este caso de uso y suma una dependencia (Tailscale) que no hace falta. Queda anotado por si en algún momento sí se busca resolver el acceso remoto (que sigue roto para `*.oscar.home` vía Tailscale, caso reportado con el celular).
