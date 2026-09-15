---
title: CI Runner
sidebar_position: 6
---

# CI Runner

**Estado:** Actual — `forgejo-runner` v13.1.0 corriendo en `devops01`, **validado con un workflow real de punta a punta** (repo de prueba → push → job tomado por el runner → corrido en contenedor Docker efímero → `status: success`, repo de prueba borrado después)
**Dónde corre:** VM `devops01`, `/srv/oscar/apps/forgejo-runner/`
**Sizing real:** comparte la VM con Forgejo (6 vCPU / 12 GB totales tras la ampliación — ver [Forgejo / Git local](./forgejo.md))
**Red/puertos:** `network_mode: host`, sale por HTTP a `127.0.0.1:3000` (Forgejo en la misma VM); no requiere panel público
**Persistencia:** `/srv/oscar/apps/forgejo-runner/data` — credencial de registro (`.runner`) y config

[ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local) cerró la decisión: **Forgejo Actions** (sintaxis compatible con GitHub Actions) es el motor de CI, corriendo sobre la instancia de Forgejo — no se suma un producto de CI separado. Alternativas descartadas en el mismo ADR: GitLab Runner y Woodpecker CI/Drone.

## Instalación

Requiere Actions habilitado en Forgejo (`FORGEJO__actions__ENABLED: "true"` en el `compose.yaml` de Forgejo — ver [Forgejo / Git local](./forgejo.md)) y un token de registro:

```bash
docker exec -u 1000 forgejo forgejo actions generate-runner-token
```

`.env`:

```dotenv
RUNNER_VERSION=13.1.0
FORGEJO_INSTANCE_URL=http://127.0.0.1:3000
RUNNER_TOKEN=<token generado arriba>
RUNNER_NAME=devops01-runner
```

`compose.yaml`:

```yaml
services:
  runner:
    image: code.forgejo.org/forgejo/runner:${RUNNER_VERSION}
    container_name: forgejo-runner
    restart: unless-stopped
    network_mode: host
    # GID del grupo "docker" en el host - sin esto, "permission denied"
    # contra /var/run/docker.sock aunque esté montado (ver Troubleshooting).
    group_add:
      - "988"
    volumes:
      - ./data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    entrypoint: sh
    command:
      - -c
      - |
        if [ ! -f /data/.runner ]; then
          forgejo-runner register --no-interactive \
            --instance "${FORGEJO_INSTANCE_URL}" \
            --token "${RUNNER_TOKEN}" \
            --name "${RUNNER_NAME}" \
            --labels docker:docker://node:20-bookworm
        fi
        forgejo-runner daemon
```

El `command` registra solo la primera vez (`if [ ! -f /data/.runner ]`) — reinicios posteriores del contenedor saltan directo a `daemon` sin volver a registrarse. Label `docker:docker://node:20-bookworm` significa que los jobs corren en contenedores Docker efímeros (imagen `node:20-bookworm` como base), no directo sobre el host — mismo motivo por el que el socket Docker está montado.

**Validado:** repo `ci-smoke-test` creado vía API, workflow con un solo step (`echo`) en `.forgejo/workflows/test.yml`, push disparó el run automáticamente, pasó por `running` → `success` en ~20 segundos. Repo de prueba borrado después — mismo patrón que "Ideas de laboratorio" abajo.

## Rol dentro de O.S.C.A.R.

- compilar proyectos Node
- crear imágenes OCI
- ejecutar tests
- desplegar a k3s o EasyPanel con credenciales acotadas

## Ejemplo concreto

Pipeline: lint → test → build image → push Nexus → actualizar tag GitOps → Argo CD despliega. Ver [pipeline de referencia](../devops/pipeline-ejemplo.md) para el detalle de cada etapa.

## Checklist de despliegue

- [x] plataforma Git/CI decidida (ADR-010: Forgejo Actions);
- [x] hostname y ubicación decididos (`devops01`, mismo host que Forgejo);
- [x] imagen/versión fijada, evitando tags flotantes en servicios importantes (`13.1.0`);
- [x] puertos documentados (`network_mode: host`, sin puertos propios publicados);
- [x] volumen/persistencia definida (`/srv/oscar/apps/forgejo-runner/data`);
- [x] `.env.example` sin secretos en Git — no aplica, nada de esto vive en un repo Git, solo en la VM;
- [ ] credenciales reales fuera de Git — el `RUNNER_TOKEN` vive en `.env` de la VM, no en Git, pero falta confirmarlo en Vaultwarden;
- [ ] backup definido antes de cargar datos importantes;
- [ ] healthcheck o monitor de disponibilidad — falta sumarlo a Uptime Kuma/Beszel;
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
