---
title: Herramientas básicas
sidebar_position: 1
---

# Herramientas básicas

El resto de esta guía asume que sabés abrir una terminal, conectarte por SSH y ejecutar comandos sin que te resulten intimidantes. Si ya tenés experiencia con Linux, esta página no te aporta nada nuevo — seguí directo a [inventario](../hardware/inventario.md). Si es tu primera vez, leela antes de tocar el Dell: te ahorra quedar trabado en el primer comando de la guía.

## La terminal

Es un programa donde escribís comandos de texto en vez de hacer clic. Todo lo que digamos "ejecutar" o "correr" en esta guía significa: abrir una terminal, escribir el comando (o pegarlo), presionar Enter.

Cómo abrir una en tu computadora (no en el homelab — esta es la que usás para *llegar* al homelab):

- **macOS**: `Cmd + Espacio`, escribir "Terminal", Enter.
- **Windows**: abrir "Windows Terminal" o "PowerShell" desde el menú inicio. Si vas a seguir esta guía seguido, instalar [WSL](https://learn.microsoft.com/windows/wsl/install) (`wsl --install` en PowerShell como administrador) te da una terminal Linux real dentro de Windows — vale la pena para evitar diferencias de sintaxis.
- **Linux**: `Ctrl + Alt + T` en la mayoría de las distros, o buscar "Terminal" en el menú de aplicaciones.

## Cómo leer los bloques de comandos de esta guía

```bash
qm clone 9000 101 --name core01 --full   # clonar el template 9000 como VM 101
```

- Lo que está después de `#` es un comentario, no se ejecuta.
- Cualquier cosa entre `<` y `>` (por ejemplo `<vmid>`) hay que reemplazarla por tu valor real, incluyendo los signos `<` `>`.
- Cuando un bloque tiene varias líneas, se ejecutan una por una, en orden, salvo que se indique lo contrario.

:::caution No pegues comandos sin entenderlos
Esta guía nunca te va a pedir que ejecutes algo a ciegas, pero es un hábito que conviene tener siempre: antes de pegar un comando de *cualquier* fuente (esta guía incluida) en una terminal con privilegios, leelo. `curl algo | sudo bash` sin mirar qué descarga es la forma más común de romper un servidor.
:::

## `sudo`

Muchos comandos necesitan permisos de administrador. `sudo` (super user do) ejecuta un solo comando con esos permisos, pidiéndote tu contraseña la primera vez:

```bash
sudo apt update
```

Si un comando falla con `Permission denied`, probablemente le falta `sudo` adelante — no es necesario ni recomendable anteponer `sudo` a todo por las dudas.

## Paquetes con `apt`

Las VMs de esta guía usan Ubuntu/Debian, que instalan software con `apt`:

```bash
sudo apt update              # actualiza la lista de paquetes disponibles (no instala nada)
sudo apt upgrade -y          # actualiza los paquetes ya instalados
sudo apt install -y git nano # instala paquetes nuevos (git y nano, en este ejemplo)
```

`apt update` no actualiza el sistema — solo refresca qué versiones existen. Sin ese paso, `install`/`upgrade` pueden instalar versiones viejas.

## Editar archivos: `nano`

Vas a necesitar editar archivos de texto por terminal (configuraciones, `.env`, YAML). El editor más simple para empezar es `nano`:

```bash
nano archivo.txt
```

Dentro de `nano`, los atajos están anotados abajo con `^` (significa `Ctrl`):

- `Ctrl + O` luego `Enter`: guardar.
- `Ctrl + X`: salir (te avisa si hay cambios sin guardar).
- `Ctrl + K`: cortar una línea.

Esta guía usa `nano` en sus ejemplos por ser el más simple. Si en algún momento ves `vim` mencionado en otro lado de internet y no sabés cómo salir: `Esc` y después escribir `:q!` y Enter (sale sin guardar).

## SSH: conectarte a otra máquina

SSH es cómo te conectás por terminal a Proxmox, a las VMs, y a las Raspberry Pi — sin necesidad de teclado/monitor propios en cada equipo.

### Generar tu clave (una sola vez, en tu computadora)

```bash
ssh-keygen -t ed25519 -C "tu-nombre@oscar"
```

Presionar Enter en las tres preguntas (ubicación default, sin passphrase) es válido para un homelab personal. Esto crea dos archivos en `~/.ssh/`: `id_ed25519` (privada, **nunca la compartas ni la subas a Git**) e `id_ed25519.pub` (pública, esta sí se comparte).

### Copiar tu clave pública a un servidor

```bash
ssh-copy-id usuario@192.168.20.11
```

Te pide la contraseña del usuario una única vez; después de esto, `ssh` no vuelve a pedirla — usa la clave.

### Conectarte

```bash
ssh usuario@192.168.20.11
```

Si es la primera vez que te conectás a esa IP, SSH te pregunta si confiás en la huella digital del servidor (`fingerprint`) — respondé `yes`. Ese mensaje solo debería aparecer una vez por servidor; si vuelve a aparecer para una IP que ya conocías, alguien cambió la máquina del otro lado (reinstalación, o algo más serio) — no lo aceptes automáticamente sin pensar por qué cambió.

## Navegación básica de archivos

```bash
pwd                 # dónde estoy parado
ls                   # qué hay acá
ls -la               # qué hay acá, con detalle y archivos ocultos
cd carpeta           # entrar a "carpeta"
cd ..                # subir un nivel
mkdir nombre         # crear una carpeta
```

## Cómo saber si un comando funcionó

La mayoría de los comandos no dicen "¡listo!" — si no hay error, funcionó. Para confirmarlo explícitamente:

```bash
echo $?
```

Muestra `0` si el comando anterior terminó bien, cualquier otro número si falló. Es útil cuando un comando no deja claro por su output si tuvo éxito.

## Con esto alcanza para arrancar

No hace falta memorizar más que esto antes de seguir. El resto de comandos específicos (Proxmox, Docker, Kubernetes) se explican en el lugar donde se usan, con el comando completo — no vas a encontrar en esta guía un paso que diga "instalá X siguiendo la documentación oficial" sin mostrar el comando real.
