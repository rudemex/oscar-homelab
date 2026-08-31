---
title: Pipeline objetivo
sidebar_position: 1
---

# DevOps en O.S.C.A.R.

La plataforma DevOps permite practicar un ciclo completo sin depender de infraestructura corporativa.

```mermaid
flowchart LR
  DEV[Commit] --> GIT[Git]
  GIT --> CI[Runner CI]
  CI --> TEST[Test]
  TEST --> IMG[Build image]
  IMG --> NEXUS[Nexus]
  NEXUS --> GITOPS[Repo GitOps]
  GITOPS --> ARGO[Argo CD]
  ARGO --> K3S[k3s]
  K3S --> OBS[Observabilidad]
```

## Principio

El artefacto promovido es el mismo artefacto probado. Evitar reconstruir una imagen diferente para cada ambiente.

## Ejemplo

`demo-api:1.4.2`:

1. CI ejecuta tests;
2. genera imagen OCI;
3. publica en Nexus;
4. actualiza manifest GitOps;
5. Argo despliega;
6. Uptime Kuma verifica endpoint;
7. Grafana muestra métricas.
