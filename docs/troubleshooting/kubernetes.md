---
title: Kubernetes
sidebar_position: 4
---

# Kubernetes

Orden rápido:

```bash
kubectl get nodes
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp
kubectl describe pod <pod>
kubectl logs <pod> --previous
```

## Pending

Revisar scheduling, recursos, PVC y taints.

## CrashLoopBackOff

Logs actuales/previous, config, secretos, probes.

## ImagePullBackOff

Nombre/tag, DNS, reachability del registry, credenciales.

## OOMKilled

Comparar consumo con limit; no subir el límite a ciegas sin entender crecimiento.
