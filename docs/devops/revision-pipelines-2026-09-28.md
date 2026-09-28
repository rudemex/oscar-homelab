---
title: Revisión de pipelines — 2026-09-28
---

# Revisión de pipelines y congelamiento del kiosco

## Hallazgos

Forgejo 16.0.4 y runner 13.1.0 estaban activos. Los últimos pipelines consumidores de `ci-demo`, `led-controller` y `nestjs-api` habían terminado correctamente, pero los tres ensambladores de `ci-shared` fallaban en la validación del commit `0e859db`: `workflow_call only supports keys inputs and outputs, but key secrets was found`.

La separación estaba iniciada, pero quedaban instalación y pruebas duplicadas, referencias internas mezclando versiones, shell extenso dentro de YAML y smoke tests con nombre de contenedor global `smoke`.

La referencia utilizada fue `/Users/maximilianodelgado/Projects/Arquitectura/pipelines/npm`: steps CI/CD independientes, plantilla general y plantillas específicas de templates y apps. Se adaptó el diseño a Forgejo sin copiar sintaxis GitLab ni agregar integraciones ajenas a O.S.C.A.R.

## Estructura v2

[ci-shared v2.0.0](http://git.oscar.home/mdelgado/ci-shared/releases/tag/v2.0.0) está publicada, con [PR de la estructura integrado](http://git.oscar.home/mdelgado/ci-shared/pulls/1).

| Componente | Responsabilidad |
| --- | --- |
| common/ci y common/cd | Steps independientes: Node, Docker, smoke, publicación y GitOps |
| scripts/ci y scripts/cd | Implementación shell verificable fuera del runner |
| template-base.yml | Plantilla general: instalación, lint, tests y build configurables |
| template-be.yml | Templates: consume la base sin publicar ni desplegar |
| apps-be.yml | Apps: base común, Docker, smoke, publicación y GitOps |
| Repos consumidores | Comandos, parámetros y pruebas específicas; sin copiar infraestructura |

Los workflows viven en `.forgejo/workflows/`, ubicación obligatoria en Forgejo. El mirror `nestjs-starter` conserva su condición de solo lectura, sincronización y configuración originales. La cadena de templates se prueba desde el propio pipeline de `ci-shared`; hay ejemplos para futuros templates editables.

v2 cambia contratos: las apps pasan de `template-be` a `apps-be`, y los steps de `actions/` a `common/`. Los tags v1 siguen intactos. `VERSION` y `scripts/version.mjs` mantienen coherentes las referencias internas; cada consumidor adopta explícitamente un tag estable.

## Validación

- Ocho pruebas de scripts: npm/Yarn, propagación de fallos, credenciales temporales de Docker, validación de rutas, build sin alterar `latest` y GitOps real contra un repositorio temporal, incluida idempotencia.
- YAML parseado y sintaxis shell verificada.
- [Cadena de templates candidata](http://git.oscar.home/mdelgado/ci-shared/actions/runs/82) y [versión estable](http://git.oscar.home/mdelgado/ci-shared/actions/runs/84): correctas.
- Candidatas reales de aplicaciones: [ci-demo](http://git.oscar.home/mdelgado/ci-demo/actions/runs/28), [LED](http://git.oscar.home/mdelgado/led-controller/actions/runs/27), [NestJS](http://git.oscar.home/mdelgado/nestjs-api/actions/runs/9), correctas. Se verificaron jobs hijos, no solo el estado del workflow padre.
- PRs integrados de adopción estable: [ci-demo](http://git.oscar.home/mdelgado/ci-demo/pulls/1), [LED](http://git.oscar.home/mdelgado/led-controller/pulls/1), [NestJS](http://git.oscar.home/mdelgado/nestjs-api/pulls/1).

Ejecuciones de `main` tras integrar: [ci-shared #85](http://git.oscar.home/mdelgado/ci-shared/actions/runs/85), [ci-demo #30](http://git.oscar.home/mdelgado/ci-demo/actions/runs/30), [LED #29](http://git.oscar.home/mdelgado/led-controller/actions/runs/29) y [NestJS #11](http://git.oscar.home/mdelgado/nestjs-api/actions/runs/11). Los enlaces conservan los logs y el resultado de cada etapa.

Los PRs y ejecuciones manuales construyen y prueban sin publicar ni desplegar. En main se conserva la política previa: publicación y GitOps para ci-demo/NestJS; LED publica manteniendo `DEPLOY=false`, con verify/rollback específicos disponibles.

Los smoke tests usan un contenedor único por ejecución y limpieza al fallar. Un build de validación no modifica el alias local `latest`. La configuración temporal de Docker se elimina tras publicar.

## Pantalla congelada

El Dell y Homepage respondían; el problema coincidía con errores repetidos del compositor Cage: `HDMI-A-1: Atomic commit failed: Device or resource busy`. Reiniciar el kiosco sin ajustar DRM no bastó: el error regresó en 21 segundos.

A las 09:07:49 se reinició solo el kiosco con este drop-in persistente:

```ini
# /etc/systemd/system/kiosk.service.d/20-drm-compat.conf
[Service]
Environment=WLR_DRM_NO_ATOMIC=1
```

Las comprobaciones posteriores mostraron el servicio activo sin nuevos errores atomic/pageflip ni reinicios durante 15 minutos. No hubo evidencia de OOM ni caída global del host. **El usuario confirmó que la pantalla funciona.** La corrección quedó incorporada al instalador y documentada en [kiosk PR #1](http://git.oscar.home/mdelgado/kiosk/pulls/1), integrado en main.

Los procesos gráficos se consultan con `journalctl -b _UID=1000`: PAM los mueve a la sesión del usuario y `journalctl -u kiosk` no contiene todo. El respaldo previo quedó en `/tmp/kiosk-incidente-20260928.log` del Dell.

Para revertir este ajuste concreto, retirar el drop-in `20-drm-compat.conf`, ejecutar `systemctl daemon-reload` y reiniciar `kiosk`. No requiere reiniciar el host.
