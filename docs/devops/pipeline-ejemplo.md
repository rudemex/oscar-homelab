---
title: Pipeline de ejemplo
sidebar_position: 4
---

# Pipeline de referencia

Una aplicación simple puede recorrer:

```text
lint -> unit-test -> build -> scan -> push -> deploy -> smoke-test
```

## Pipeline real (validado, no pseudocódigo)

El motor de CI es **Forgejo Actions** ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)), corriendo en el [CI Runner](../servicios/ci-runner.md). Este workflow es el real, tomado de [`ci-demo`](http://git.oscar.home/mdelgado/ci-demo) — corrió de punta a punta con `status: success` e imagen confirmada en Nexus, después de encontrar 5 problemas reales que un pseudocódigo nunca hubiera anticipado (ver [Gotchas reales](../servicios/ci-runner.md#gotchas-reales-encontrados-con-el-pipeline-completo-no-obvios-de-antemano) en CI Runner):

```yaml
name: CI/CD
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: docker
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm install

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm test

      - name: Instalar Docker CLI
        run: |
          apt-get update -qq
          apt-get install -y -qq docker.io

      - name: Build Docker image
        run: docker build -t 192.168.0.151:8082/ci-demo:${{ github.sha }} -t 192.168.0.151:8082/ci-demo:latest .

      - name: Login a Nexus
        run: echo "${{ secrets.NEXUS_PASSWORD }}" | docker login 192.168.0.151:8082 -u "${{ secrets.NEXUS_USER }}" --password-stdin

      - name: Push a Nexus
        run: |
          docker push 192.168.0.151:8082/ci-demo:${{ github.sha }}
          docker push 192.168.0.151:8082/ci-demo:latest
```

Diferencias reales contra lo que decía esta página antes: la sintaxis es `on:`/`jobs:`/`steps:` (compatible con GitHub Actions, no `stages:`/`script:` estilo GitLab), las variables de contexto son `github.*` (no `gitea.*`, pese a ser Forgejo — ver gotcha #1), y el `docker build`/`push` necesitó dos ajustes de infraestructura que no son parte del YAML: `docker_host: automount` en la config del runner y `insecure-registries` en el daemon Docker del host (Nexus corre HTTP plano). Credenciales del registry (`NEXUS_USER`/`NEXUS_PASSWORD`) van como **repo secrets** de Forgejo, nunca en el YAML — usuario `ci-forgejo` con rol acotado a push en `docker-hosted` únicamente, no la cuenta admin de Nexus.

## Deploy GitOps

En vez de dar `cluster-admin` al runner, una opción es que CI modifique el repo GitOps mediante PR/commit controlado. Argo CD hace la reconciliación.
