---
title: DNS con AdGuard Home
sidebar_position: 4
---

# DNS con AdGuard Home

**Estado:** Actual — corriendo como LXC (`vmid 100`, tag `adblock;community-script`) en `oscar-core`, instalado vía el script comunitario de [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/).

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
