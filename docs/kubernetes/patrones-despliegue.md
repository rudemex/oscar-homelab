---
title: Patrones de despliegue
sidebar_position: 6
---

# Patrones de despliegue

## Stateless web

```text
Deployment -> Service -> Ingress
```

Ideal para APIs/frontends replicables.

## Worker

```text
Deployment -> Queue/DB
```

Sin Ingress. Escala por replicas o métricas.

## CronJob

Adecuado para tareas programadas idempotentes. No reemplaza n8n cuando el workflow necesita múltiples integraciones, estado humano o ramas complejas.

## Stateful

```text
StatefulSet -> PVC -> StorageClass
```

Usarlo cuando realmente se necesitan identidades/volúmenes estables.

## Requests y limits

Toda app persistente debería tender a definir requests. Los limits se ajustan con métricas; límites de memoria demasiado bajos provocan OOMKills y demasiado altos ocultan fugas.
