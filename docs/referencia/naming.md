---
title: Naming
sidebar_position: 1
---

# Naming convention

**Actualizado 2026-09-22:** convención revisada como parte de la reorganización del rack. Ver `REORGANIZACION_RACK.md`
(raíz del repo, fuera de `docs/`) para el detalle completo y el estado de la migración — mientras dura, convive
documentación con los nombres viejos (`pinode01`, `core01`, etc.) y nueva.

## Hosts

Se elimina el sufijo `01` cuando existe una única instancia real de ese rol. La numeración se reserva para cuando
existe más de una instancia real (no "por si acaso").

```text
core
network
monitor
devops
automation
k3s
services
apps
games
lab
```

Ejemplo de cuándo sí numerar (todavía no aplica, es ilustrativo):

```text
k3s-control
k3s-worker01
k3s-worker02

n8n-worker01
n8n-worker02
```

Minúscula, sin guion bajo. Este es el nombre DNS/Proxmox/lógico — el que se usa en toda la documentación técnica,
inventario y comandos.

`oscar-core` (el hostname del propio Proxmox) es la excepción real a este patrón: quedó puesto al instalar Proxmox,
antes de que existiera esta convención por escrito, y no se renombra retroactivamente (requiere reinstalar o
regenerar certificados).

## Etiquetas físicas de cableado

Las etiquetas impresas en patch panel y cables (ver [cableado y patch panel](../red/cableado-patch-panel.md)) usan
**mayúscula**, ej. `OSCAR-CORE`, `SW01-01`, `PWR-OSCAR-CORE`. Es una convención deliberadamente distinta a la de
hostnames: una etiqueta física se lee rápido sobre una impresora de cinta y en poca luz, mientras que el hostname es
lo que se escribe en terminal. No mezclar los dos formatos dentro de un mismo contexto. No agregar prefijos de
fabricante (`Dell-`, etc.): el rol ya identifica el equipo sin ambigüedad.

## Servicios

DNS interno:

```text
grafana.oscar.home
n8n.oscar.home
nexus.oscar.home
argocd.oscar.home
```

El dominio interno final es una decisión de arquitectura; `oscar.home` se usa en la guía como ejemplo legible.

## Áreas conceptuales

Cada host pertenece a una de estas cuatro áreas (ver `REORGANIZACION_RACK.md` para el detalle de qué va en cada
una y por qué):

```text
INFRASTRUCTURE  → core, network, monitor
PLATFORM        → devops, automation, k3s
WORKLOADS       → services, apps
SPECIAL PURPOSE → games, lab
```

Regla de decisión rápida para un componente nuevo: ¿es infraestructura transversal? → `core`. ¿Red/DNS/acceso
remoto? → `network`. ¿Mide o alerta? → `monitor`. ¿Toolchain de CI/CD? → `devops`. ¿Workflows/automatización? →
`automation`. ¿Plataforma Kubernetes en sí? → `k3s`. ¿App de terceros que instalamos? → `services`. ¿Software que
desarrollamos nosotros? → `apps`. ¿Servidor de juego? → `games`. ¿Todavía no se sabe si se adopta? → `lab`.
