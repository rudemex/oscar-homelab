# Hermes para OSCAR

Chart candidato para `apps/hermes` en `http://git.oscar.home/apps/gitops.git`.
Estado: Hermes/WebUI/Discord están desplegados en `oscar-ai`; la fuente GitOps activa aún no contiene
las herramientas operadoras de este candidato. `discord.enabled` y `proxmox.enabled` están listos;
las credenciales viven en Infisical y no en estos archivos.

## Activación

1. Proveedor confirmado: Anthropic API, cuenta personal, piloto de US$10. El catálogo autenticado
   confirmó `claude-sonnet-5-5`; `ANTHROPIC_API_KEY` recibe el secreto `MODEL_API_KEY`.
2. Proyecto dedicado **Hermes** en Infisical (`3ff70b49-4ae2-4cb7-9f0e-2465925f8d6a`), ambiente `prod`, raíz `/`. Contiene:
   `MODEL_API_KEY`, `API_SERVER_KEY`, `WEBUI_SECRET_KEY`, `WEBUI_ADMIN_PASSWORD`, credenciales del
   bot Discord y token/CA del operador Proxmox.
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
No otorgar Administrator ni Manage Channels. En el despliegue actual Hermes sigue con herramientas
de consulta; las acciones descritas abajo se habilitan al sincronizar este chart.
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

Validación realizada el 2026-10-05: siete tests, Helm, dry-run contra k3s, ambos arranques reales
y build de documentación aprobados. Sin llamada al modelo ni validación end-to-end todavía.
Las pruebas aisladas no prueban la aplicación efectiva de NetworkPolicies del despliegue final.

## Operación habilitada en el candidato

El MCP conserva upstreams fijos y agrega: inventario/acciones de energía de VMs Proxmox, clonación
de una VM detenida desde la plantilla 9000, reinicio de Deployments/StatefulSets, control del LED
OSCAR y llamadas genéricas a servicios de Home Assistant. Home Assistant usa un token dedicado
de Infisical y permite descubrir entidades, consultar su estado y llamar cualquier servicio (por ejemplo,
`light.turn_on`/`light.turn_off`). `OSCAR_HOME_ASSISTANT_TOKEN` está guardado en `Hermes/prod` en Infisical
y el chart ya activa la integración. El LED usa el Service interno del clúster.
No hay terminal, URL arbitraria ni ejecución de shell. El rol Kubernetes permite `get/list/patch`
solo sobre Deployments y StatefulSets. El token Proxmox `hermes-operator@pve!oscar` tiene permisos
de administración de VMs y `local-lvm`; el token y la CA pública ya están en Infisical y una consulta
de inventario pasó validación TLS. La clonación deja la VM detenida para revisar Cloud-Init, red,
credenciales y disco antes de encenderla.

Este cambio es un candidato local: hasta sincronizar la fuente GitOps y validar las acciones contra
recursos de prueba, Hermes en Discord sigue teniendo solo las herramientas desplegadas.

## Límites deliberados

- No hay terminal, filesystem ni ejecución arbitraria. Las escrituras se hacen mediante funciones API concretas.
- El porcentaje histórico excluye huecos: se informa cobertura desconocida. No es uptime de ventana completa.
- Las NetworkPolicies permiten HTTPS público al modelo, DNS y los endpoints LAN específicos de cada integración habilitada.
- Sin gestión de Docker Compose/n8n, DNS/router, edición GitOps/Argo CD, agentes de código ni RAG.
- Sin inferencia validada, monitoreo propio ni backup/restore todavía. Eso es necesario antes de producción.
- `local-path` fija el estado a un nodo y no permite expansión directa; no ofrece alta disponibilidad.
- Hermes puede copiar la key de entorno a su credential pool en el PVC: respaldar ese estado cifrado.

## Reversión

Detener ambos deployments conservando los PVC, o revertir la versión en GitOps después de validar
compatibilidad de los datos. No borrar namespace/PVC como procedimiento de rollback.
