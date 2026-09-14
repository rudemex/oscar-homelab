---
title: CI Runner
sidebar_position: 6
---

# CI Runner

**Estado:** Objetivo · Decisión tomada ([ADR-010](./forgejo.md)), pendiente de despliegue
**Dónde corre:** VM `devops01` o runners efímeros
**Sizing inicial:** depende de builds; comenzar 2 vCPU/4 GB y medir
**Red/puertos:** salida HTTPS hacia la plataforma Git/CI elegida; no requiere panel público
**Persistencia:** cache de builds, config y artefactos temporales

:::info Motor decidido, despliegue pendiente
[ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local) cerró la decisión: **Forgejo Actions** (sintaxis compatible con GitHub Actions) es el motor de CI, corriendo sobre la instancia de Forgejo — no se suma un producto de CI separado.

Alternativas descartadas en el mismo ADR: GitLab Runner (implica correr GitLab, descartado por peso — ver ADR-010) y Woodpecker CI/Drone (runner desacoplado del Git server, redundante teniendo Actions integrado en Forgejo).

Esta página describe el rol y las prácticas de seguridad del runner; los detalles de instalación se agregan cuando Forgejo esté desplegado.
:::

## Rol dentro de O.S.C.A.R.

- compilar proyectos Node
- crear imágenes OCI
- ejecutar tests
- desplegar a k3s o EasyPanel con credenciales acotadas

## Ejemplo concreto

Pipeline: lint → test → build image → push Nexus → actualizar tag GitOps → Argo CD despliega. Ver [pipeline de referencia](../devops/pipeline-ejemplo.md) para el detalle de cada etapa.

## Checklist de despliegue

- [ ] plataforma Git/CI decidida (ver ADR pendiente);
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

No usar un runner privilegiado compartido para jobs no confiables. Separar runners por nivel de confianza.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados (el acceso al socket Docker desde un runner equivale a acceso root en el host);
- separar secretos de la configuración versionada.

## Backup y restore

Documentar específicamente:

1. qué directorios/DB contienen estado;
2. si la aplicación necesita dump consistente;
3. dónde se guarda la copia;
4. cómo restaurarla en una instancia aislada;
5. cuánto tarda una recuperación real.

## Observabilidad

Como mínimo:

- disponibilidad HTTP/TCP;
- consumo de CPU/RAM;
- tamaño del volumen;
- reinicios del proceso/contenedor;
- logs de errores.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

- Forgejo Actions: https://forgejo.org/docs/latest/user/actions/
- GitLab Runner: https://docs.gitlab.com/runner/
- Woodpecker CI: https://woodpecker-ci.org/docs/intro
