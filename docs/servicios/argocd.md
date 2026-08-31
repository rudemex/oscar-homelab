---
title: Argo CD
sidebar_position: 7
---

# Argo CD

**Estado:** Objetivo · GitOps  
**Dónde corre:** cluster k3s  
**Sizing inicial:** ~1–2 GB RAM para instalación pequeña, validar métricas  
**Red/puertos:** UI/API interna; acceso administrativo protegido  
**Persistencia:** estado principalmente reconstruible; config declarativa en Git

## Rol dentro de O.S.C.A.R.

- sincronizar Helm/manifests
- detectar drift
- hacer rollbacks declarativos
- operar múltiples apps desde un repo

## Ejemplo concreto

Cambiar `replicas: 2` en Git; Argo CD detecta el commit y reconcilia el Deployment sin ejecutar `kubectl apply` manual.

## Checklist de despliegue

- [ ] hostname y ubicación decididos;
- [ ] imagen/versión fijada, evitando tags flotantes en servicios importantes;
- [ ] puertos documentados;
- [ ] volumen/persistencia definida;
- [ ] `.env.example` sin secretos en Git;
- [ ] credenciales reales fuera de Git;
- [ ] backup definido antes de cargar datos importantes;
- [ ] healthcheck o monitor de disponibilidad;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado.

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
