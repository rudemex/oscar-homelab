---
title: Sonatype Nexus Repository
sidebar_position: 4
---

# Sonatype Nexus Repository

**Estado:** Actual — Nexus 3.96.1 corriendo en `devops01`, admin real configurado, acceso anónimo deshabilitado, repos npm y Docker creados y verificados
**Dónde corre:** VM `devops01`, `/srv/oscar/apps/nexus/` (comparte la VM con Forgejo y el CI Runner — ver [sizing real](./forgejo.md) tras la ampliación a 6 vCPU/12 GB)
**Sizing real:** sin overrides de JVM propios, usando los defaults de la imagen — medir antes de ajustar
**Red/puertos:** `8081` (UI/API), `8082` (registry Docker — puerto HTTP dedicado, Nexus lo requiere aparte de la UI)
**Persistencia:** `/srv/oscar/data/nexus` (blob stores, config, metadata — `chown 200:200`, uid con el que corre el proceso dentro del contenedor)

## Repositorios configurados

| Repositorio | Formato/tipo | Para qué |
|---|---|---|
| `npm-proxy` | npm, proxy | cache de `https://registry.npmjs.org` |
| `npm-hosted` | npm, hosted | paquetes propios |
| `npm-group` | npm, group (`npm-hosted`+`npm-proxy`) | endpoint único que usan los proyectos — `http://nexus.oscar.home:8081/repository/npm-group/` |
| `docker-hosted` | docker, hosted | destino real del `docker push` del [CI Runner](./ci-runner.md) — `192.168.0.151:8082` (puerto dedicado, no pasa por NPM) |

Todos creados vía la API REST (`POST /service/rest/v1/repositories/<formato>/<tipo>`), no a mano por la UI. Acceso anónimo deshabilitado durante el wizard de primer login — confirmado que **todos** los repos (incluido el proxy de npm, que en teoría solo cachea algo público) devuelven `401` sin credenciales.

**Pendiente real (solo por UI, sin API disponible):** cleanup policy para `docker-hosted` — el endpoint REST de cleanup policies devuelve `404` en esta versión (probado `v1` y `beta`, y no aparece en el propio swagger). Se arma a mano: **Administration → Repository → Cleanup Policies**, formato `docker`, criterio de antigüedad/último `pull`, y asignarla a `docker-hosted` en su configuración — sin esto, el blob store puede crecer sin límite (ver "Troubleshooting" abajo).

## Rol dentro de O.S.C.A.R.

- proxy/cache de npm
- registry Docker privado
- repositorio Maven para laboratorios Java
- hostear artefactos internos
- practicar políticas de retención

## Ejemplo concreto

Laboratorio: configurar npm proxy, apuntar un proyecto Node al registry interno, borrar `node_modules` y medir el efecto del cache en una segunda instalación.

## Checklist de despliegue

- [x] hostname y ubicación decididos (`devops01`, `nexus.oscar.home` para la UI, IP directa para el registry Docker);
- [x] imagen/versión fijada, evitando tags flotantes en servicios importantes (`3.96.1`);
- [x] puertos documentados (`8081` UI/API, `8082` Docker registry);
- [x] volumen/persistencia definida (`/srv/oscar/data/nexus`);
- [x] `.env.example` sin secretos en Git — no aplica, nada de esto vive en un repo Git, solo en la VM;
- [x] credenciales reales fuera de Git (admin real creado, en Vaultwarden);
- [ ] backup definido antes de cargar datos importantes — pendiente, hoy no hay artefactos reales cargados todavía;
- [ ] healthcheck o monitor de disponibilidad — falta sumarlo a Uptime Kuma/Beszel;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado;
- [ ] **cleanup policy del repo Docker** — bloqueada por API (ver arriba), pendiente por UI.

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
