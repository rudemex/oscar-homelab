---
title: Naming
sidebar_position: 1
---

# Naming convention

## Hosts

```text
oscar-core
core01
devops01
k3s01
pi-dns01
pi-probe01
dvr01
sw01
fw01
```

Minúscula, sin guion bajo, `<rol><número de dos dígitos>`. Este es el nombre DNS/Proxmox/lógico — el que se usa en toda la documentación técnica, inventario y comandos.

`oscar-core` es la excepción real a este patrón: es el hostname que quedó puesto al instalar Proxmox, antes de que existiera esta convención por escrito. No se renombra retroactivamente (requiere reinstalar o regenerar certificados) — el resto de los hosts nuevos sí sigue el patrón `<rol><número>` desde acá en adelante.

## Etiquetas físicas de cableado

Las etiquetas impresas en patch panel y cables (ver [cableado y patch panel](../red/cableado-patch-panel.md)) usan **mayúscula**, ej. `OSCAR-CORE`, `SW01-01`, `PWR-OSCAR-CORE`. Es una convención deliberadamente distinta a la de hostnames: una etiqueta física se lee rápido sobre una impresora de cinta y en poca luz, mientras que el hostname es lo que se escribe en terminal. No mezclar los dos formatos dentro de un mismo contexto (no escribir `OSCAR-CORE` en un comando `ssh`, no imprimir `oscar-core` en una etiqueta si el resto del rack usa mayúscula). No agregar prefijos de fabricante (`Dell-`, etc.): el rol+número ya identifica el equipo sin ambigüedad.

## Servicios

DNS interno:

```text
grafana.oscar.home
n8n.oscar.home
nexus.oscar.home
argocd.oscar.home
```

El dominio interno final es una decisión de arquitectura; `oscar.home` se usa en la guía como ejemplo legible.
