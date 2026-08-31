---
title: GitOps end-to-end
sidebar_position: 5
---

# Demo GitOps

## Objetivo

Demostrar el circuito completo sin tocar una app crítica.

1. repo contiene Deployment de `whoami`;
2. Argo CD sincroniza;
3. cambiar tag/replicas en una rama;
4. revisar diff;
5. merge;
6. observar sync;
7. validar health;
8. revertir commit;
9. observar rollback declarativo.

## Éxito

Si podemos destruir manualmente un Pod y Kubernetes lo recrea, y podemos alterar el Deployment y Argo lo devuelve al estado Git, entendimos dos niveles distintos de reconciliación.
