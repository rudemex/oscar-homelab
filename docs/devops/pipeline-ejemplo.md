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

El motor de CI concreto (Forgejo Actions, GitLab Runner, Woodpecker, etc.) todavía es una [decisión pendiente](../servicios/ci-runner.md). El pseudocódigo siguiente expresa las etapas independientemente del producto; la sintaxis real se escribe recién cuando el ADR se cierre.

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

Notas de portabilidad: si el motor elegido es **Forgejo Actions**, la sintaxis real usa `on:`/`jobs:`/`steps:` (compatible con GitHub Actions); si es **GitLab Runner**, la sintaxis de arriba ya es válida `.gitlab-ci.yml`. En ambos casos, el job real debe usar el método de build elegido y credenciales del registry con permisos mínimos.

## Deploy GitOps

En vez de dar `cluster-admin` al runner, una opción es que CI modifique el repo GitOps mediante PR/commit controlado. Argo CD hace la reconciliación.
