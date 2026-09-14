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

## Cómo resuelven hoy las máquinas de administración

**Preferido: `/etc/hosts` por hostname puntual** (`sudo` para editar, en macOS/Linux):

```text
192.168.0.151 git.oscar.home
192.168.0.151 nexus.oscar.home
```

Es lo que ya se usaba en la práctica para `argocd.oscar.home` y `led.oscar.home` (apuntando a `192.168.0.150`, `k3s01`) antes incluso de que existiera esta nota — se documenta acá recién ahora. Ventaja sobre cambiar el DNS del sistema: no depende de que AdGuard esté arriba en absoluto para esos hostnames puntuales, y no manda el resto del tráfico DNS de la máquina por AdGuard de paso.

**Alternativa: DNS del sistema apuntado a `192.168.0.93`** (+ un fallback como `1.1.1.1`) — resuelve *cualquier* hostname de `*.oscar.home` sin mantener una lista a mano, pero depende de que AdGuard esté arriba y manda todo el tráfico DNS del dispositivo por él. Usar cuando hace falta resolver muchos hostnames nuevos seguido (ej. mientras se prueban servicios), no como default permanente.
