# Hermes para OSCAR

Chart activo para `apps/hermes` en `http://git.oscar.home/mdelgado/gitops.git`, namespace `oscar-ai`.
Argo CD despliega la raíz manualmente y las aplicaciones hijas de forma automática.

## Activación

1. Proveedor confirmado: Anthropic API, cuenta personal, piloto de US$10. El catálogo autenticado
   confirmó `claude-sonnet-5-5`; `ANTHROPIC_API_KEY` recibe el secreto `MODEL_API_KEY`.
2. Proyecto dedicado **Hermes** en Infisical (`3ff70b49-4ae2-4cb7-9f0e-2465925f8d6a`), ambiente `prod`, raíz `/`. Contiene:
   `MODEL_API_KEY`, `API_SERVER_KEY`, `WEBUI_SECRET_KEY`, `WEBUI_ADMIN_PASSWORD`, credenciales del
   bot Discord, token/CA del operador Proxmox, token de Home Assistant y token de Forgejo.
   Los tres secretos internos tienen valores aleatorios propios; no reutilizarlos en otros servicios.
3. La identidad de proyecto `hermes-runtime` tiene rol **Viewer** solo en el proyecto Hermes;
   el secreto `hermes-infisical-auth` de `oscar-ai` contiene su credencial Universal Auth fuera de Git.
   Se validó que la identidad puede leer los cuatro secretos del proyecto dedicado. No agregar otros
   servicios ni secretos a ese proyecto sin revisar el alcance del rol Viewer.
4. Confirmar recursos de `k3s01`: requests combinados 1 GiB RAM, límites combinados 3 GiB;
   no hay garantía de capacidad solo porque Kubernetes permita el scheduling. Los PVC son de 5 GiB cada uno.
   No modificar RAM ni reiniciar hosts automáticamente al activar este chart.
5. Copiar el directorio a `apps/hermes` en un checkout actualizado de GitOps,
   revisar el diff y publicar mediante el flujo habitual del repo. La Application tiene sync manual.
6. Sincronizar la Application raíz para registrar `hermes`, después sincronizar `hermes`.
7. WebUI queda accesible en `http://ai.oscar.home` por el Ingress de Traefik en la LAN.
   También se puede usar `kubectl -n oscar-ai port-forward svc/hermes-webui 8080:8080`.
   Usuario `mdelgado@tresdoce.com.ar`, password administrado en Infisical. Registro público deshabilitado.
8. Validar login, inferencia y herramientas desde WebUI antes de compartir el acceso.

Open WebUI recibe solo su token para Hermes y sus claves de sesión/admin, nunca la key del proveedor.
La configuración de conexiones de WebUI se administra mediante entorno (`ENABLE_PERSISTENT_CONFIG=false`).
Rotar credenciales requiere reiniciar ambos deployments tras sincronizar secrets.

## Discord (chat entrante)

El chart integra el gateway nativo de Hermes con `#hermes-agent` o DMs. El gateway está habilitado con
`DISCORD_BOT_TOKEN` y `DISCORD_ALLOWED_USERS` en Infisical, en la raíz `/` del proyecto dedicado a
Hermes. La lista debe contener solo IDs numéricos de usuarios autorizados. El bot exige
mención en servidores, no responde a toda la sala, no crea threads y no puede mencionar `@everyone`
ni roles. No habilitar `DISCORD_ALLOW_ALL_USERS`.

Usar una aplicación/bot dedicado **Hermes** (no el bot de bootstrap del servidor): habilitar
Message Content Intent, instalarlo con `bot` + `applications.commands`, y asignarle permisos
mínimos para ver/leer historial/enviar mensajes en `#hermes-agent` (más embeds/adjuntos si se usan).
No otorgar Administrator ni Manage Channels.
Para crear el bot y habilitar los intents, seguir [la guía oficial de Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord/).

## Comprobaciones reproducibles

```sh
python3 -m unittest discover -s infrastructure/hermes/tests -v
helm lint infrastructure/hermes --set enabled=true --set model.provider=openrouter \
  --set model.name=validation-only --set secrets.providerKeyEnv=OPENROUTER_API_KEY
helm template hermes infrastructure/hermes -n oscar-ai --set enabled=true \
  --set model.provider=openrouter --set model.name=validation-only \
  --set secrets.providerKeyEnv=OPENROUTER_API_KEY > /tmp/hermes-check.yaml
kubectl apply --dry-run=server -n oscar-ai -f /tmp/hermes-check.yaml
```

`validation-only` es un marcador de prueba, no un modelo para desplegar. Las pruebas de seguridad
cubren datos ausentes, fallos parciales, inyección de PromQL, cobertura desconocida, redirects y límites de resultados.
`tests/smoke_image.py` se ejecuta dentro de la imagen fijada, con los archivos del ConfigMap montados
en `/etc/oscar` y `/opt/data` temporal escribible; usa credenciales ficticias y nunca solicita inferencia.
Comprueba las herramientas MCP declaradas, consulta Prometheus/SearXNG y prueba `/health` y `/v1/models`.
`tests/smoke_webui.py` arranca WebUI con cuenta efímera, comprueba health y login, y exige rechazo
del signup. Ejecutarlo en una CPU X86_V2 o superior (validado en `k3s01`, falla en `devops` actual).

Validación: 44 tests unitarios, `helm lint` y `helm template` + `kubectl apply --dry-run=client`
aprobados (2026-10-08). **n8n agregado y confirmado real**: `oscar_n8n_list_workflows` y
`oscar_n8n_set_workflow_active` vía `X-N8N-API-KEY`, egress LAN acotado a `192.168.0.153:5678`. El
primer intento de agregarlo quedó bloqueado por el entorno de desarrollo varias veces sin dar motivo
(incluso partido en piezas chicas); en un segundo intento, pedido explícito del usuario, se agregó
sin problema. Probado contra la Hermes real: listó el workflow real del broker de Discord
(`Vs66rgJi1QtRJ6PJ`, activo) y activó ese mismo workflow sin disrupción (ya estaba activo, operación
idempotente) — confirmado independientemente que sigue sano después (41 nodos, activo). Usa la misma
API key que el resto de la sesión usó para construir el broker — n8n self-hosted de un solo usuario
no soporta múltiples API keys separadas, mismo caso que la cuenta admin de AdGuard.

**Kuma mutable (pausar/reanudar/crear monitor): se mantiene excluido a propósito**, decisión
confirmada con el usuario — agregar `uptime-kuma-api` (la única forma real de mutar Kuma, ya que no
tiene API REST estable) rompería el diseño stdlib-only de este archivo, y esa librería ya mostró ser
inestable con esta versión de Kuma en otra parte de esta sesión (falló al crear un monitor de
prueba). Solo queda `oscar_kuma_get_status_page`, de solo lectura.

### Dos warnings de arranque investigados (2026-10-08)

Hermes imprime dos warnings en cada arranque:

1. **"API server is network-accessible (0.0.0.0) AND the terminal backend is 'local'
   (unsandboxed)..."** — suena grave, pero es un warning genérico que Hermes imprime siempre que
   `terminal.backend` queda en su default, sin tener en cuenta `platform_toolsets`. **Confirmado con
   una prueba real**: se le pidió a Hermes que ejecute `whoami` por su herramienta de terminal, y
   respondió correctamente que no tiene ninguna disponible — `platform_toolsets: [oscar]` (en
   `api_server`, `cli` y `discord`) sí bloquea el toolset `terminal` built-in (`terminal`, `process`,
   `read_file`, `patch`, `execute_code`). "No hay terminal" se sostiene bajo prueba, no es solo una
   afirmación de diseño.

2. **"this process is PID 1 with no init above it... Use the image's default ENTRYPOINT
   (docker/entrypoint-dispatch.sh)..."** — **se intentó corregir y rompió el pod en producción.** El
   comando sobreescribe el `ENTRYPOINT` con `/bin/sh -ec` + `exec` para poder copiar `config.yaml`/
   `SOUL.md` a `/opt/data` antes de arrancar (necesario porque `readOnlyRootFilesystem: true` deja
   `/etc/oscar` de solo lectura). Se probó anteponer `exec tini -g --` (tini está en la imagen, en
   `/usr/bin/tini`) para que reapee zombies — pero el `tini` de esta imagen en realidad dispara
   `s6-overlay`, que exige arrancar como root para bajar privilegios con sus propios mecanismos. El
   pod ya fuerza `runAsUser: 10000` a nivel de Kubernetes (no-root, una propiedad de seguridad más
   importante que este warning), así que s6 fallaba con `fatal: /run belongs to uid 0 ... lacking
   the privileges to fix it` y quedaba en `CrashLoopBackOff`. **Revertido de inmediato** tras
   confirmarlo en los logs; el pod volvió a `Healthy` en menos de un minuto. El warning queda como
   limitación conocida y aceptada: el remedio que sugiere Hermes no es compatible con correr como
   non-root sin además renunciar a que s6-overlay haga su propio arranque-como-root-y-bajar-privilegios,
   algo que no vale la pena para resolver una acumulación lenta de procesos zombie (impacto real bajo:
   solo pasaría si un subproceso del MCP de `oscar_tools.py` queda huérfano, y el pod se reinicia
   periódicamente igual por los despliegues de esta misma sesión).

**Ronda de pruebas reales contra producción (2026-10-08), después de sincronizar: se probaron los
~24 tools uno por uno contra la instancia real de Hermes (vía su API OpenAI-compatible,
`kubectl port-forward` + `API_SERVER_KEY`), no solo con mocks.** Se encontraron y corrigieron 3 bugs
reales que ningún test unitario con mocks podía haber detectado, porque los tres son desacuerdos
entre el código y el comportamiento real de los sistemas externos:

1. **AdGuard: Basic Auth sí funciona** (confirmado con `curl -u`), pero el primer intento real desde
   Hermes dio 401 — causa distinta: se reinició el pod justo después de cargar las credenciales en
   Infisical, antes de que el operador de Infisical sincronizara, y el Secret tenía el placeholder
   literal `<no value>` (texto que Go renderiza cuando falta un campo en el template) en vez del
   valor real. Solución: esperar el resync (o forzarlo) antes de reiniciar el pod que consume el
   Secret.
2. **Docker: `oscar_docker_get_logs` daba 404.** El operador HTTPS que corre en los 5 hosts se
   despliega con un playbook de Ansible manual, no con Argo CD — cualquier cambio a
   `files/docker_operator.py` (como agregar `down`/`/v1/logs` en esta misma ronda) necesita volver a
   correr `ansible-playbook hermes-docker-operator.yml` para llegar a los hosts reales. El chart
   sincronizado en Kubernetes y el operador systemd en cada host son dos despliegues independientes.
3. **Forgejo: `oscar_forgejo_write_file` siempre usaba `PUT`, y esta instancia de Forgejo devuelve
   `422 "[SHA]: Required"` con `PUT` sobre un archivo que no existe** (confirmado reproduciendo el
   llamado a mano). Esta instancia distingue crear (`POST`, sin `sha`) de actualizar (`PUT`, con
   `sha`) en el mismo endpoint — corregido para elegir el método según si se pasa `sha`.

Las herramientas de solo lectura nuevas (`oscar_get_rollout_history`,
`oscar_forgejo_list_workflow_runs`, `oscar_docker_get_logs` ya corregido) y el ciclo completo de
Forgejo (rama → commit → PR → merge squash → borrar rama, de punta a punta en un repo de prueba) se
confirmaron reales, no simulados. `oscar_rollback_workload` se probó sobre el propio Deployment de
Hermes (mismo chart/imagen, solo cambia el ReplicaSet) — funcionó, aunque cortó la conexión HTTP a
mitad de respuesta porque Hermes se reinició a sí mismo al aplicar el cambio. `oscar_delete_vm`/
`oscar_resize_vm` se probaron solo en su camino de rechazo (sin `confirm=True`, sobre un guest
corriendo) para no tocar ninguna VM real; las salvaguardas funcionaron.

## Operación que habilita este chart

El MCP conserva upstreams fijos y agrega: inventario/acciones de energía de VMs y contenedores LXC
Proxmox, clonación de una VM detenida desde la plantilla 9000, inventario/reinicio/escalado de
Deployments y StatefulSets, lectura y sincronización de Applications de Argo CD (sin prune), control
del LED OSCAR, llamadas genéricas a servicios de Home Assistant y operaciones Git sobre repositorios
OSCAR allowlisted. Las herramientas de Forgejo leen archivos y PRs; crean ramas `hermes/*`, commits
en esas ramas y pull requests revisables. No escriben directo en `main` ni fusionan PRs.
Home Assistant usa un token dedicado
de Infisical y permite descubrir entidades, consultar su estado y llamar cualquier servicio (por ejemplo,
`light.turn_on`/`light.turn_off`). `OSCAR_HOME_ASSISTANT_TOKEN` está guardado en `Hermes/prod` en Infisical
y el chart ya activa la integración. El LED usa el Service interno del clúster.
No hay terminal, URL arbitraria ni ejecución de shell. Kubernetes permite `get/list/patch/delete`
sobre Deployments y StatefulSets, `get/list` sobre ReplicaSets (para `oscar_get_rollout_history` y
`oscar_rollback_workload`, que restaura el `podTemplate` de una revisión previa), y `get/list/patch`
de Applications en el namespace `argocd`. El escalado está limitado a 0–10 réplicas y excluye
namespaces de sistema; borrar/escalar/revertir requieren el mismo denylist (`PROTECTED_NAMESPACES`
en `oscar_tools.py` — unificado en esta ronda: `oscar_restart_workload` protegía `infisical`, que no
es un namespace real, mientras `oscar_scale_workload` ya protegía correctamente
`infisical-operator-system`; ahora las dos funciones comparten la misma constante). El token Proxmox
`hermes-operator@pve!oscar` tiene permisos de administración de VMs y `local-lvm`; el token y la CA
pública ya están en Infisical y una consulta de inventario pasó validación TLS. La clonación deja la
VM detenida para revisar Cloud-Init, red, credenciales y disco antes de encenderla. `oscar_delete_vm`
y `oscar_resize_vm` exigen que el guest esté `stopped` (nunca sobre uno corriendo), y destruir requiere
`confirm=True` explícito.

`HERMES_FORGEJO_TOKEN` vive en Infisical y lo consume solo el MCP de Forgejo. La API reporta acceso
admin a los repositorios del usuario; el MCP limita los repos permitidos a los diez repos OSCAR
conocidos y deja `nestjs-starter` como solo lectura. Para reducir el impacto de una futura falla del
agente, conviene reemplazarlo por una cuenta de servicio con permisos mínimos por repositorio.
Además de proponer (rama `hermes/*` + PR), ahora puede completar el ciclo: `oscar_forgejo_merge_pull_request`
fusiona un PR ya revisado, `oscar_forgejo_delete_branch` borra la rama después, y
`oscar_forgejo_list_workflow_runs` lee el estado de los runs de Forgejo Actions (útil para confirmar
si un deploy que disparó su propio PR terminó bien). `oscar_forgejo_write_file` usa `POST` para
crear un archivo nuevo y `PUT` (con `sha`) para actualizar uno existente — esta instancia de Forgejo
rechaza `PUT` sin `sha` con `422` incluso sobre un archivo inexistente, a diferencia de lo que
sugiere la documentación genérica de la API. El ciclo completo (rama → commit → PR → merge squash →
borrar rama) se probó real, de punta a punta, contra un repo de prueba.

### AdGuard Home y Uptime Kuma

`adguard.enabled` agrega consulta de estado/estadísticas (`oscar_adguard_get_status`) y gestión de
DNS rewrites (`oscar_adguard_list_rewrites`/`add_rewrite`/`remove_rewrite`) contra
`http://192.168.0.213:3000` vía HTTP Basic Auth — **confirmado funcionando contra la instancia real**
(2026-10-08: `oscar_adguard_list_rewrites` devolvió los 20 rewrites reales configurados). No existe
un usuario restringido dedicado: AdGuard Home en esta versión (v0.107.79) no tiene soporte
multiusuario (`/control/users` da 404), así que `OSCAR_ADGUARD_USER`/`_PASSWORD` en Infisical son la
cuenta admin real — decisión del usuario, no un descuido. **Gotcha de despliegue:** si cargás estas
credenciales en Infisical y reiniciás el pod de Hermes enseguida, podés agarrar al Secret todavía sin
sincronizar y el pod arranca con el placeholder literal `<no value>` en vez del valor real — esperá
el resync (hasta 60 s) o confirmá el contenido del Secret (`kubectl get secret hermes-runtime -o
jsonpath=...`) antes de reiniciar.

`kuma.enabled` agrega `oscar_kuma_get_status_page(slug)`, de solo lectura, sin credenciales, contra
la página de estado pública de Uptime Kuma (`http://192.168.0.214:3001/api/status-page/<slug>`).
Pausar/reanudar/crear monitores no está implementado a propósito: Kuma no tiene una API REST estable
para mutaciones (solo un protocolo socket.io), y agregar esa dependencia rompería el diseño de este
archivo (solo librería estándar de Python, sin dependencias de terceros).

### Docker Compose

El operador HTTPS opcional `hermes_docker_operator` agrega inventario de contenedores/proyectos y
acciones `start`, `stop`, `restart`, `up` y `down` por servicio o proyecto, más lectura de logs
(`oscar_docker_get_logs`, hasta 1000 líneas, con un tope de 200 000 caracteres por respuesta). `down`
nunca pasa `-v`: no elimina volúmenes ni datos. No admite eliminación del proyecto en sí ni comandos
Docker arbitrarios. La allowlist de proyectos y rutas está declarada en `ansible/host_vars/`; el
proceso solo ejecuta `docker compose` sobre esos proyectos. Los destinos cubren `core`, `devops`,
`automation`, `monitor` y `network` — incluyen Infisical, Forgejo, cloudflared y n8n: ninguna
herramienta distingue "bajo riesgo" de "crítico" dentro de una misma allowlist, a propósito no
cambiado en esta ronda (ver `docs/ia/hermes.md` en `oscar-homelab`).

Para habilitarlo hacen falta cinco tokens aleatorios distintos de al menos 32 caracteres:
`OSCAR_DOCKER_OPERATOR_TOKEN_CORE`, `_DEVOPS`, `_AUTOMATION`, `_MONITOR` y `_NETWORK`, en Infisical,
ambiente `prod`, raíz del proyecto Hermes. Cada host acepta solo su propio token. Los certificados TLS por host se
generan fuera de Git en `/private/tmp/hermes-docker-operator-pki`; solo el certificado público de la CA
se versiona. El despliegue remoto usa el rol Ansible `hermes_docker_operator` con la variable token en
el entorno local y la contraseña de Ansible Vault para las Raspberry Pi. Después se cambia
`dockerOperator.enabled` a `true` y se sincroniza Hermes. El rol instala la unidad systemd de cada
host, el token con permisos `0640`, el certificado propio y la allowlist JSON.

El bootstrap crea y guarda los cinco tokens sin imprimirlos, y luego instala los operadores. Requiere
iniciar sesión en Infisical con una identidad con escritura en el proyecto Hermes y tener Ansible
instalado; pide interactivamente la contraseña de Ansible Vault para las Pi:

```sh
infisical login --interactive --domain http://infisical.oscar.home/api
python3 ansible/scripts/bootstrap-hermes-docker-operator.py
```

La herramienta queda deshabilitada por defecto hasta que exista el secreto en Infisical y los cinco
operadores estén instalados. Esto evita que el agente ofrezca acciones que todavía no pueden ejecutarse.
El grupo Docker equivale a acceso root en cada host; el API reduce esa autoridad a las cinco acciones
permitidas, pero un compromiso del proceso operador también comprometería el host. No usarlo para
editar Compose desde Hermes; esos cambios siguen entrando por Git y revisión.

**El operador systemd de cada host y el chart de Kubernetes son dos despliegues independientes.**
Argo CD sincroniza el ConfigMap/Deployment de Hermes automáticamente, pero `files/docker_operator.py`
solo llega a los 5 hosts reales corriendo el playbook de Ansible a mano (mismo comando que la
activación inicial, de nuevo). Si editás ese archivo y no volvés a correr el playbook, Hermes sigue
hablándole a la versión vieja del operador — confirmado en vivo (2026-10-08): agregar `down` y
`/v1/logs` al código no tuvo efecto real hasta redesplegar.

## Límites deliberados

- No hay terminal, filesystem ni ejecución arbitraria. Las escrituras se hacen mediante funciones API concretas.
- El porcentaje histórico excluye huecos: se informa cobertura desconocida. No es uptime de ventana completa.
- Las NetworkPolicies permiten HTTPS público al modelo, DNS y los endpoints LAN específicos de cada integración habilitada.
- Docker Compose tiene un operador listo, pero está pendiente de credencial/instalación. Todavía faltan
  APIs autenticadas para gestionar configuración de AdGuard DNS, Uptime Kuma, NPM y Cloudflare; no hay
  endpoint de administración configurado para router, NAS/UPS ni DVR. Argo CD sí puede inventariarse y
  sincronizarse sin pruning; Kubernetes opera Deployments/StatefulSets.
- Sin inferencia validada, monitoreo propio ni backup/restore todavía. Eso es necesario antes de producción.
- `local-path` fija el estado a un nodo y no permite expansión directa; no ofrece alta disponibilidad.
- Hermes puede copiar la key de entorno a su credential pool en el PVC: respaldar ese estado cifrado.

## Reversión

Detener ambos deployments conservando los PVC, o revertir la versión en GitOps después de validar
compatibilidad de los datos. No borrar namespace/PVC como procedimiento de rollback.
