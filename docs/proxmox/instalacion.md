---
title: Instalación de Proxmox
sidebar_position: 1
---

# Instalación de Proxmox VE

Esta guía asume que el Dell OptiPlex 7060 se dedicará a Proxmox. Antes de comenzar, respaldar cualquier dato existente en sus SSD.

Usar siempre la **versión estable actual de la rama Proxmox VE 8.x** (descargada desde proxmox.com al momento de instalar) — no fijar acá un número de versión exacto, que quedaría desactualizado; validar contra las release notes oficiales de la versión que efectivamente se descargue.

## Pre-flight

Ajustes de BIOS del Dell OptiPlex 7060 (F2 al bootear):

- [ ] backup verificado de información existente en los discos;
- [ ] BIOS/UEFI actualizado si corresponde;
- [ ] **VT-x** (Intel Virtualization Technology) habilitado — obligatorio para correr VMs;
- [ ] **VT-d** (Intel Virtualization Technology for Directed I/O) habilitado — no es indispensable para el arranque inicial, pero sin él no va a ser posible pasar un dispositivo PCIe/USB directo a una VM más adelante (por ejemplo una capturadora para CCTV); mejor dejarlo activado desde el día uno que reabrir el BIOS después;
- [ ] **Secure Boot deshabilitado** — Proxmox VE puede convivir con Secure Boot, pero módulos de kernel de terceros (drivers, ZFS en algunos casos) suelen fallar a firmar; para un homelab sin ese requisito de compliance, deshabilitarlo evita dolores de cabeza innecesarios;
- [ ] **power management / C-states**: dejar el perfil de energía en el default de fábrica (no forzar "máximo rendimiento" ni "máximo ahorro"); revisar sí que no haya un límite de energía de CPU agresivo pensado para uso de escritorio, que puede generar throttling bajo carga sostenida de varias VMs;
- [ ] boot USB disponible;
- [ ] cable Ethernet conectado;
- [ ] IP de administración reservada;
- [ ] hostname decidido (`pve01`);
- [ ] DNS y gateway conocidos.

## Instalación

1. Descargar la ISO estable desde Proxmox.
2. Crear USB booteable.
3. Arrancar el Dell desde USB.
4. Seleccionar el disco destinado al sistema.
5. Configurar país, zona horaria y teclado.
6. Definir contraseña administrativa temporal robusta y mail válido.
7. Configurar la interfaz de management con IP estable.
8. Finalizar instalación y reiniciar.
9. Acceder desde un cliente de la LAN a `https://<IP>:8006`.

:::warning
No exponer el puerto 8006 directamente a Internet.
:::

## Primeras acciones

```bash
apt update
apt full-upgrade
```

Antes de aplicar cambios de repositories, validar la documentación correspondiente a la versión instalada. No copiar comandos antiguos de foros sin entender qué repositorio habilitan.

## Naming

Usar nombres cortos y predecibles:

```text
pve01      host Proxmox
core01     VM servicios base
devops01   VM Git/registry/runners
k3s01      nodo k3s inicial
```

## Bridge de red (vmbr0)

El instalador crea `vmbr0` automáticamente sobre la NIC física elegida durante la instalación — es el bridge que las VMs usan por defecto para salir a la red. Verificar la configuración generada en `/etc/network/interfaces`:

```text
auto vmbr0
iface vmbr0 inet static
    address 192.168.20.10/24        # IP de management de pve01 — ejemplo, usar el plan real
    gateway 192.168.20.1
    bridge-ports enp1s0             # NIC física real del Dell — confirmar con `ip link`
    bridge-stp off
    bridge-fd 0
```

Tras editar `/etc/network/interfaces`, aplicar sin reiniciar el host:

```bash
ifreload -a
ip -br a show vmbr0
```

Cuando llegue OPNsense y VLANs (target state, no instalado hoy), `vmbr0` pasa a `bridge-vlan-aware yes` para poder entregar VLANs distintas a VMs distintas sobre el mismo enlace físico — ver [VLAN y segmentación](../red/vlans.md#proxmox).

## Definition of Done

- interfaz web accesible desde red administrativa;
- DNS directo y reverso razonables;
- hora sincronizada;
- updates aplicados;
- storage visible (`pvesm status` sin errores);
- `vmbr0` configurado y documentado (IP, gateway, NIC física);
- backup de configuración/host planificado;
- primera VM de prueba creada y eliminada correctamente.
