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

El motor de CI es **Forgejo Actions** ([ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local)), corriendo en el [CI Runner](../servicios/ci-runner.md). Este workflow es el real, tomado de [`ci-demo`](http://git.oscar.home/mdelgado/ci-demo) — corre de punta a punta con `status: success`, imagen confirmada en Nexus **y despliegue real en Argo CD sin ningún paso manual**, después de encontrar 10 problemas reales que un pseudocódigo nunca hubiera anticipado (ver [Gotchas reales](../servicios/ci-runner.md#gotchas-reales-encontrados-con-el-pipeline-completo-no-obvios-de-antemano) en CI Runner):

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

      - name: Actualizar tag en oscar-gitops
        run: |
          apt-get install -y -qq sed
          git config --global user.email "ci@oscar.home"
          git config --global user.name "CI (ci-demo)"
          git -c http.extraHeader="Authorization: token ${{ secrets.GITOPS_TOKEN }}" clone http://git.oscar.home/mdelgado/oscar-gitops.git /tmp/oscar-gitops
          cd /tmp/oscar-gitops
          sed -i "s|tag: .*|tag: ${{ github.sha }}|" apps/ci-demo/values.yaml
          git add apps/ci-demo/values.yaml
          git commit -m "ci-demo: actualizar tag a ${{ github.sha }}" || echo "sin cambios"
          git -c http.extraHeader="Authorization: token ${{ secrets.GITOPS_TOKEN }}" push http://git.oscar.home/mdelgado/oscar-gitops.git main
```

Diferencias reales contra lo que decía esta página antes: la sintaxis es `on:`/`jobs:`/`steps:` (compatible con GitHub Actions, no `stages:`/`script:` estilo GitLab), las variables de contexto son `github.*` (no `gitea.*`, pese a ser Forgejo — ver gotcha #1), y el `docker build`/`push` necesitó dos ajustes de infraestructura que no son parte del YAML: `docker_host: automount` en la config del runner y `insecure-registries` en el daemon Docker del host (Nexus corre HTTP plano). Credenciales (`NEXUS_USER`, `NEXUS_PASSWORD`, `GITOPS_TOKEN`) van como **secrets de Forgejo Actions a nivel usuario** (no por repo — ver [Forgejo: secrets a nivel usuario](../servicios/forgejo.md#secrets-y-variables-de-actions-nivel-usuario-no-solo-por-repo)), nunca en el YAML — `NEXUS_USER`/`NEXUS_PASSWORD` son el usuario `ci-forgejo` con rol acotado a push en `docker-hosted` únicamente, no la cuenta admin de Nexus; `GITOPS_TOKEN` es un token de acceso de Forgejo con permiso de escritura sobre `oscar-gitops` únicamente.

El último paso, `git clone` necesita el header de auth igual que el `push` — clonar un repo privado sin credenciales también requiere autenticación, no solo escribir en él (gotcha #10 en CI Runner).

## Deploy GitOps

Implementado, no es una opción a futuro: el último step del workflow de arriba clona `oscar-gitops`, actualiza `apps/ci-demo/values.yaml` con el `sha` del commit recién construido, y lo pushea a `main` — sin darle `cluster-admin` ni ninguna credencial de Kubernetes al runner. Argo CD, con `syncPolicy.automated` en la `Application` de `ci-demo`, detecta el cambio y hace la reconciliación solo. Validado con `kubectl exec` contra el pod real, confirmando el código del último commit corriendo — sin ningún `kubectl apply` manual de por medio.
