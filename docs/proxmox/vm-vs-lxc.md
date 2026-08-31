---
title: VM vs LXC
sidebar_position: 3
---

# ¿VM o LXC?

## VM

Elegir VM cuando:

- se necesita aislamiento fuerte;
- Docker será una plataforma central;
- el servicio modifica kernel/networking de forma compleja;
- se quiere portar fácilmente la carga;
- se quiere aprender administración tradicional de Linux.

## LXC

Elegir LXC cuando:

- el servicio es pequeño;
- queremos bajo consumo de RAM;
- no necesita kernel propio;
- el modelo de seguridad es suficiente para el caso.

## Regla de O.S.C.A.R.

Docker de aplicaciones corre, por defecto, **dentro de una VM**, no dentro del host Proxmox. LXC se reserva para utilidades concretas donde su simplicidad compense.

## Ejemplos

| Carga | Recomendación |
|---|---|
| Docker host | VM |
| k3s node | VM |
| DNS auxiliar | LXC o Pi |
| pequeña jumpbox | LXC |
| Home Assistant OS | VM |
| laboratorio Linux | VM/LXC según objetivo |
