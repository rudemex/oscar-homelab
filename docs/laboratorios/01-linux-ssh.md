---
title: Lab 01 · Linux y SSH
sidebar_position: 2
---

# Lab 01 · Linux y SSH

**Tipo:** descartable. La VM se destruye al final del lab; lo que queda es la práctica del flujo, no la VM en sí. Ese mismo flujo (clonar template → acceder por clave → hardening → destruir) es exactamente lo que la Fase 2 del [roadmap](../roadmap/roadmap-general.md) exige como gate ("una VM puede crearse, respaldarse, destruirse y restaurarse"), así que este lab no es un ejercicio aislado: es la habilidad base de todo lo que sigue.

## Objetivo

Crear una VM Linux desde el template Cloud-Init, acceder por clave SSH sin password, aplicar el hardening SSH básico documentado para O.S.C.A.R., crear un usuario administrativo dedicado y destruir la VM limpiamente.

## Prerequisitos

- Proxmox VE instalado y accesible ([instalación de Proxmox](../proxmox/instalacion.md)) — es el único requisito duro.
- Idealmente, el template Cloud-Init ya creado ([templates y Cloud-Init](../proxmox/templates-cloud-init.md)). Si todavía no existe, el lab puede arrancar desde una instalación manual mínima de Ubuntu/Debian Server por ISO; en ese caso, saltar el paso 1 y crear el usuario administrativo durante la instalación en vez de vía `--ciuser`.
- Un par de claves SSH propio (o generarlo en el paso 2).
- Acceso de red a la VLAN/segmento de administración donde vive `pve01`.

Recursos mínimos para la VM del lab (deliberadamente más chica que `core01`, que usa 2 vCPU/4 GB — ver [crear-vm-core01.md](../proxmox/crear-vm-core01.md)):

```text
vCPU: 1
RAM: 1 GB
Disco: 8-10 GB
NIC: VirtIO
```

## Arquitectura

```text
[equipo cliente] --clave SSH ed25519--> [VM lab-linux01 en pve01, red de administración]
```

No hay más partes móviles que esas dos; no amerita un diagrama Mermaid.

## Pasos

### 1. Clonar el template y arrancar la VM

```bash
qm clone 9000 199 --name lab-linux01 --full
qm set 199 --ipconfig0 ip=192.168.20.199/24,gw=192.168.20.1   # ejemplo — usar el plan de direccionamiento real
qm start 199
```

Si no existe template todavía, instalar Ubuntu/Debian Server mínimo por ISO en el VMID `199` y crear un usuario `oscar` con sudo durante el instalador.

### 2. Generar (o reutilizar) el par de claves SSH en el cliente

```bash
ssh-keygen -t ed25519 -C "lab01-oscar" -f ~/.ssh/oscar_lab01_ed25519
```

### 3. Inyectar la clave pública y confirmar acceso

Si el template ya inyectó una clave vía `--sshkey` (ver templates-cloud-init.md), usar esa. Si se instaló a mano:

```bash
ssh-copy-id -i ~/.ssh/oscar_lab01_ed25519.pub oscar@192.168.20.199
ssh -i ~/.ssh/oscar_lab01_ed25519 oscar@192.168.20.199
```

### 4. Baseline y usuario administrativo dedicado

```bash
sudo apt update
sudo apt full-upgrade -y
sudo adduser --disabled-password labadmin
sudo usermod -aG sudo labadmin
sudo rsync --archive --chown=labadmin:labadmin ~/.ssh /home/labadmin
```

### 5. Hardening SSH

Seguir [hardening-linux.md](../seguridad/hardening-linux.md): crear el drop-in `/etc/ssh/sshd_config.d/oscar-hardening.conf` con `PermitRootLogin no`, `PasswordAuthentication no` y `AllowUsers labadmin`, validar sintaxis con `sshd -t` **antes** de recargar, y confirmar el acceso por clave desde una terminal aparte antes de cerrar la sesión actual — es el paso donde más gente se bloquea a sí misma (ver Troubleshooting).

```bash
sudo sshd -t
sudo systemctl reload ssh
```

En otra terminal, sin cerrar la primera:

```bash
ssh -i ~/.ssh/oscar_lab01_ed25519 labadmin@192.168.20.199
```

## Validación

```bash
# acceso por clave funciona
ssh -i ~/.ssh/oscar_lab01_ed25519 labadmin@192.168.20.199 "whoami; sudo -l"

# password auth quedó deshabilitado: esto debe ser rechazado
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password labadmin@192.168.20.199
```

El primer comando debe devolver `labadmin` y una lista de privilegios sudo sin pedir contraseña de sesión SSH; el segundo debe terminar en `Permission denied`, confirmando que no queda ningún camino de password SSH permanente.

## Qué aprendimos

Esta es la mecánica exacta detrás de cada VM real de O.S.C.A.R. (`core01`, `devops01`, `k3s01`): template → clon → clave → hardening. Practicarla en una VM descartable, sin miedo a romper nada, es lo que permite tratar después a las VMs reales como reproducibles en vez de como mascotas que nadie quiere tocar. También es la base concreta de la que depende [hardening-linux.md](../seguridad/hardening-linux.md) para el resto del homelab: si el drop-in de SSH se rompe acá, mejor descubrirlo en una VM que se destruye en cinco minutos que en `core01` un sábado a la noche.

## Cleanup

```bash
qm stop 199
qm destroy 199
qm list | grep 199   # no debe devolver nada
```

En el cliente:

```bash
ssh-keygen -R 192.168.20.199
rm ~/.ssh/oscar_lab01_ed25519 ~/.ssh/oscar_lab01_ed25519.pub   # solo si no se va a reutilizar en otro lab
```

## Troubleshooting

- **`ssh-copy-id` falla con "Permission denied (publickey)"** → el template ya deshabilitó `PasswordAuthentication` antes de poder inyectar la clave manualmente → usar la clave que el template ya inyectó vía Cloud-Init (`--sshkey`), o entrar por la consola noVNC de Proxmox para pegar la clave a mano en `~/.ssh/authorized_keys`.
- **La sesión SSH se corta al aplicar el hardening y no se puede reconectar** → error de sintaxis en el drop-in, o `AllowUsers` no incluye al usuario real que se está usando → entrar por la consola noVNC de Proxmox (no depende de la red) para corregir `/etc/ssh/sshd_config.d/oscar-hardening.conf`; de ahí la regla de validar con `sshd -t` y probar desde otra terminal antes de cerrar la sesión actual, como en el paso 5.
- **`qm clone` falla con "unable to create image: already exists"** → el VMID `199` quedó ocupado por una corrida anterior del lab que no se limpió → `qm list` para encontrar el VMID en conflicto y hacer `qm destroy` sobre el residuo antes de continuar.
