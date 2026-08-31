---
title: Catálogo de ejemplos
sidebar_position: 1
---

# Ejemplos de despliegue

Los ejemplos de esta sección tienen dos objetivos: enseñar una tecnología y convertirse en smoke tests de la plataforma.

| Ejemplo | Plataforma | Aprende |
|---|---|---|
| [Whoami en Docker](./docker-whoami.md) | Docker | red, puertos, healthcheck |
| [Whoami en Kubernetes](./kubernetes-whoami.md) | k3s | Services, Ingress, DNS interno |
| [API + PostgreSQL](./docker-api-postgres.md) | Docker | persistencia, env vars, backup |
| [GitOps end-to-end](./gitops-demo.md) | k3s + Argo CD | reconciliación y rollback declarativo |

Los manifiestos reutilizables viven también bajo `examples/` en la raíz del repositorio.

## Pipeline completo ("Hello O.S.C.A.R.")

El recorrido completo pedido en el roadmap — `git push → CI → build image → Nexus → actualizar manifiesto → Argo CD → k3s` — no es un ejemplo aislado: es la combinación de dos páginas que ya cubren cada mitad del circuito:

1. [Pipeline de referencia](../devops/pipeline-ejemplo.md): las etapas de CI (lint, test, build, push a Nexus) sobre una app Node simple.
2. [Demo GitOps](./gitops-demo.md): qué pasa desde que el manifiesto cambia en Git hasta que Argo CD lo reconcilia en k3s.

Cuando el ADR de plataforma Git/CI ([decisión pendiente](../servicios/ci-runner.md)) se cierre, esta página puede sumar un ejemplo único de punta a punta con el motor de CI real elegido; hasta entonces, mantener las dos mitades separadas evita documentar un pipeline concreto que dependa de un producto todavía no decidido.

Ideas de ejemplo para sumar más adelante (no existen todavía, no hay que buscarlos en `examples/`): frontend + API separados en dos Deployments con Ingress compartido, y un worker con cola (Redis) sin puerto HTTP. Se agregan cuando haya una necesidad real de aprender ese patrón, no antes.
