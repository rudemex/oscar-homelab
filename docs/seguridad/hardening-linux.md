---
title: Hardening Linux
sidebar_position: 3
---

# Hardening de VMs Linux

Baseline:

- updates regulares;
- SSH con claves;
- deshabilitar login root remoto cuando sea viable;
- firewall del host si aporta defensa en profundidad;
- usuarios individuales;
- `sudo`;
- NTP correcto;
- qemu guest agent;
- logs persistentes;
- fail2ban solo cuando aplica y entendemos el servicio;
- paquetes mínimos.

## SSH

No abrir 22 a Internet. Usar red MGMT/VPN. Validar acceso por clave antes de deshabilitar password para no bloquear administración.

Cambios recomendados en `/etc/ssh/sshd_config.d/oscar-hardening.conf` (no editar `sshd_config` directamente, usar un drop-in):

```text
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
X11Forwarding no
MaxAuthTries 3
AllowUsers oscar
```

Aplicar y validar antes de cerrar la sesión actual:

```bash
sudo sshd -t                       # valida sintaxis antes de recargar
sudo systemctl reload ssh
ssh -o PreferredAuthentications=publickey oscar@<host>   # confirmar acceso por clave en OTRA terminal
```

## Firewall del host (nftables)

Como defensa en profundidad además del firewall perimetral (no en reemplazo). Ejemplo mínimo para una VM que solo sirve SSH desde MGMT y un puerto de aplicación:

```bash
sudo apt install -y nftables
```

```text
# /etc/nftables.conf
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    iif "lo" accept
    ct state established,related accept
    ip saddr 192.168.10.0/24 tcp dport 22 accept   # SSH solo desde VLAN MGMT
    tcp dport { 80, 443 } accept                    # ajustar según el servicio
    ip protocol icmp accept
  }
}
```

```bash
sudo systemctl enable --now nftables
sudo nft -f /etc/nftables.conf
sudo nft list ruleset   # verificar antes de cerrar la sesión
```

## fail2ban (cuando aplica)

Solo si el servicio expuesto genera intentos de login reales (ej. SSH accesible desde más de la VLAN MGMT, o un panel con auth propia). Ejemplo para sshd:

```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
maxretry = 5
bantime = 1h
findtime = 10m
```

```bash
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

## Actualizaciones automáticas de seguridad (Debian/Ubuntu)

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Verificar que `/etc/apt/apt.conf.d/50unattended-upgrades` incluya al menos el origen `${distro_id}:${distro_codename}-security`. No confundir esto con `apt full-upgrade` manual (ver [operación de Proxmox](../proxmox/operacion.md) para el host) — esto es para el sistema operativo *dentro* de cada VM.
