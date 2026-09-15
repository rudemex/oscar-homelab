---
title: Instalación de k3s
sidebar_position: 2
---

# Instalación de k3s

:::caution Corregido tras la experiencia real
`k3s01` se creó sobre la red plana real (`192.168.0.0/24`, IP fija `192.168.0.150`), no sobre el esquema de VLANs `192.168.20.0/24` que usan los ejemplos de esta página y de [crear VM core01](../proxmox/crear-vm-core01.md) — la segmentación por VLAN sigue siendo un plan futuro (ver [plan de direccionamiento](../red/plan-direccionamiento.md)), `core01` tampoco la usa todavía. Reemplazar los ejemplos de IP de esta página por `192.168.0.x` hasta que la migración a VLANs sea real.
:::

## VM recomendada para laboratorio inicial

- Ubuntu/Debian estable;
- 2–4 vCPU;
- 4–8 GB RAM según apps;
- 40–80 GB disco;
- IP/reservation estable;
- DNS funcional;
- qemu-guest-agent instalado.

## Bootstrap

Dentro de la VM (`k3s01`), el instalador oficial de k3s en un solo comando:

```bash
curl -sfL https://get.k3s.io | sh -
```

Descarga el binario, instala `k3s` como servicio systemd, y arranca un cluster de un solo nodo (server + agent en la misma máquina) usando Traefik como Ingress y ServiceLB como load balancer por defecto — ambos suficientes para un laboratorio. Para fijar una versión concreta en vez de "la última estable" (recomendable si vas a automatizar esto más adelante):

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.31.2+k3s1" sh -
```

(reemplazar por la versión estable vigente al momento de instalar — ver [releases de k3s](https://github.com/k3s-io/k3s/releases)).

Después de instalar:

```bash
sudo kubectl get nodes -o wide
sudo kubectl get pods -A
```

### Llevarte el kubeconfig a tu equipo de administración

k3s guarda el kubeconfig en `/etc/rancher/k3s/k3s.yaml`, apuntando a `127.0.0.1` por defecto — hay que copiarlo y cambiar esa IP por la real del nodo:

```bash
# en k3s01
sudo cat /etc/rancher/k3s/k3s.yaml
```

```bash
# en tu equipo de administración — IP real de k3s01 en la red plana actual (192.168.0.x, no la VLAN de ejemplo)
mkdir -p ~/.kube
scp oscar@192.168.0.150:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i '' 's/127.0.0.1/192.168.0.150/' ~/.kube/config   # macOS; en Linux: sed -i 's/127.0.0.1/.../'
chmod 600 ~/.kube/config
kubectl get nodes
```

En la práctica, en `k3s01` se usa `sudo kubectl` directo en la VM en vez de llevarse el kubeconfig afuera — más simple para un solo nodo administrado por SSH, a costa de depender de SSH para cada `kubectl`. Llevarse el kubeconfig vale la pena si se administra seguido desde el equipo local.

## Registry insecure (Nexus) — necesario si vas a pullear imágenes propias

Si algún Deployment va a usar una imagen pusheada al [Docker registry de Nexus](../servicios/nexus.md) (HTTP, sin TLS), k3s necesita su propio archivo de configuración de registries — **es un sistema separado del `daemon.json` de Docker**, no lo hereda ni lo comparte:

```yaml
# /etc/rancher/k3s/registries.yaml — crear/editar y reiniciar k3s (systemctl restart k3s) para aplicar
mirrors:
  "<ip-devops01>:8082":
    endpoint:
      - "http://<ip-devops01>:8082"
configs:
  "<ip-devops01>:8082":
    tls:
      insecure_skip_verify: true
```

Sin esto, un pod con imagen de Nexus falla con `ImagePullBackOff` aunque el `docker push` desde la CI haya funcionado bien — es una capa de configuración completamente distinta a la de Docker.

El kubeconfig de k3s por defecto tiene permisos de cluster-admin — tratarlo como un secreto (nunca en Git, ver [gestión de secretos](../seguridad/secretos.md)).

## Namespace de O.S.C.A.R.

Ejemplo:

```bash
kubectl create namespace oscar-lab
kubectl create namespace observability
kubectl create namespace argocd
```

No poner todo en `default`; los namespaces ayudan a observar ownership, cuotas y limpieza.

## Definition of Done

- nodo `Ready`;
- CoreDNS saludable;
- storage class disponible;
- Service/Ingress de prueba accesible;
- métricas/health visibles;
- kubeconfig fuera de Git;
- snapshot/backup de la VM o procedimiento de reconstrucción.
