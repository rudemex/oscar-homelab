---
title: Instalar Argo CD
sidebar_position: 7
---

# Argo CD paso a paso

:::caution Corregido tras la experiencia real
- El `kubectl apply -f .../install.yaml` de abajo falló en la instalación real (`v3.5.2`) con `metadata.annotations: Too long: may not be more than 262144 bytes` al crear el CRD de `ApplicationSet` — es un límite del annotation `last-applied-configuration` que genera el apply client-side por defecto contra un CRD grande. Se resolvió con `kubectl apply --server-side -f ...` (y `--force-conflicts` si el primer intento parcial ya dejó algunos recursos aplicados client-side).
- Si el repo GitOps es **privado** (recomendado, ver [ADR-004](../arquitectura/decisiones-arquitectonicas.md)), Argo CD necesita credenciales registradas antes de poder sincronizar — no alcanza con `argocd app create --repo ...`. Se usó una **deploy key SSH de solo lectura** específica del repo (`gh api repos/<owner>/<repo>/keys` con `read_only=true`), registrada como Secret con label `argocd.argoproj.io/secret-type: repository` — nunca el token personal de una cuenta (demasiado amplio para vivir dentro del cluster).
:::

## 1. Precondiciones

```bash
kubectl get nodes
kubectl get pods -A
```

Todo debe estar estable antes de sumar GitOps.

## 2. Namespace

```bash
kubectl create namespace argocd
```

## 3. Instalar

Manifest oficial de Argo CD, fijando una versión concreta en vez de `stable` para que la instalación sea reproducible (reemplazar `v2.13.2` por la versión vigente al momento de instalar — ver [releases de Argo CD](https://github.com/argoproj/argo-cd/releases)):

```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.13.2/manifests/install.yaml
```

Esperar a que todos los pods queden `Running`:

```bash
kubectl -n argocd get pods -w
```

Anotar la versión instalada en la [bitácora](/bitacora) o en `inventory/services.yaml` — no queda registrada en ningún otro lado.

## 4. Acceso inicial

Para bootstrap se puede usar port-forward sin publicar el UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Obtener la contraseña inicial del usuario `admin` (Argo CD la genera y la guarda cifrada en un Secret):

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Entrar a `https://localhost:8080` (certificado autofirmado, el navegador va a advertir — es esperable en este paso) con usuario `admin` y esa contraseña, cambiarla desde la UI o con `argocd account update-password`, y borrar el Secret inicial una vez cambiada:

```bash
kubectl -n argocd delete secret argocd-initial-admin-secret
```

Después definir el método de autenticación/acceso definitivo (SSO, Cloudflare Access delante del port-forward, etc. — ver [exposición a Internet](../seguridad/exposicion-internet.md)); no dejar el `admin` local como único método de acceso a largo plazo.

## 5. Repo demo

Con el [CLI de Argo CD](https://argo-cd.readthedocs.io/en/stable/cli_installation/) instalado y logueado (`argocd login localhost:8080`), crear una Application apuntando al ejemplo `whoami` del repo GitOps:

```bash
argocd app create whoami \
  --repo https://github.com/<tu-usuario>/oscar-gitops.git \
  --path apps/whoami \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace oscar-lab
```

Ver [demo GitOps](../despliegues/gitops-demo.md) para el circuito completo de sync/diff/rollback sobre esta Application.

## 6. Sync manual

Primeras pruebas con sync manual. Observar:

- desired state;
- live state;
- diff;
- health;
- history.

## 7. Auto-sync

Habilitar después de entender:

- self-heal;
- prune;
- qué sucede si se borra un manifest del repo.

## 8. Recuperación

Argo debe poder reinstalarse desde documentación/Git. No convertir su propia configuración en un estado que exista solamente dentro del cluster.
