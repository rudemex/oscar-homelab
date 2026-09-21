---
title: DNS con AdGuard Home
sidebar_position: 4
---

# DNS con AdGuard Home

**Estado:** LXC 100 **caído desde 2026-09-21** (falla del disco `sda`); DNS activo en [`pinode01`](../hardware/pinode01.md) — sección más abajo. Histórico: corriendo como LXC (`vmid 100`, tag `adblock;community-script`) en `oscar-core`, instalado vía el script comunitario de [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/). Sano y disponible, pero **ya NO es el DNS de toda la LAN** — se activó por DHCP el 2026-09-18 y se revirtió ese mismo día tras una recurrencia del hang de NIC del Dell (ver [rollback](#rollback-el-dhcp-wide-se-revirtió-2026-09-18) más abajo). El router (TP-Link Archer) reparte `8.8.8.8`/`8.8.4.4` (Google) por defecto hoy; AdGuard sigue usable apuntándolo a mano por dispositivo.

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
- **Cambio real**: `Advanced → Network → DHCP Server` — DNS primario `192.168.0.93` (Dell), DNS secundario `1.1.1.1` (fallback real si AdGuard se cae). **Roles provisorios**, no el diseño final: cuando `network01` (Pi 3) exista, pasa a primario y el del Dell a secundario de verdad — ver `OSCAR_FINAL_INFRASTRUCTURE.md` sección 12/13. La Pi Zero W no tiene ningún rol de DNS (es `edge01`, sensores).
- Recursos del LXC subidos antes del cambio, con margen real: 2 vCPU / 1 GB (antes 1 vCPU / 512 MB).

**Validado con tráfico real, no solo pruebas sintéticas** (un dispositivo real — Mac del usuario — renovando DHCP y navegando normal):

- El DHCP reparte bien lo configurado — confirmado con `ipconfig getpacket en0` mostrando `domain_name_server: {192.168.0.93, 1.1.1.1}`.
- **Gotcha real encontrado en el camino**: el Mac de prueba tenía DNS fijado a mano (`8.8.8.8`) en **dos** servicios de red distintos (`Wi-Fi` y, más sorprendente, un adaptador `USB 10/100/1000 LAN 4` sin uso real pero con prioridad más alta en el orden de servicios de macOS) — un override manual en cualquiera de los dos gana por sobre el DNS que reparte el DHCP, sin ningún error visible. Hubo que limpiar los dos (`networksetup -setdnsservers <servicio> Empty`) para que el sistema realmente usara lo nuevo. Si un dispositivo "no toma" el DNS nuevo del router, esta es la primera causa a revisar — no asumir que el router está mal configurado.
- Con el override limpio: `doubleclick.net` resolvió `0.0.0.0` (bloqueado por el filtro de AdGuard) — confirmación real de que el tráfico pasa por ahí, no solo que el DNS "apunta bien" en teoría.
- Durante una sesión de navegación normal: **+397 paquetes UDP entrantes** al LXC (medido en `/proc/net/snmp`), CPU y RAM sin moverse de prácticamente cero (81 MB de 1 GB). La carga real de un dispositivo navegando es insignificante para los recursos asignados — nunca fue un problema de capacidad.
- **Pendiente, no bloqueante**: el querylog persistente (`/opt/AdGuardHome/data/querylog.json`) no se actualizó con las consultas reales de esta prueba, solo con pruebas sintéticas anteriores — la resolución en sí funciona (confirmado por las tres formas de arriba), pero el archivo de log parece no estar flusheando a disco después de los reinicios del servicio de hoy. Revisar si persiste — puede afectar las estadísticas que se ven en la UI de AdGuard, no la resolución real.

Mientras se sigue de cerca la primera semana de uso real (rollout gradual — cada dispositivo lo toma recién al renovar su lease DHCP, no todos de golpe), cada dispositivo que necesite `*.oscar.home` puntualmente sigue teniendo dos formas de resolverlo sin depender de que el DNS de red esté sano:

## Incidente menor: `systemd-resolved` de `core01` no volvía a usar AdGuard (2026-09-18)

Tras los varios `systemctl restart AdGuardHome` del diagnóstico del `ratelimit` (arriba), `resolvectl status eth0` en `core01` mostraba `Current DNS Server: 1.1.1.1` aunque la config seguía teniendo `192.168.0.93` primero en la lista (`DNS Servers: 192.168.0.93 1.1.1.1`). `systemd-resolved` había marcado a AdGuard como no disponible durante uno de esos reinicios y no volvió a probarlo solo — quedó pegado en el fallback indefinidamente.

**Síntoma real:** el contenedor de Homepage (que usa el DNS del host `core01` vía Docker embedded DNS, `127.0.0.11` → host) no podía resolver `portainer.oscar.home` (`Error: queryAaaa ENOTFOUND`), aunque AdGuard respondía perfecto si se lo consultaba directo (`dig +short portainer.oscar.home @192.168.0.93` → `192.168.0.156`). El problema nunca fue AdGuard ni la config — fue la selección en vivo de `systemd-resolved` en el host.

**Fix:** `sudo systemctl restart systemd-resolved` en `core01` — fuerza a reevaluar los servidores configurados desde cero. Volvió a `Current DNS Server: 192.168.0.93` de inmediato, `portainer.oscar.home` resolvió tanto en el host como dentro del contenedor de Homepage sin más cambios.

Si vuelve a pasar tras un reinicio de AdGuard: mismo fix, un `systemctl restart systemd-resolved` en el host afectado (no hace falta reiniciar Docker ni los contenedores).

## Rollback: el DHCP-wide se revirtió (2026-09-18)

La activación de más arriba duró el mismo día. A las 20:32 el [hang recurrente de la NIC física del Dell](../arquitectura/estado-actual.md#incidente-real-2026-09-18-hang-de-la-nic-física-caída-de-core01-y-adguard) volvió a pasar — con toda la LAN dependiendo de `192.168.0.93` como DNS primario, la intermitencia de la NIC se sintió como "internet no anda" en cualquier dispositivo de la casa (caso real: `drive.tresdoce.com.ar` inaccesible en pleno uso). AdGuard en sí nunca estuvo mal configurado ni caído por su cuenta — la NIC del host le tapaba el camino.

**Decisión:** mientras la NIC siga siendo poco confiable (es la segunda vez en la semana), no debería ser el DNS del que depende toda la casa. Rollback del que ya existía backup:

- Router restaurado por UI (`System Tools → Backup & Restore → Restore`, mismo archivo guardado antes de la activación) — vuelve a repartir lo de antes (`8.8.8.8`/`8.8.4.4`, Google).
- Dispositivos toman el DNS nuevo al renovar su lease DHCP (forzado a mano en el Mac de prueba con `sudo ipconfig set en0 DHCP` — sin eso, queda con el lease viejo apuntando a `192.168.0.93` hasta que expire solo).
- AdGuard sigue arriba, sano, y se puede seguir usando apuntándolo a mano en un dispositivo puntual — solo dejó de ser el default de toda la LAN.

**Condición para reactivar:** la NIC del Dell necesita una mitigación real (ver el incidente en `estado-actual.md`) antes de volver a intentar DHCP-wide — si vuelve a colgarse con la LAN entera dependiendo de ella, el radio de impacto es toda la casa, no solo OSCAR.

## AdGuard Home en `pinode01` (2026-09-21)

El AdGuard del Dell (LXC 100) **está caído desde el 2026-09-21 03:32**: su disco vive en el storage `Backups` (SSD SATA `sda`), que dejó de responder — ver [estado actual](../arquitectura/estado-actual.md). Como su config no se pudo leer, se instaló uno **nuevo** en [`pinode01`](../hardware/pinode01.md) con la configuración documentada arriba.

| Dato | Valor |
|---|---|
| Versión | AdGuard Home `v0.107.79` (binario oficial arm64, checksum SHA-256 verificado) en `/opt/AdGuardHome`, servicio systemd `AdGuardHome` |
| Escucha | DNS `192.168.0.213:53` (UDP/TCP, también por la IP de tailnet `100.102.205.119`); UI `http://192.168.0.213:3000` (solo LAN) |
| Acceso | usuario `admin`, contraseña en Vaultwarden ("AdGuard Home (pinode01) — admin") |
| `ratelimit` | `300`, `ratelimit_subnet_len_ipv4: 24` (el fix del incidente de arriba, ya desde el inicio) |
| Upstreams | `1.1.1.1` y `8.8.8.8` (balanceo de carga) |
| Filtros | *AdGuard DNS filter* (181 586 reglas, activo). Las listas del LXC viejo no se pudieron recuperar |
| Rewrites | `git`, `nexus`, `portainer`, `infisical` `.oscar.home` → `192.168.0.156` (los 4 proxy hosts reales de NPM); `*.oscar.home` → `192.168.0.150` (Traefik) |
| Querylog | retención de 24 h (cuida la microSD) |
| Consumo | ~68 MB de RAM |

**Validado:** los rewrites y el wildcard resuelven bien, `doubleclick.net` se bloquea (`0.0.0.0`), Internet resuelve, y **60/60 consultas simultáneas** contestan (la regresión que tenía el `ratelimit: 20`).

**No se cambió el DHCP del router**: sigue repartiendo `8.8.8.8`/`8.8.4.4`. La condición para activar DNS de red completa (mitigar el cuelgue de la NIC del Dell) sigue en pie; ver el [rollback](#rollback-el-dhcp-wide-se-revirtió-2026-09-18). Para un dispositivo puntual, alcanza con apuntarle el DNS a `192.168.0.213`.

**Efecto colateral detectado:** `core01` y `lab01` tienen `192.168.0.93` como DNS principal (y `1.1.1.1` de respaldo). Con el LXC caído resuelven por `1.1.1.1`, que no conoce `*.oscar.home`: el contenedor de Homepage no resuelve `portainer.oscar.home` ni `git.oscar.home`. Solución pendiente: apuntarlos a `192.168.0.213`.

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
