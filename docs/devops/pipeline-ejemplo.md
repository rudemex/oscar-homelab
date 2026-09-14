---
title: Pipeline de ejemplo
sidebar_position: 4
---

# Pipeline de referencia

Una aplicación simple puede recorrer:

```text
lint -> unit-test -> build -> scan -> push -> deploy -> smoke-test
```

## Pseudopipeline (agnóstico de motor)

El motor de CI es **Forgejo Actions** ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)), pendiente de despliegue — ver [CI Runner](../servicios/ci-runner.md). El pseudocódigo siguiente expresa las etapas independientemente del producto; la sintaxis real (`on:`/`jobs:`/`steps:`) se escribe recién cuando Forgejo esté desplegado.

```yaml
stages: [test, build, publish, deploy]

test:
  stage: test
  script:
    - npm ci
    - npm test

build-image:
  stage: build
  script:
    - docker build -t "$IMAGE:$CI_COMMIT_SHA" .

publish:
  stage: publish
  script:
    - docker push "$IMAGE:$CI_COMMIT_SHA"
```

La sintaxis real en Forgejo Actions usa `on:`/`jobs:`/`steps:` (compatible con GitHub Actions), no el formato `stages:`/`script:` del pseudocódigo de arriba. El job real debe usar el método de build elegido y credenciales del registry (Nexus, ADR-009) con permisos mínimos.

## Deploy GitOps

En vez de dar `cluster-admin` al runner, una opción es que CI modifique el repo GitOps mediante PR/commit controlado. Argo CD hace la reconciliación.
