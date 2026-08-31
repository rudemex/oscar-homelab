---
title: Bootstrap de Argo CD
sidebar_position: 4
---

# Bootstrap de Argo CD

## Flujo objetivo

```mermaid
flowchart LR
  GIT[Git] --> ARGO[Argo CD]
  ARGO --> K3S[k3s]
  K3S --> APP[Aplicaciones]
```

## Repo sugerido

```text
oscar-gitops/
├── apps/
│   ├── whoami/
│   ├── demo-api/
│   └── monitoring/
├── clusters/
│   └── oscar/
└── README.md
```

## Bootstrap manual permitido

Argo CD tiene un problema inevitable de bootstrap: algo debe instalarlo la primera vez. Ese paso manual/scriptado se documenta y, desde entonces, la mayor cantidad posible de configuración se mueve a Git.

## Reglas

- no guardar kubeconfig/tokens en Git;
- evitar auto-sync destructivo en primeras pruebas;
- entender pruning antes de habilitarlo;
- revisar diffs antes de cambiar CRDs o storage;
- tener un camino de acceso si el Ingress falla.
