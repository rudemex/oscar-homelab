---
title: Instalar Argo CD
sidebar_position: 7
---

# Argo CD paso a paso

## 1. Precondiciones

```bash
kubectl get nodes
kubectl get pods -A
```

Todo debe estar estable antes de sumar GitOps.

## 2. Namespace

```bash
kubectl create namespace argocd
```

## 3. Instalar

Usar el manifest o chart oficial correspondiente a una versión estable fijada. Guardar en la documentación qué versión se instaló.

## 4. Acceso inicial

Para bootstrap se puede usar port-forward sin publicar el UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Cambiar credenciales iniciales y luego definir el método de autenticación/acceso definitivo.

## 5. Repo demo

Crear una aplicación apuntando al path del ejemplo `whoami` del repo GitOps.

## 6. Sync manual

Primeras pruebas con sync manual. Observar:

- desired state;
- live state;
- diff;
- health;
- history.

## 7. Auto-sync

Habilitar después de entender:

- self-heal;
- prune;
- qué sucede si se borra un manifest del repo.

## 8. Recuperación

Argo debe poder reinstalarse desde documentación/Git. No convertir su propia configuración en un estado que exista solamente dentro del cluster.
