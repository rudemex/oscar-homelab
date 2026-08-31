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

Seguir el instalador y versión estable documentada por k3s al momento de implementación. No usar una versión flotante en automatizaciones sin revisar release notes.

Después de instalar:

```bash
sudo kubectl get nodes -o wide
sudo kubectl get pods -A
```

Copiar kubeconfig de forma segura al equipo de administración y cambiar el endpoint si fuese necesario.

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
