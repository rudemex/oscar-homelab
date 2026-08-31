---
title: Restic
sidebar_position: 18
---

# Restic

**Estado:** Objetivo · Backup  
**Dónde corre:** clientes/VMs que necesiten backup de archivos  
**Sizing inicial:** bajo; CPU aumenta con cifrado/compresión según flujo  
**Red/puertos:** según backend de destino  
**Persistencia:** repositorio de backup cifrado

## Rol dentro de O.S.C.A.R.

- backup de configs
- volúmenes pequeños
- copias off-site
- retención y snapshots

## Ejemplo concreto

Backup nocturno de `/srv/oscar` a repositorio cifrado; check semanal; restore drill mensual de una carpeta aleatoria.

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

La password del repositorio debe existir fuera del host respaldado. Probar restore regularmente.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Esta página es distinta a las demás: Restic ES la herramienta de backup, así que acá se trata de proteger el propio mecanismo de backups, no de tener un backup de Restic.

El punto crítico es la **contraseña del repositorio**: sin ella, todos los snapshots son irrecuperables, porque Restic cifra todo el repositorio. Esa contraseña debe guardarse en un gestor de contraseñas y tener al menos una copia offline/impresa fuera del homelab — nunca solo en un archivo dentro del mismo host que se está respaldando.

Además, el repositorio Restic en sí (donde viven los snapshots) debe existir en al menos dos ubicaciones físicas distintas para cumplir 3-2-1 (ver [estrategia-321.md](../backup-dr/estrategia-321.md)); no tiene sentido que el único repositorio Restic viva en el mismo disco que respalda.

Mantenimiento: correr `restic check` periódicamente para detectar corrupción del repositorio antes de necesitarlo en una emergencia real.

## Observabilidad

- que el job programado de backup termine sin error (código de salida);
- resultado de `restic check`;
- tamaño y crecimiento del repositorio, para anticipar necesidad de más storage o de una política de retención con `restic forget`.

## Troubleshooting

**El backup programado falla** → repositorio bloqueado por un job anterior interrumpido, o credenciales del destino remoto vencidas → revisar el log del job, correr `restic unlock` si aplica, y ver el runbook [backup-fallido.md](../runbooks/backup-fallido.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://restic.readthedocs.io/
