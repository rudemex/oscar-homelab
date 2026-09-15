---
title: CI Runner
sidebar_position: 6
---

# CI Runner

**Estado:** Actual — `forgejo-runner` v13.1.0 corriendo en `devops01`, **validado con un pipeline real de punta a punta**: checkout → setup Node → install → lint → test → build de imagen Docker → push a Nexus, `status: success`, imagen confirmada en el registry (repo `ci-demo`, queda como referencia permanente — ver abajo)
**Dónde corre:** VM `devops01`, `/srv/oscar/apps/forgejo-runner/`
**Sizing real:** comparte la VM con Forgejo (6 vCPU / 12 GB totales tras la ampliación — ver [Forgejo / Git local](./forgejo.md))
**Red/puertos:** `network_mode: host`, sale por HTTP a la **IP LAN de la VM** (`192.168.0.151:3000`, no `127.0.0.1` — ver "Gotcha: red del contenedor del job" abajo); no requiere panel público
**Persistencia:** `/srv/oscar/apps/forgejo-runner/data` — credencial de registro (`.runner`) y `config.yaml` (`docker_host: automount`, ver abajo)

[ADR-010](../arquitectura/decisiones-arquitectonicas.md#adr-010--forgejo-con-forgejo-actions-como-plataforma-git-local) cerró la decisión: **Forgejo Actions** (sintaxis compatible con GitHub Actions) es el motor de CI, corriendo sobre la instancia de Forgejo — no se suma un producto de CI separado. Alternativas descartadas en el mismo ADR: GitLab Runner y Woodpecker CI/Drone.

## Instalación

Requiere Actions habilitado en Forgejo (`FORGEJO__actions__ENABLED: "true"` en el `compose.yaml` de Forgejo — ver [Forgejo / Git local](./forgejo.md)) y un token de registro:

```bash
docker exec -u 1000 forgejo forgejo actions generate-runner-token
```

`.env`:

```dotenv
RUNNER_VERSION=13.1.0
FORGEJO_INSTANCE_URL=http://192.168.0.151:3000
RUNNER_TOKEN=<token generado arriba>
RUNNER_NAME=devops01-runner
```

`data/config.yaml` (generado con `forgejo-runner generate-config`, un solo campo cambiado):

```yaml
container:
  # "automount" monta el socket Docker del host dentro del contenedor del
  # job automáticamente - sin esto, "docker: command not found" ni siquiera
  # llega a ser el error, porque no hay socket para hablarle.
  docker_host: "automount"
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
        forgejo-runner daemon --config /data/config.yaml
```

El `command` registra solo la primera vez (`if [ ! -f /data/.runner ]`) — reinicios posteriores del contenedor saltan directo a `daemon` sin volver a registrarse. Label `docker:docker://node:20-bookworm` significa que los jobs corren en contenedores Docker efímeros (imagen `node:20-bookworm` como base), no directo sobre el host — mismo motivo por el que el socket Docker está montado. Cambiar `FORGEJO_INSTANCE_URL` o `docker_host` requiere borrar `data/.runner` y dejar que se re-registre — la URL de instancia queda cacheada ahí, no se relee del `.env` en cada arranque.

**Validado tres veces, cada una más completa:**
- Smoke test: repo `ci-smoke-test` (borrado después), workflow de un solo step (`echo`), `running` → `success` en ~20s — confirmó el registro básico.
- **Pipeline real:** repo [`ci-demo`](http://git.oscar.home/mdelgado/ci-demo) (dejado como referencia permanente) — checkout, `setup-node`, `npm install`, lint, test, `docker build`, login e imagen pusheada a Nexus.
- **Loop GitOps completo:** el mismo `ci-demo` ahora además actualiza el tag de imagen en `oscar-gitops` y Argo CD lo despliega solo (`syncPolicy.automated`) — confirmado con `kubectl exec` contra el pod real mostrando el código del último commit, sin ningún `kubectl apply` manual de por medio. Ver [pipeline de referencia](../devops/pipeline-ejemplo.md) para el YAML completo y [Sonatype Nexus Repository](./nexus.md#configuración-para-ci) para la parte de Nexus.

Diez problemas reales encontrados en total entre las tres vueltas de validación — ver "Gotchas reales" abajo.

## Gotchas reales (encontrados con el pipeline completo, no obvios de antemano)

Cada uno costó un ciclo completo de push→esperar→fallar→diagnosticar. Quedan acá para no repetir el proceso:

1. **`${{ gitea.sha }}` no es una variable válida** → `Unknown Variable Access gitea` en la validación del schema, falla instantáneo sin llegar al runner. Forgejo Actions valida contra el contexto de **GitHub** Actions (`github.sha`, `github.actor`, etc.), no uno propio de Gitea — coherente con que la promesa del producto es compatibilidad con sintaxis de GitHub Actions.
2. **ESLint sin `globals` de Node declarados** → `'process' is not defined no-undef` — el flat config (`eslint.config.js`) no asume ningún entorno por default, hay que declarar `process`/`console` a mano en `languageOptions.globals`.
3. **`node --test` no setea `NODE_ENV=test` solo** — esa es convención de Jest/Mocha, no del test runner nativo de Node. Un `index.js` que arrancaba un servidor HTTP salvo que `NODE_ENV === "test"` seguía arrancándolo igual durante los tests (el `import` desde el test dispara el side-effect), dejando un socket abierto que nunca deja terminar al proceso — el job quedó colgado 5 minutos hasta matarlo a mano. Fix real: separar el módulo testeable (sin side effects) del entrypoint que hace `.listen()`, no tratar de detectar "soy el módulo principal" con una condición frágil.
4. **La IP de instancia del runner no puede ser `127.0.0.1`** → `Failed to connect to 127.0.0.1 port 3000` al hacer checkout. El runner corre en `network_mode: host` (ve el `127.0.0.1` de `devops01` real), pero el **contenedor del job es otro contenedor separado**, con su propio loopback — para él, `127.0.0.1` es él mismo, no el host. Hace falta la IP LAN real (`192.168.0.151`) en `FORGEJO_INSTANCE_URL`.
5. **Docker asume HTTPS por defecto en cualquier registry** → `http: server gave HTTP response to HTTPS client` al pushear a Nexus (`8082`, HTTP plano, sin TLS). Hace falta `insecure-registries` en `/etc/docker/daemon.json` del **host** (`devops01`, no del contenedor del job — el `docker` del job habla con el daemon del host vía el socket montado) + `systemctl restart docker`, lo que reinicia brevemente todos los contenedores de esa VM.
6. **Nexus rechaza re-pushear un tag que ya existe** → `cannot be updated as asset already exists and redeploy is not allowed`. El repo `docker-hosted` se creó con `writePolicy: "allow_once"` (cada componente se escribe una sola vez) — funciona para tags inmutables (`:${{ github.sha }}`), pero rompe el patrón normal de sobreescribir `:latest` en cada build. Fix: `writePolicy: "allow"` en la config del repo.
7. **k3s/containerd tiene el mismo problema de HTTPS que Docker, pero en su propia config** — un pod con `ImagePullBackOff` contra Nexus aunque el `docker push` ya funcionaba. `/etc/rancher/k3s/registries.yaml` en `k3s01` necesita su propio bloque `mirrors`/`configs` con `insecure_skip_verify: true`, y `systemctl restart k3s` para que containerd lo relea — el fix de Docker en `devops01` no le sirve de nada al nodo de k3s, son daemons de contenedores completamente distintos.
8. **Nexus exige auth también para el `pull`, no solo el `push`** — con el acceso anónimo deshabilitado (a propósito, ver [Nexus](./nexus.md)), un pod sin `imagePullSecrets` da `pull access denied... no basic auth credentials` aunque la imagen exista y el `docker login` del CI haya sido exitoso. Hace falta un `Secret` tipo `docker-registry` en el namespace destino, referenciado desde `spec.template.spec.imagePullSecrets` en el Deployment.
9. **El contenedor del job no resuelve hostnames `*.oscar.home`** → `Could not resolve host: git.oscar.home` al clonar `oscar-gitops` desde el propio pipeline. Docker no le pasa el DNS del host a los contenedores por default (menos todavía si el host usa `systemd-resolved`, que apunta a `127.0.0.53`, un stub que solo sirve desde el host mismo) — y `devops01` tampoco tenía a AdGuard como su propio DNS. Fix real, no un parche puntual: `"dns": ["192.168.0.93", "1.1.1.1"]` en `/etc/docker/daemon.json` (junto al `insecure-registries` ya existente) + `systemctl restart docker` — a partir de ahí, **cualquier** contenedor nuevo en `devops01` resuelve `*.oscar.home` solo, no hace falta más `docker run --dns=...` a mano. Ojo: esto es el DNS de **Docker**, no el del sistema operativo de `devops01` — el runner en sí (`network_mode: host`) sigue sin resolver esos hostnames, porque usa el resolver del SO directo, no el de Docker; por eso `FORGEJO_INSTANCE_URL` se queda con la IP.
10. **`git clone` de un repo privado sin credenciales cuelga con un error engañoso** → `fatal: could not read Username for '...': No such device or address`. No es un problema de red ni de DNS (ese ya se había resuelto) — es que el `clone` intenta pedir usuario/contraseña interactivo, que no existe en un shell no interactivo de CI. El header de auth (`http.extraHeader`) hay que ponerlo en **el `clone` también**, no solo en el `push` — es fácil poner el header solo donde "se escribe" y olvidarse de que leer un repo privado también necesita autenticación.

## Rol dentro de O.S.C.A.R.

- compilar proyectos Node
- crear imágenes OCI
- ejecutar tests
- desplegar a k3s o EasyPanel con credenciales acotadas

## Ejemplo concreto

Pipeline real y funcionando en [`ci-demo`](http://git.oscar.home/mdelgado/ci-demo), loop completo de punta a punta: lint → test → build image → push a Nexus → actualizar tag en `oscar-gitops` → Argo CD sincroniza y despliega solo. Ver [pipeline de referencia](../devops/pipeline-ejemplo.md) para el workflow completo.

## Checklist de despliegue

- [x] plataforma Git/CI decidida (ADR-010: Forgejo Actions);
- [x] hostname y ubicación decididos (`devops01`, mismo host que Forgejo);
- [x] imagen/versión fijada, evitando tags flotantes en servicios importantes (`13.1.0`);
- [x] puertos documentados (`network_mode: host`, sin puertos propios publicados);
- [x] volumen/persistencia definida (`/srv/oscar/apps/forgejo-runner/data`);
- [x] `.env.example` sin secretos en Git — no aplica, nada de esto vive en un repo Git, solo en la VM;
- [ ] credenciales reales fuera de Git — el `RUNNER_TOKEN` vive en `.env` de la VM, no en Git, pero falta confirmarlo en Vaultwarden;
- [ ] backup definido antes de cargar datos importantes;
- [x]/[ ] healthcheck o monitor de disponibilidad — parcial: `beszel-agent` ya corre en `devops01` y cubre CPU/RAM/disco del host (tarjeta "Beszel devops01" en Homepage), pero no hay un chequeo específico del proceso del runner ni de la tasa de éxito de los jobs — falta sumarlo a Uptime Kuma si se quiere ese nivel de detalle;
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
