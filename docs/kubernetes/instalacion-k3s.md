---
title: Instalación de k3s
sidebar_position: 2
---

# Instalación de k3s

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
# en tu equipo de administración
mkdir -p ~/.kube
scp oscar@192.168.20.12:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i '' 's/127.0.0.1/192.168.20.12/' ~/.kube/config   # macOS; en Linux: sed -i 's/127.0.0.1/.../'
chmod 600 ~/.kube/config
kubectl get nodes
```

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
