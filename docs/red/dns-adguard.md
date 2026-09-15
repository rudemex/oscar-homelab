---
title: DNS con AdGuard Home
sidebar_position: 4
---

# DNS con AdGuard Home

**Estado:** Actual — corriendo como LXC (`vmid 100`, tag `adblock;community-script`) en `oscar-core`, instalado vía el script comunitario de [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/). El servicio DNS en sí responde bien (confirmado con `dig @192.168.0.93`), pero **no es el DNS de toda la LAN**: `dhcp.enabled: false` en su config, y no hay ninguna configuración en el router apuntando su DHCP a AdGuard — se evitó a propósito porque hacerlo coincidió con una caída real de throughput (600→20 Mbps), causa **todavía sin diagnosticar**. Hasta resolver eso, cada dispositivo que necesite resolver `*.oscar.home` tiene que apuntar su DNS a mano a `192.168.0.93` — no es automático.

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

## Incidente sin resolver: caída de throughput al usarlo como DNS de red

Configurar el router para repartir AdGuard por DHCP a toda la LAN coincidió con una caída real de velocidad, 600→20 Mbps — se revirtió esa configuración (el router volvió a repartir su DNS de siempre) y se dejó anotado sin investigar a fondo. AdGuard como servicio sigue sano (`dig @192.168.0.93` resuelve bien, puerto 53 abierto) — el problema aparece específicamente al ponerlo como resolver de **toda la red simultáneamente**, no al consultarlo desde un dispositivo puntual.

Hipótesis sin confirmar, en orden de sospecha:
- el LXC 100 quedó con recursos (CPU/RAM) insuficientes para el volumen real de consultas de todos los dispositivos a la vez;
- algo en el vSwitch/bridge de Proxmox se satura al concentrar tráfico DNS de toda la LAN por un solo LXC;
- coincidencia con otra cosa (cambio de canal Wi-Fi, evento del ISP) no relacionada a AdGuard en sí.

Mientras no se diagnostique, cada dispositivo que necesite `*.oscar.home` tiene dos formas de resolverlo sin tocar el DNS de toda la red — carga mínima comparada con ser el DNS de la LAN completa, no debería reproducir el problema:

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
  - domain: '*.oscar.home'
    answer: 192.168.0.150      # Traefik (k3s01) — todo lo que corre en k3s
    enabled: true
```

Motivo: cada app nueva desplegada vía Argo CD (`led`, `argocd`, `ci-demo`, y las que vengan) ya trae su propio `Ingress` en Traefik — el único paso manual que faltaba era agregar el rewrite en AdGuard cada vez. Con el wildcard, cualquier `Ingress` nuevo con host `<lo-que-sea>.oscar.home` resuelve solo, sin tocar AdGuard de nuevo. Los dominios explícitos (`git`, `nexus`, que van a `192.168.0.156`, no a k3s01) siguen ganando por especificidad — confirmado con `dig`, no es una suposición sobre cómo prioriza AdGuard.

Deliberadamente **no** se unificó bajo NPM (ej. `*.oscar.home` → NPM → Traefik): Traefik ya es un reverse proxy completo con routing por host nativo de k3s, meter NPM en el medio sería un proxy delante de otro resolviendo lo mismo, y ataría la disponibilidad de las apps de k3s a que `core01`/NPM esté arriba — hoy son capas independientes (Docker y k3s), a propósito.

## Cómo resuelven hoy los dispositivos

**Wildcard + DNS del dispositivo apuntado a `192.168.0.93`** (+ fallback `1.1.1.1`) es ahora la opción más práctica para cualquier app de k3s — con el wildcard de arriba, resuelve *cualquier* `*.oscar.home` sin mantener una lista a mano y sin tocar nada de nuevo cuando se agrega una app. Sigue dependiendo de que AdGuard esté arriba y manda todo el tráfico DNS del dispositivo por él.

**`/etc/hosts` por hostname puntual** sigue siendo válido para `git.oscar.home`/`nexus.oscar.home` (no cubiertos por el wildcard) o si no se quiere depender de AdGuard en absoluto:

```text
192.168.0.151 git.oscar.home
192.168.0.151 nexus.oscar.home
```

**Descartado a propósito: Tailscale Split DNS.** Resolvería lo mismo para cualquier dispositivo del tailnet sin configurar DNS a mano en cada uno, incluido el acceso remoto desde el celular — pero el objetivo acá es explícitamente **DNS por nombre dentro de la LAN, no acceso desde afuera**, así que no aporta nada sobre el wildcard de arriba para este caso de uso y suma una dependencia (Tailscale) que no hace falta. Queda anotado por si en algún momento sí se busca resolver el acceso remoto (que sigue roto para `*.oscar.home` vía Tailscale, caso reportado con el celular).
