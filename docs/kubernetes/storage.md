---
title: Persistencia en Kubernetes
sidebar_position: 5
---

# Storage en k3s

Los workloads stateless son simples; los datos persistentes requieren decisiones explícitas.

## Fase inicial

Para laboratorios, el local-path provisioner puede ser suficiente. La consecuencia es que el volumen queda ligado al nodo.

## Fase futura

Con NAS se puede evaluar NFS/CSI según caso. Antes de usar storage distribuido complejo, preguntarse qué problema real resuelve en un cluster pequeño.

## Regla para bases de datos

No colocar una base importante en k3s solamente para “tener todo en Kubernetes”. Primero demostrar:

- backup consistente;
- restore;
- storage sano;
- límites/requests;
- mantenimiento del nodo.
