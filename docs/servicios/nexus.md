---
title: Sonatype Nexus Repository
sidebar_position: 4
---

# Sonatype Nexus Repository

**Estado:** Objetivo · DevOps  
**Dónde corre:** VM `devops01`  
**Sizing inicial:** 2–4 vCPU, 4–8 GB RAM; storage según artefactos  
**Red/puertos:** UI/repositories; publicar solo lo necesario en LAN  
**Persistencia:** blob stores, configuración y metadata

## Rol dentro de O.S.C.A.R.

- proxy/cache de npm
- registry Docker privado
- repositorio Maven para laboratorios Java
- hostear artefactos internos
- practicar políticas de retención

## Ejemplo concreto

Laboratorio: configurar npm proxy, apuntar un proyecto Node al registry interno, borrar `node_modules` y medir el efecto del cache en una segunda instalación.

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

Definir cleanup policies desde el comienzo; un registry sin retención puede consumir el disco silenciosamente.

El panel de administración y la API de Nexus no deben quedar expuestos sin autenticación fuerte: quien tiene acceso de admin puede leer y sobrescribir cualquier artefacto alojado.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Todo el estado vive en el volumen `/nexus-data`: blobstores (los binarios), la base de datos embebida de metadata y la configuración. No hay un dump SQL tradicional que alcance por sí solo.

Para un backup consistente, dos opciones:

- detener el contenedor y copiar el árbol completo de `/nexus-data`;
- en caliente, correr la tarea interna "Admin - Export databases for backup", que exporta la metadata a `nexus-data/backup/` sin bajar el servicio — pero igual hay que respaldar los blobstores aparte, porque los binarios no están en ese dump.

Restore: levantar una instancia nueva con volumen vacío, restaurar ahí el árbol `/nexus-data`, iniciar el contenedor y verificar que los componentes proxeados/alojados aparezcan en la UI.

Si Nexus se usa solo como proxy/cache de npm, es razonablemente recreable: se repuebla re-descargando. Pero si aloja artefactos propios (imágenes internas, builds), esos datos no son recreables y hay que tratarlos como críticos.

## Observabilidad

- endpoint de salud `/service/rest/v1/status`;
- tamaño del blobstore: crece silenciosamente si no hay cleanup policies — es la causa más común de "Nexus lleno";
- tareas de cleanup ejecutando sin error;
- disponibilidad HTTP/TCP y reinicios del contenedor;
- logs de errores.

## Troubleshooting

- **Nexus lleno / disco al 100%** → sin cleanup policies o blobstore sin límite → revisar tamaño del blobstore, configurar cleanup policy por edad/cantidad de componentes, correr la tarea de compactación del blobstore. Ver [`disco-lleno.md`](../runbooks/disco-lleno.md).
- **Componentes proxeados no se actualizan** → cache de proxy con TTL vencido o remoto inalcanzable → revisar configuración del proxy repository y conectividad de red hacia el remoto.
- **Nexus no arranca tras un restore** → volumen `/nexus-data` restaurado parcialmente (falta un blobstore) o permisos de archivo incorrectos → revisar logs de arranque del contenedor y comparar el árbol restaurado contra un backup íntegro. Ver [`docker-servicio-caido.md`](../runbooks/docker-servicio-caido.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://help.sonatype.com/
