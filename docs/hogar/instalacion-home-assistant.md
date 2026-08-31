---
title: Instalar Home Assistant
sidebar_position: 4
---

# Home Assistant paso a paso

La forma final depende de dónde se aloje:

- **Home Assistant OS en VM**: experiencia completa y aislada;
- **Raspberry Pi 5**: futuro equipo dedicado;
- contenedor: válido, pero algunas capacidades/add-ons difieren.

Para O.S.C.A.R. preferimos HA OS en VM o Pi dedicada cuando se busque un servicio doméstico estable.

## Instalar Home Assistant OS como VM en Proxmox

Comandos reales, corridos **en Proxmox** — usan la imagen oficial `haos_ova` que Home Assistant publica específicamente para hypervisors tipo Proxmox/VMware (UEFI, sin necesidad de instalador interactivo). Reemplazar `<version>` por la [versión estable vigente](https://github.com/home-assistant/operating-system/releases) y `<vmid>` por un VMID libre.

```bash
# 1. Descargar y descomprimir la imagen oficial
wget https://github.com/home-assistant/operating-system/releases/download/<version>/haos_ova-<version>.qcow2.xz
unxz haos_ova-<version>.qcow2.xz

# 2. Crear la VM (UEFI/OVMF, requerido por HAOS)
qm create <vmid> --name home-assistant --memory 4096 --cores 2 \
  --net0 virtio,bridge=vmbr0 --ostype l26 --machine q35 --bios ovmf

# 3. Disco EFI (obligatorio con --bios ovmf)
qm set <vmid> --efidisk0 local-lvm:0,pre-enrolled-keys=0

# 4. Importar el disco de la imagen descargada
qm importdisk <vmid> haos_ova-<version>.qcow2 local-lvm
qm set <vmid> --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-<vmid>-disk-1
qm set <vmid> --boot order=scsi0

# 5. Iniciar
qm start <vmid>
```

Ajustar `--net0` a la VLAN IoT/servers según el diseño de red final (ver [VLAN y segmentación](../red/vlans.md)) una vez que exista segmentación real.

## Primer acceso

Esperar 1-2 minutos a que arranque, y entrar desde el navegador a `http://homeassistant.local:8123` (o a la IP asignada por DHCP, visible en `qm agent <vmid> ping` o en la UI de Proxmox si el guest agent de HAOS responde). El asistente de onboarding pide crear el primer usuario ahí mismo — no hay usuario/contraseña por defecto que cambiar.

## Integración del rack

Primeras entidades útiles:

- sensor de temperatura;
- estado UPS;
- disponibilidad de hosts;
- MQTT;
- consumo eléctrico si existe medidor.

## Primera automatización segura

Solo notificación por temperatura. No apagar hardware automáticamente hasta validar meses de lecturas y umbrales.

## Backup

Procedimiento concreto (snapshot nativo, qué incluye, cómo restaurar) en [Home Assistant — Backup y restore](../servicios/home-assistant.md#backup-y-restore). Probarlo al menos una vez antes de incorporar automatizaciones domésticas importantes.
