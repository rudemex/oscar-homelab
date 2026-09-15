---
title: Argo CD
sidebar_position: 7
---

# Argo CD

**Estado:** Actual — desplegado en `k3s01`, 3 Applications reales corriendo (`root-app`, `oscar-led-controller`, `ci-demo`), todas `Synced` contra Forgejo  
**Dónde corre:** `k3s01` (192.168.0.150), namespace `argocd`  
**Sizing inicial:** ~1–2 GB RAM para instalación pequeña, validar métricas  
**Red/puertos:** `argocd-server` es `ClusterIP` (80/443, sin `LoadBalancer`/ServiceLB) — se expone vía `Ingress` de Traefik en `http://argocd.oscar.home` (manifiesto real en `oscar-gitops/clusters/oscar/argocd-server-ingress.yaml`), solo alcanzable desde la LAN con DNS apuntado a AdGuard — nunca a internet (ADR-005)  
**Persistencia:** estado principalmente reconstruible; config declarativa en el repo `oscar-gitops` (origen real en Forgejo desde [ADR-012](../arquitectura/decisiones-arquitectonicas.md#adr-012--forgejo-como-mirror-de-solo-lectura-de-oscar-gitops-no-origen), no GitHub)

## Applications reales

| Application | Namespace | Sync | Health | Notas |
|---|---|---|---|---|
| `root-app` | `argocd` | Manual (sin `automated`, a propósito — ver Troubleshooting) | Healthy | app-of-apps, apunta a `clusters/oscar/` en `oscar-gitops` |
| `oscar-led-controller` | `oscar-lab` | Automated | Progressing (`0/1`) | El pod está `Running` pero falla el readiness probe — el ESP32 físico está apagado, no es un problema de la plataforma. Ver [runbook](../runbooks/k3s-degradado.md) si en algún momento el ESP32 está prendido y sigue sin ponerse healthy. |
| `ci-demo` | `oscar-lab` | Automated (`selfHeal`, `prune`) | Healthy | Cierra el loop CI→registry→GitOps→deploy, ver [pipeline de ejemplo](../devops/pipeline-ejemplo.md) |

`root-app` sin `syncPolicy.automated` es intencional, no un olvido: el operador dispara el sync manual (`kubectl patch application root-app -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'` o desde la UI) para tener control explícito sobre cuándo se propaga un cambio en la estructura de `clusters/oscar/`, mientras que las Applications hoja (`oscar-led-controller`, `ci-demo`) sí son automáticas porque su blast radius es una sola app.

## Rol dentro de O.S.C.A.R.

- sincronizar Helm/manifests
- detectar drift
- hacer rollbacks declarativos
- operar múltiples apps desde un repo

## Ejemplo concreto

Cambiar `replicas: 2` en Git; Argo CD detecta el commit y reconcilia el Deployment sin ejecutar `kubectl apply` manual.

## Checklist de despliegue

- [x] hostname y ubicación decididos (`argocd.oscar.home`, Ingress Traefik en `k3s01`);
- [x] imagen/versión fijada — manifiesto oficial pineado a una tag concreta al instalar, no `stable`;
- [x] puertos documentados (`ClusterIP` 80/443 interno, expuesto por `Ingress`, no por `LoadBalancer`);
- [x] volumen/persistencia definida — reconstruible desde Git + `argocd admin export` para el resto (ver Backup abajo);
- [ ] `.env.example` sin secretos en Git — no aplica del mismo modo que un Docker Compose; la credencial del repo (`oscar-gitops-forgejo`) es un Secret de k8s, no un `.env`;
- [x] credenciales reales fuera de Git (Secret `oscar-gitops-forgejo` en el namespace `argocd`, nunca en el repo);
- [ ] backup definido antes de cargar datos importantes — el mecanismo (`argocd admin export`) está documentado pero no se corrió nunca en la práctica, no hay un backup real guardado todavía;
- [ ] healthcheck o monitor de disponibilidad — Homepage sí tiene el `siteMonitor`/estado de sync como widget, pero **no está sumado a Uptime Kuma** (confirmado: no aparece en `http://192.168.0.156:3001/api/status-page/oscar`, a diferencia de Forgejo y Nexus que sí);
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
