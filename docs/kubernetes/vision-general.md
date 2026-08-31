---
title: Visión de k3s
sidebar_position: 1
---

# Kubernetes con k3s

Kubernetes entra en O.S.C.A.R. como **plataforma de aprendizaje y despliegue declarativo**, no como requisito para correr cada aplicación doméstica.

## Por qué k3s

k3s reduce componentes y consumo respecto de una distribución Kubernetes completa, manteniendo APIs y conceptos que permiten practicar:

- Deployments y StatefulSets;
- Services e Ingress;
- ConfigMaps y Secrets;
- namespaces;
- storage classes/PVC;
- Helm;
- GitOps;
- observabilidad del cluster.

## Topología por etapas

### Etapa 1: un nodo

```text
k3s01 (VM)
├── control plane
└── worker
```

Sirve para aprender y desplegar aplicaciones no críticas.

### Etapa 2: tres nodos

Cuando exista RAM/hardware suficiente:

```text
k3s01
k3s02
k3s03
```

El objetivo de tres nodos es aprender alta disponibilidad, scheduling y mantenimiento; no se crea antes de tener capacidad real.

## Qué sí desplegar

- APIs de prueba;
- frontend + backend;
- herramientas internas;
- exporters;
- Argo CD;
- pequeños servicios stateless;
- proyectos demo.

## Qué mantener fuera inicialmente

- DNS del que depende el propio cluster;
- firewall;
- servicios imprescindibles para recuperar k3s;
- bases con datos importantes hasta dominar storage y backup.
