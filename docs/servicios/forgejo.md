---
title: Forgejo / Git local
sidebar_position: 5
---

# Forgejo / Git local

**Estado:** Objetivo · Decisión pendiente  
**Dónde corre:** VM `devops01` o VM pequeña dedicada  
**Sizing inicial:** 1–2 vCPU, 1–2 GB RAM para uso personal  
**Red/puertos:** HTTP(S) y SSH si se habilita Git por SSH  
**Persistencia:** repositorios, DB, attachments y configuración

## Rol dentro de O.S.C.A.R.

- mirror de repositorios importantes
- repositorios privados del homelab
- GitOps completamente local
- practicar hooks y flujos de PR

## Ejemplo concreto

Ejemplo: repo `oscar-gitops` con manifests k3s; Argo CD observa el repo y sincroniza aplicaciones internas.

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

La plataforma Git definitiva queda como decisión explícita. No acoplar GitOps a un producto hasta cerrar el ADR.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Forgejo trae un comando de backup integrado, `forgejo dump`, que genera un único archivo comprimido con la base de datos, los repositorios Git completos, LFS y la configuración (`app.ini`) en un solo paso consistente. Es el mecanismo recomendado en vez de copiar directorios a mano.

Ese archivo debe salir del host inmediatamente: es una copia completa del código fuente que aloja el servidor Git interno.

Restore: `forgejo dump` genera un artefacto pensado para restaurarse en una instancia nueva siguiendo la guía oficial de "restore from dump". El restore debe probarse al menos una vez con un dump real; no asumir que funciona.

## Observabilidad

- endpoint `/api/healthz`;
- uso de disco del árbol de repositorios (crece con el tiempo, especialmente con LFS);
- jobs de Actions fallando, si se usa CI integrado;
- disponibilidad HTTP/SSH;
- reinicios del proceso/contenedor.

## Troubleshooting

- **`git push` falla con timeout** → disco lleno o proceso Forgejo sin memoria → ver [Disco lleno](../runbooks/disco-lleno.md), revisar espacio del volumen de repos y logs del contenedor.
- **`/api/healthz` no responde pero el contenedor está `Up`** → DB inaccesible o proceso colgado → ver [Servicio Docker caído](../runbooks/docker-servicio-caido.md), revisar logs de conexión a la base.
- **Un `forgejo dump` falla o queda incompleto** → falta de espacio temporal en disco durante el dump, o LFS muy grande para el timeout configurado → ver [Backup fallido](../runbooks/backup-fallido.md), revisar espacio libre y logs del dump.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://forgejo.org/docs/
