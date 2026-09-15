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

## Pipeline completo ("Hello O.S.C.A.R.") — ya existe, no es un ejercicio aislado

El recorrido completo `git push → CI → build image → Nexus → actualizar manifiesto → Argo CD → k3s` **ya está armado y validado de punta a punta**, no es solo un plan — es la app real `ci-demo` (repo en Forgejo, `http://git.oscar.home/mdelgado/ci-demo`, chart en `oscar-gitops/apps/ci-demo`). El ADR que esta página dejaba pendiente ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local): Forgejo + Forgejo Actions) ya se cerró y desplegó:

1. [CI Runner](../servicios/ci-runner.md): el motor de CI real (Forgejo Actions), desplegado en `devops01`, con el detalle de cada gotcha encontrado al validarlo.
2. [Pipeline de referencia](../devops/pipeline-ejemplo.md): el workflow YAML real (no pseudocódigo) — lint, test, build, push a Nexus, actualización del manifiesto en `oscar-gitops`.
3. [Demo GitOps](./gitops-demo.md): qué pasa desde que el manifiesto cambia en Git hasta que Argo CD lo reconcilia en k3s — mismo mecanismo que usa `ci-demo`, con `whoami` como ejercicio didáctico más simple para practicarlo antes de leer el pipeline real completo.

Ideas de ejemplo para sumar más adelante (no existen todavía, no hay que buscarlos en `examples/`): frontend + API separados en dos Deployments con Ingress compartido, y un worker con cola (Redis) sin puerto HTTP. Se agregan cuando haya una necesidad real de aprender ese patrón, no antes.
