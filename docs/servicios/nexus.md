---
title: Sonatype Nexus Repository
sidebar_position: 4
---

# Sonatype Nexus Repository

**Estado:** Actual — Nexus 3.96.1 corriendo en `devops`, admin real configurado, acceso anónimo deshabilitado, repos npm y Docker creados y verificados
**Dónde corre:** VM `devops`, `/srv/oscar/apps/nexus/` (comparte la VM con Forgejo y el CI Runner — ver [sizing real](./forgejo.md) tras la ampliación a 6 vCPU/12 GB)
**Sizing real:** sin overrides de JVM propios, usando los defaults de la imagen — medir antes de ajustar
**Red/puertos:** `8081` (UI/API, accesible también sin puerto vía `http://nexus.oscar.home` — ver "Reverse proxy" abajo), `8082` (registry Docker — puerto HTTP dedicado, Nexus lo requiere aparte de la UI, siempre por IP directa, nunca por el hostname)
**Persistencia:** `/srv/oscar/data/nexus` (blob stores, config, metadata — `chown 200:200`, uid con el que corre el proceso dentro del contenedor)

## Repositorios configurados

| Repositorio | Formato/tipo | Para qué |
|---|---|---|
| `npm-proxy` | npm, proxy | cache de `https://registry.npmjs.org` |
| `npm-hosted` | npm, hosted | paquetes propios |
| `npm-group` | npm, group (`npm-hosted`+`npm-proxy`) | endpoint único que usan los proyectos — `http://nexus.oscar.home:8081/repository/npm-group/` |
| `docker-hosted` | docker, hosted | destino real del `docker push` del [CI Runner](./ci-runner.md) — `192.168.0.151:8082` (puerto dedicado, no pasa por NPM) |

Todos creados vía la API REST (`POST /service/rest/v1/repositories/<formato>/<tipo>`), no a mano por la UI. Acceso anónimo deshabilitado durante el wizard de primer login — confirmado que **todos** los repos (incluido el proxy de npm, que en teoría solo cachea algo público) devuelven `401` sin credenciales.

**Hecho (por UI, sin API disponible):** cleanup policy para `docker-hosted` creada y asignada a mano — el endpoint REST de cleanup policies devuelve `404` en esta versión (probado `v1` y `beta`, no aparece en el swagger), así que no se pudo automatizar.

## Reverse proxy — Nginx Proxy Manager

`nexus.oscar.home` (sin puerto) tiene un Proxy Host real en [Nginx Proxy Manager](./nginx-proxy-manager.md) (`core`, `192.168.0.156`) → `forward_host: 192.168.0.151`, `forward_port: 8081` — mismo patrón que `git.oscar.home`, verificado devolviendo el HTML real de la UI de Nexus (`<title>Sonatype Nexus Repository</title>`) a través de NPM, no solo un `200` genérico.

El registry Docker (`8082`) **no** pasa por NPM — sigue siendo IP directa (`192.168.0.151:8082`) en todos lados donde se lo referencia (`insecure-registries` de Docker, `registries.yaml` de containerd en k3s, `image.repository` en los charts de Helm). Meterlo detrás de un proxy cambiaría el host:puerto que ven Docker/containerd, lo que rompería la config de `insecure-registries` existente en cada host sin ganar nada — el registry no necesita URL linda, lo consumen máquinas, no un navegador.

## Configuración para CI

Dos cosas que hicieron falta para que el [CI Runner](./ci-runner.md) pudiera pushear de verdad, ninguna obvia desde el wizard inicial:

- **`writePolicy: "allow"` en `docker-hosted`**, no el `"allow_once"` con el que se creó originalmente — con `allow_once`, re-pushear el mismo tag (`:latest` en cada build) falla con `cannot be updated as asset already exists and redeploy is not allowed`. `allow_once` tiene sentido para tags inmutables tipo versión semántica, no para el patrón normal de CI de sobreescribir `latest`.
- **Usuario dedicado `ci-forgejo`**, rol `ci-docker-push` acotado a `nx-repository-view-docker-docker-hosted-{add,edit,read,browse}` — ni el CI ni el `imagePullSecret` de k3s usan la cuenta `admin`. Mismo criterio que el resto de las credenciales acotadas del homelab (token de solo lectura de Argo CD, runner separado del admin de Forgejo, etc.).

Este mismo usuario se reutiliza para el `imagePullSecret` de k3s — Nexus exige auth tanto para `push` como para `pull` con el acceso anónimo deshabilitado, así que un Deployment sin `imagePullSecrets` falla con `pull access denied` aunque el CI haya pusheado bien.

## Rol dentro de O.S.C.A.R.

- proxy/cache de npm
- registry Docker privado
- repositorio Maven para laboratorios Java
- hostear artefactos internos
- practicar políticas de retención

## Ejemplo concreto

Laboratorio: configurar npm proxy, apuntar un proyecto Node al registry interno, borrar `node_modules` y medir el efecto del cache en una segunda instalación.

## Checklist de despliegue

- [x] hostname y ubicación decididos (`devops`, `nexus.oscar.home` para la UI, IP directa para el registry Docker);
- [x] imagen/versión fijada, evitando tags flotantes en servicios importantes (`3.96.1`);
- [x] puertos documentados (`8081` UI/API, `8082` Docker registry);
- [x] volumen/persistencia definida (`/srv/oscar/data/nexus`);
- [x] `.env.example` sin secretos en Git — no aplica, nada de esto vive en un repo Git, solo en la VM;
- [x] credenciales reales fuera de Git (admin real creado, en Vaultwarden);
- [ ] backup definido antes de cargar datos importantes — pendiente, hoy no hay artefactos reales cargados todavía;
- [x] healthcheck o monitor de disponibilidad — "Nexus (devops)" en Uptime Kuma, más `beszel-agent` para CPU/RAM/disco del host;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado;
- [x] **cleanup policy del repo Docker** — creada y asignada por UI (bloqueada por API, ver arriba).

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
