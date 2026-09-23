---
title: Argo CD
sidebar_position: 7
---

# Argo CD

**Estado:** Actual — desplegado en `k3s`, 8 Applications reales corriendo (`root-app`, `oscar-led-controller`, `ci-demo`, `searxng`, `infisical-operator`, `headlamp`, `argocd-config`, `coredns-custom`), todas `Synced` contra Forgejo  
**Dónde corre:** `k3s` (192.168.0.150), namespace `argocd`  
**Sizing inicial:** ~1–2 GB RAM para instalación pequeña, validar métricas  
**Red/puertos:** `argocd-server` es `ClusterIP` (80/443, sin `LoadBalancer`/ServiceLB) — se expone vía `Ingress` de Traefik en `http://argocd.oscar.home` (manifiesto en `oscar-gitops/infra/argocd/manifests/ingress.yaml`, gestionado por la Application `argocd-config`), solo alcanzable desde la LAN con DNS apuntado a AdGuard — nunca a internet (ADR-005)  
**Persistencia:** estado principalmente reconstruible; config declarativa en el repo `oscar-gitops` (origen real en Forgejo desde [ADR-012](../arquitectura/decisiones-arquitectonicas.md#adr-012--forgejo-como-mirror-de-solo-lectura-de-oscar-gitops-no-origen), no GitHub)

## Token de Homepage (rotado 2026-09-21)

El widget de Argo CD en Homepage usa una cuenta propia de solo lectura, `homepage` (`accounts.homepage: apiKey` en `argocd-cm`), con un token JWT en el campo `key` del `services.yaml` de `core`. El 2026-09-21 el token anterior quedó expuesto en una salida de consola y se **rotó**: se generó uno nuevo por la API (`POST /api/v1/account/homepage/token`, con la sesión de `admin`), se verificó el widget (lee las 8 aplicaciones) y recién entonces se **revocó el viejo** (`DELETE /api/v1/account/homepage/token/<id>`, comprobado con `401`). El valor vive solo en Vaultwarden y en el `services.yaml`; no está en Git. Para rotarlo de nuevo, el mismo procedimiento; el `id` del token es el `jti` de su JWT.

## Applications reales

| Application | Namespace | Sync | Health | Notas |
|---|---|---|---|---|
| `root-app` | `argocd` | Manual (sin `automated`, a propósito — ver Troubleshooting) | Healthy | app-of-apps — descubre `apps/*/application.yaml` e `infra/*/application.yaml` en `oscar-gitops` (ver "Estructura del repo" abajo). Su propio manifiesto vive en `clusters/oscar/root-app.yaml`, pero eso es solo dónde vive el bootstrap, no lo que vigila. |
| `oscar-led-controller` | `oscar-lab` | Automated (`selfHeal`, `prune`) — antes era manual por error, aunque esta doc decía lo contrario | Progressing / Degraded (`0/1`) | El pod está `Running` pero falla el readiness probe — el ESP32 físico está apagado, no es un problema de la plataforma. Tras un rollout reciente Kubernetes marca el plazo vencido (`ProgressDeadlineExceeded`) y Argo CD lo muestra `Degraded` en vez de `Progressing`: mismo estado de fondo. Ver [runbook](../runbooks/k3s-degradado.md) si en algún momento el ESP32 está prendido y sigue sin ponerse healthy. Código en Forgejo (`mdelgado/oscar-led-controller`); la imagen es local y **se despliega a mano** (comandos en el `values.yaml` del chart), ver [LED de estado](../hardware/led-status.md#código-fuente-y-despliegue). |
| `ci-demo` | `oscar-lab` | Automated (`selfHeal`, `prune`) | Healthy | Cierra el loop CI→registry→GitOps→deploy, ver [pipeline de ejemplo](../devops/pipeline-ejemplo.md) |
| `searxng` | `oscar-ai` | Automated | Healthy | Metabuscador, primera pieza de la capa OSCAR AI (Fase 1 del spec de Hermes). Chart propio `apps/searxng/`, secret desde Infisical. Publicado en `searxng.oscar.home` solo para probar. |
| `infisical-operator` | `infisical-operator-system` | Automated | Healthy | Chart oficial de Infisical (fuente Helm remota, no un chart propio), versión fija `v0.11.9` — sincroniza `Secret`s de k8s desde Infisical. Ver [gestión de secretos](../seguridad/secretos.md#secrets-en-gitops-k3s--argo-cd). |
| `headlamp` | `headlamp` | Automated | Healthy | UI de exploración del cluster (pods/logs/eventos) — complementa a Argo CD, que se enfoca en estado de sync, no en explorar recursos sueltos. Login por token de ServiceAccount (`cluster-admin`), no usuario/contraseña — token real en Vaultwarden. Publicado en `headlamp.oscar.home`. Chart fijo `0.45.0`; los valores viven en `infra/headlamp/values.yaml` (multi-source con `ref: values`). |
| `argocd-config` | `argocd` | Automated | Healthy | Ingress de `argocd-server` (antes un archivo en `clusters/oscar/` que nada sincronizaba). Solo maneja ese Ingress: la instalación de Argo CD sigue siendo manual. |
| `coredns-custom` | `kube-system` | Automated | Healthy | ConfigMap `coredns-custom` con `git.oscar.home` e `infisical.oscar.home` → `192.168.0.156` (antes existía solo en el cluster). **CoreDNS no recarga solo**: tras cambiarlo, `kubectl -n kube-system rollout restart deploy coredns`. |

`root-app` sin `syncPolicy.automated` es intencional, no un olvido: el operador dispara el sync manual (`kubectl patch application root-app -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'` o desde la UI) para tener control explícito sobre cuándo se propaga un cambio en la estructura del repo, mientras que las Applications hoja (`ci-demo`, `searxng`, `infisical-operator`, `headlamp`) sí son automáticas porque su blast radius es una sola app. Las Applications **no llevan finalizer** de borrado en cascada a propósito: borrar una (ej. `oscar-led-controller`) no debe llevarse su PVC con datos.

**Gotcha real, encontrado dos veces (2026-09-19 y 2026-09-20):** como `root-app` es manual, un cambio a `clusters/oscar/root-app.yaml` **tampoco** se propaga solo — hay que `kubectl apply -f` ese archivo puntual a mano antes de esperar que el sync manual haga algo. Pasa fácil de olvidar porque el resto del repo sí es autodiscovery: la única pieza que de verdad requiere tocar el cluster a mano es ese único archivo.

### Estructura del repo (2026-09-20)

```text
oscar-gitops/
├── clusters/oscar/     # solo el bootstrap: root-app.yaml, aplicado a mano
├── apps/                # apps propias de OSCAR (ci-demo, oscar-led-controller)
└── infra/                # plataforma de la que las apps dependen, pero que
                          # no es "una app de OSCAR" (infisical-operator, headlamp, argocd-config, coredns-custom)
```

Hay tres formas de pieza: chart propio (`Chart.yaml`+`templates/`), chart de terceros (`application.yaml` con versión fija + `values.yaml`) y manifests planos (`manifests/`). Lo que queda fuera de Git a propósito (instalación de Argo CD y sus ajustes, secrets de arranque) está listado en el README del repo.

Inspirada en un repo real de referencia revisado en sesión (no copiado 1:1 — se mantuvo el autodiscovery de `root-app` en vez de pasar a un `Application` manual por servicio, que es más control explícito pero más pasos para agregar algo nuevo).

Todas las apps siguen el mismo layout en `values.yaml` (inspirado en un repo de referencia). Criterio: **`values.yaml` solo tiene valores de la app**. Lo que es igual para toda la plataforma (dónde está Infisical, el proyecto, la credencial de acceso, los nombres derivados) o es cableado interno del chart (probes, estrategia de rollout, rutas de volúmenes) vive en `templates/`.

```yaml
hpa: {enabled: false, minReplicas: 1, maxReplicas: 1, cpuUtilization: 80}   # opcional

backend:
  image: {repository: …, tag: …, pullPolicy: …}
  replicaCount: 1
  historyLimitReplicas: 1
  resources: {…}
  service: {port: 3000}
  ingress: {enabled: true, host: mi-app.oscar.home}
  configmap:                      # variables NO secretas   NOMBRE: valor   → ConfigMap <chart>-cm
    PORT: 3000
  secrets:                        # CLAVE_K8S: NOMBRE_EN_INFISICAL          → Secret <chart>-sc
    APP_USER: SECRET_APP_USER
    APP_PASS: SECRET_APP_PASS
```

Agregar una variable o un secret es agregar una línea en `values.yaml`: `templates/config-map.yaml` y `templates/secrets.yaml` solo iteran esos mapas. **Los secrets se leen de Infisical por convención, no por configuración:** proyecto "OSCAR Apps", ambiente `prod`, carpeta `/<nombre-del-chart>` (`/ci-demo`, `/searxng`); el host de Infisical, el `projectId` y la identidad de acceso (`infisical-universal-auth`) están en `templates/secrets.yaml`. Los nombres de los recursos se derivan del chart (`<chart>-cm`, `<chart>-sc`); el Deployment lleva `revisionHistoryLimit`, `CURRENT_COMMIT` (= tag de la imagen) y un checksum del ConfigMap para reiniciar el Pod cuando cambia una variable. Caso especial: `imagePullSecret: true` en `ci-demo` (k8s exige un único JSON `dockerconfigjson`): el template arma el JSON con `NEXUS_USER`/`NEXUS_PASSWORD` de la carpeta del chart y deriva el registry del host de `image.repository`.

**Diferencias deliberadas con el repo de referencia:** no se replica `namespace` en `values.yaml` (lo da el `Application`, tenerlo dos veces es duplicar la fuente de verdad), ni el nombre `<chart>-svc` del Service ni las labels `-backend` (el selector de un Deployment vivo es inmutable, y `searxng.oscar-ai.svc` ya es el nombre que usa el resto). `oscar-led-controller` usa `Recreate` en vez de `RollingUpdate`: su readiness depende del WLED físico, y con el ESP32 apagado un Pod nuevo no llega nunca a `Ready` (el rollout no termina y quedan dos Pods sobre el mismo PVC).

**Límites conocidos:** las constantes de la plataforma están repetidas en el `secrets.yaml` de cada chart (no hay librería compartida a propósito; si crecen las apps con secrets, una librería Helm local las centralizaría); cambiar un valor en Infisical actualiza el `Secret` pero no reinicia el Pod solo; y el CI de `ci-demo` reemplaza con `sed` toda línea `tag: ` de su `values.yaml` (no agregar otra clave `tag:`). Referencias: `apps/searxng/` (la más simple), `apps/ci-demo/`, `apps/oscar-led-controller/`.

## Rol dentro de O.S.C.A.R.

- sincronizar Helm/manifests
- detectar drift
- hacer rollbacks declarativos
- operar múltiples apps desde un repo

## Ejemplo concreto

Cambiar `replicas: 2` en Git; Argo CD detecta el commit y reconcilia el Deployment sin ejecutar `kubectl apply` manual.

## Checklist de despliegue

- [x] hostname y ubicación decididos (`argocd.oscar.home`, Ingress Traefik en `k3s`);
- [x] imagen/versión fijada — manifiesto oficial pineado a una tag concreta al instalar, no `stable`;
- [x] puertos documentados (`ClusterIP` 80/443 interno, expuesto por `Ingress`, no por `LoadBalancer`);
- [x] volumen/persistencia definida — reconstruible desde Git + `argocd admin export` para el resto (ver Backup abajo);
- [ ] `.env.example` sin secretos en Git — no aplica del mismo modo que un Docker Compose; la credencial del repo (`oscar-gitops-forgejo`) es un Secret de k8s, no un `.env`;
- [x] credenciales reales fuera de Git (Secret `oscar-gitops-forgejo` en el namespace `argocd`, nunca en el repo);
- [ ] backup definido antes de cargar datos importantes — el mecanismo (`argocd admin export`) está documentado pero no se corrió nunca en la práctica, no hay un backup real guardado todavía;
- [x] healthcheck o monitor de disponibilidad — monitor `Argo CD (k3s)` en Uptime Kuma y en la status page (2026-09-20), además del `siteMonitor` de Homepage;
- [ ] métricas/logs incorporados cuando sea razonable — sin Prometheus/Grafana desplegado todavía, pendiente del stack de observabilidad;
- [ ] procedimiento de actualización y rollback documentado — el de password perdida y OutOfSync sí existen (ver Troubleshooting), el de actualizar la versión de Argo CD en sí no.

## Seguridad

Git es la intención; el cluster es el estado actual. Evitar cambios manuales permanentes que Argo luego revierta.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Por diseño, el estado deseado de Argo CD vive en Git (los manifiestos/Helm charts de cada Application), así que eso ya está respaldado por el propio repositorio GitOps; no hay que duplicarlo.

Lo que sí es estado propio de Argo CD y no está en Git son sus Secrets internos (credenciales de repos privados, configuración SSO/RBAC si se usa), guardados como Kubernetes Secrets en el namespace `argocd`. Para eso existe `argocd admin export`, que genera un backup completo de la configuración de Argo CD (Applications, Projects, Clusters, RBAC) reimportable con `argocd admin import`.

El resto del estado (etcd de k3s) se cubre en el backup de k3s; no se duplica acá.

Restore: reinstalar Argo CD y `argocd admin import` el export; las Applications sincronizan solas contra Git apenas el controller arranca.

## Observabilidad

- estado de sincronización por Application (`Synced`/`OutOfSync`/`Degraded`);
- salud del `application-controller` (pod en el namespace `argocd`);
- webhooks de Git no llegando, con fallback a poll periódico;
- tiempo desde el último sync exitoso por Application;
- reinicios del `application-controller` o `repo-server`.

## Troubleshooting

- **Una Application queda en `OutOfSync` permanente** → drift manual en el cluster, o el repo Git no es alcanzable → `argocd app diff`, revisar credenciales del repo configuradas en Argo CD.
- **`root-app` muestra `Synced` pero un cambio real (ej. `repoURL` de una app hija) no se propagó** → pasó de verdad al migrar `oscar-gitops` a Forgejo (ver [ADR-012](../arquitectura/decisiones-arquitectonicas.md#adr-012--forgejo-como-mirror-de-solo-lectura-de-oscar-gitops-no-origen)): `root-app` puede estar `Synced` contra una revisión vieja porque su sync es manual — "Synced" no significa "contra el HEAD más reciente". Forzar `kubectl patch application root-app -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD","prune":false}}}'` y recién ahí confirmar que las apps hijas tomaron el cambio real.
- **Una Application queda en `Degraded`** → el recurso subyacente no llega a estar healthy (CrashLoop, probes fallando) → ver [k3s degradado](../runbooks/k3s-degradado.md), revisar eventos del recurso con `kubectl describe`.
- **Los cambios en Git no se reflejan** → webhook no configurado o no llega, y el poll periódico todavía no corrió → forzar `argocd app sync` manual, verificar configuración del webhook en el repo Git.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://argo-cd.readthedocs.io/
