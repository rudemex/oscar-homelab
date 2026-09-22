# Reorganización del rack — borrador de trabajo

**Estado:** propuesta en discusión, nada de esto está aplicado todavía. **Fecha:** 2026-09-22 **Por qué existe:** con
meses de sesiones agregando cosas de a una, terminamos con herramientas repetidas (tres o cuatro midiendo lo mismo) y al
menos un servicio en el lugar que no le corresponde (Minecraft mezclado con la infra core en vez de con los juegos).
Esto ordena qué hay, dónde debería vivir, y qué falta decidir.

## Hardware disponible

| Nodo físico                 | Qué es                                                                     | RAM   | Disco                                                                     | Estado                   |
|-----------------------------|----------------------------------------------------------------------------|-------|---------------------------------------------------------------------------|--------------------------|
| `oscar-core`                | Dell OptiPlex 7060 Micro, Proxmox VE — el más potente, con margen de sobra | 32 GB | NVMe 1 TB (sano) + SSD SATA (muerto, esperando reemplazo y cables nuevos) | En línea                 |
| Raspberry Pi 3 (`pinode01`) | Standalone, no virtualizada                                                | 1 GB  | microSD 64 GB                                                             | En línea, ~54% RAM usada |
| Raspberry Pi 3 (`pinode02`) | Standalone, no virtualizada                                                | 1 GB  | microSD 64 GB                                                             | En línea, ~48% RAM usada |

**Sobre el SSD SATA:** en pausa hasta que lleguen el disco y los cables nuevos. Cuando estén, se prueba el disco viejo
en un adaptador USB-SATA para saber si es recuperable, y aparte se decide qué backend de storage usa el reemplazo.

**Sobre las Pi:** no son "espacio libre" — cada una ya tiene un rol con la mitad de su RAM comprometida. Sumarles algo
nuevo compite en serio por memoria; no cualquier app liviana entra gratis.

## Inventario real (relevado en vivo, 2026-09-22)

### `oscar-core` (Proxmox, 192.168.0.233)

| Servicio            | Acceso                                                                                             | Nota                                                                            |
|---------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Proxmox VE (web UI) | https://192.168.0.233:8006, LAN                                                                    | gestión del hipervisor                                                          |
| ProxMenux Monitor   | http://192.168.0.233:8008 LAN, https://monitor.oscarlab.com.ar remoto (Cloudflare Tunnel + Access) | dashboard del propio Proxmox — redundante con Beszel/Glances/Grafana, ver abajo |

### VM core01 (192.168.0.156, 8 GB RAM, ~1,5 GB usada) — apps generales

| Servicio                      | DNS / URL                                                          | Acceso                                                                                 |
|-------------------------------|--------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| Homepage                      | http://192.168.0.156:3005 LAN, https://home.oscarlab.com.ar remoto | Cloudflare Access                                                                      |
| Nginx Proxy Manager           | http://192.168.0.156:81                                            | LAN                                                                                    |
| Cloudflare Tunnel (principal) | —                                                                  | 7 hostnames públicos: home, vault, n8n, beszel, monitor, ha, led                       |
| Portainer (servidor)          | http://192.168.0.156:9000 (puerto a confirmar)                     | LAN                                                                                    |
| Vaultwarden                   | https://vault.oscarlab.com.ar                                      | Cloudflare Access                                                                      |
| n8n + Postgres                | https://n8n.oscarlab.com.ar                                        | Cloudflare Access                                                                      |
| SMTP relay                    | interno (Postfix)                                                  | sin acceso directo                                                                     |
| Beszel (servidor) + agente    | https://beszel.oscarlab.com.ar                                     | Cloudflare Access — redundante, ver abajo                                              |
| Glances                       | http://192.168.0.156:61208                                         | LAN — redundante, ver abajo                                                            |
| MySpeed                       | http://192.168.0.156:5216 (puerto a confirmar)                     | LAN — redundante con el Speedtest exporter propuesto, ver abajo                        |
| Minecraft                     | — (apagado)                                                        | mal ubicado: es un juego, mezclado acá con infra core en vez de estar con CS2 en lab01 |

### VM devops01 (192.168.0.151, 12 GB RAM, ~4,3 GB usada) — DevOps/CI

| Servicio                            | DNS / URL                                         | Acceso                              |
|-------------------------------------|---------------------------------------------------|-------------------------------------|
| Forgejo (git + CI runner)           | http://git.oscar.home:3000                        | LAN                                 |
| Nexus (registry Docker + proxy npm) | http://nexus.oscar.home:8081 (UI), :8082 (Docker) | LAN                                 |
| Infisical (backend + DB + Redis)    | http://infisical.oscar.home                       | LAN                                 |
| Portainer-agent                     | —                                                 | interno, lo usa Portainer de core01 |
| Beszel-agent                        | —                                                 | interno, lo usa Beszel de core01    |

### VM k3s01 (192.168.0.150, 8 GB RAM, ~2 GB usada) — Kubernetes / GitOps

| Servicio                               | DNS / URL                                                     | Acceso                          |
|----------------------------------------|---------------------------------------------------------------|---------------------------------|
| Argo CD                                | http://argocd.oscar.home                                      | LAN                             |
| Traefik (Ingress)                      | *.oscar.home apunta a esta IP                                 | resuelve todo lo de abajo       |
| Headlamp                               | http://headlamp.oscar.home                                    | LAN                             |
| SearXNG                                | http://searxng.oscar.home                                     | LAN                             |
| ci-demo                                | http://ci-demo.oscar.home                                     | LAN, app de prueba del pipeline |
| oscar-led-controller                   | http://led.oscar.home LAN, https://led.oscarlab.com.ar remoto | Cloudflare Access               |
| infisical-operator                     | —                                                             | interno, sincroniza secrets     |
| claude-code-poc (namespace hermes-poc) | —                                                             | PoC descartable, sin URL        |

### VM lab01 (192.168.0.152, 6 GB RAM, ~466 MB usada) — juegos

| Servicio | DNS / URL                 | Acceso                  |
|----------|---------------------------|-------------------------|
| CS2      | puerto de juego (apagado) | directo por IP, sin DNS |

Hoy casi vacía: solo CS2, apagado. Candidata a absorber Minecraft (que hoy está mal puesto en core01), o a
achicarse/fusionarse si el uso real de los servidores de juego sigue siendo esporádico.

### pinode01 — red (192.168.0.213)

| Servicio                  | DNS / URL                                                                         | Acceso                                                                    |
|---------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| AdGuard Home              | http://192.168.0.213:3000                                                         | LAN — es el DNS primario de core01, lab01, el propio Proxmox y las dos Pi |
| Tailscale (subnet router) | —                                                                                 | acceso remoto a toda la LAN; respaldo mutuo con el de core01              |
| Uptime Kuma               | http://192.168.0.213:3001 LAN, https://kuma.oscarlab.com.ar remoto (túnel propio) | Cloudflare Access                                                         |
| cloudflared (dedicado)    | —                                                                                 | solo enruta kuma.oscarlab.com.ar, para que sobreviva a una caída del Dell |
| node_exporter             | :9100                                                                             | scrapeado por Prometheus                                                  |

### pinode02 — observabilidad (192.168.0.214)

| Servicio          | DNS / URL                 | Acceso             |
|-------------------|---------------------------|--------------------|
| Prometheus        | http://192.168.0.214:9090 | LAN                |
| Grafana           | http://192.168.0.214:3006 | LAN                |
| Blackbox Exporter | http://192.168.0.214:9115 | LAN, sin UI propia |
| node_exporter     | :9100                     | métricas propias   |

## Redundancias encontradas — necesitan más información antes de decidir

Como pediste: no se elimina nada todavía. La idea es dejar correr Grafana un tiempo real y comparar contra lo que ya
existe, y recién ahí decidir si se puede sacar algo o si conviene que convivan.

| Función                                     | Herramientas que la cubren hoy                                     | Qué falta saber                                                                                                                                                                                |
|---------------------------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CPU/RAM/disco por host                      | Beszel, Glances, ProxMenux Monitor, y ahora Prometheus+Grafana     | ¿Grafana da el mismo detalle día a día? ¿Alguna de las otras tiene algo que Grafana no (por ejemplo, Glances ve procesos individuales; Beszel es la que alimenta el header de Homepage)?       |
| Velocidad de Internet                       | MySpeed (ya corriendo)                                             | El Speedtest exporter que se propuso para pinode02 sigue sin desplegarse — no se agrega hasta decidir si reemplaza a MySpeed o si conviene dejar los dos (distinta frecuencia, distinta vista) |
| Disponibilidad de servicios (¿está arriba?) | Uptime Kuma (21 monitores) y ahora Blackbox Exporter (5 objetivos) | Se solapan poco todavía (Blackbox es nuevo y chico); podrían quedar los dos — Kuma para notificaciones y una status page, Blackbox como la fuente de series históricas de Grafana              |

## Propuesta de renombrado

### Las VM del Dell: no tocarlas

Ya están nombradas por función (core01, devops01, k3s01, lab01) y son fáciles de entender. Renombrarlas implica tocar
DNS (AdGuard), el inventario de Ansible, referencias en Argo CD/GitOps y la documentación entera, para ganar poco.
Recomendación: dejarlas como están.

### Las Raspberry Pi: sí tiene sentido

Se llaman pinode01/pinode02 por el orden en que se instalaron, no por su función. El plan original de infraestructura
(OSCAR_FINAL_INFRASTRUCTURE.md) ya las nombraba por rol: network01 y monitor01. Propuesta:

| Nombre actual | Nombre propuesto | Motivo                                                                              |
|---------------|------------------|-------------------------------------------------------------------------------------|
| pinode01      | network01        | Coincide con el plan original; es lo que hace (DNS, VPN, monitor de disponibilidad) |
| pinode02      | monitor01        | Ídem; ya se lo venía llamando así en la doc                                         |

Esto es más manejable que renombrar el Dell: son 2 hosts, con pocas referencias (hostname de la Pi, inventario de
Ansible, AdGuard, Homepage, Kuma, Grafana, la doc de docs/hardware/). Si se confirma, se hace en un solo paso y se
actualiza todo junto.

## Cosas fuera de lugar, para mover

- Minecraft: está en core01 (apps generales), debería estar en lab01 (junto con CS2, es la VM de juegos).

## Preguntas abiertas antes de tocar nada

1. ¿Se confirma el renombrado pinode01→network01 / pinode02→monitor01?
2. ¿Se mueve Minecraft a lab01 ahora, o se deja para cuando se vuelva a usar (sigue sin resolverse el usuario real de
   Java)?
3. Para las redundancias de monitoreo: ¿dejamos correr Grafana un tiempo (¿cuánto?) antes de decidir qué sacar, o se
   compara ya mismo función por función?
4. ¿Se sigue con el Speedtest exporter en core01 (quedó pausado) o se pospone hasta resolver el tema MySpeed?

## Estado al momento de escribir esto (2026-09-22)

Las 4 preguntas de arriba ya están respondidas (ver el resto del documento y el plan aprobado más abajo). Lo que sigue es **ejecución**, no más decisiones de diseño, salvo que aparezca algo imprevisto.

- Se aprobó un plan detallado de ejecución con Claude Code, guardado en `/Users/maximilianodelgado/.claude/plans/quizzical-discovering-lerdorf.md` (en esta misma Mac — si no es accesible desde donde corra Codex, el contenido relevante está resumido en el prompt de abajo).
- OSCAR está encendido y sano: 5 VMs en el Dell, Argo CD con sus aplicaciones `Synced`/`Healthy`, las 2 Pi arriba.
- El SSD SATA de `Backups` volvió (era el conector, no el disco) y está reactivado en producción — no es parte de esta reorganización, ver `docs/arquitectura/estado-actual.md`.
- `oscar-gitops` (Forgejo, `mdelgado/oscar-gitops`, rama `main`) ya tiene subido: el control node de Ansible completo (`ansible/`, roles `common`/`node_exporter`/`docker`/`monitoring_stack`), con el stack de `monitor01` (Prometheus, Grafana, Blackbox HTTP+ICMP) **ya desplegado y funcionando** en `pinode02` (192.168.0.214), y el Speedtest exporter **preparado en el código pero sin desplegar todavía**.
- Las dos contraseñas nuevas (sudo de las Pi, admin de Grafana) están cifradas con `ansible-vault` en `ansible/group_vars/{pis,monitor01}/vault.yml`, y la contraseña del vault de Ansible en sí ya está guardada en Vaultwarden (ítem "Ansible Vault (oscar-gitops)") — no está en ningún archivo del repo.

## Prompt para Codex (continuar la ejecución)

Copiar y pegar tal cual como prompt inicial:

> Segui el plan de reorganizacion de la infraestructura homelab "O.S.C.A.R." documentado en `REORGANIZACION_RACK.md` (raiz de este repo, `oscar-homelab`). Ese archivo tiene el inventario completo relevado en vivo, las decisiones ya tomadas con el usuario, y las 4 preguntas abiertas ya respondidas en la seccion "Estado al momento de escribir esto". No vuelvas a proponer alternativas a esas decisiones salvo que encuentres algo que las contradiga en la practica.
>
> Contexto que necesitas saber antes de tocar nada:
> - Todo el proyecto se documenta y se conversa en **español**.
> - Hay un repo hermano `oscar-gitops` en Forgejo (`http://git.oscar.home/mdelgado/oscar-gitops`, rama `main`) con el control node de Ansible (`ansible/`) y los charts de Argo CD (`apps/`, `infra/`). Cloná ese repo tambien; las credenciales de Forgejo estan en Vaultwarden ("O.S.C.A.R." token), no las pidas por otro lado.
> - La contraseña que descifra `ansible/group_vars/{pis,monitor01}/vault.yml` esta en Vaultwarden, item "Ansible Vault (oscar-gitops)". Sin eso no podes correr el playbook contra las Pi ni tocar la config de Grafana.
> - **No rotes ninguna credencial** (contraseña de `pi`, tokens, etc.) aunque las veas en texto plano en algun lado — es una decision explicita del usuario, es una red domestica que considera segura. Ver la memoria/nota al respecto si tu entorno la tiene disponible, o preguntale al usuario si no estas seguro.
> - Antes de escribir en cualquier microSD o tocar `/etc/hosts`/`cmdline.txt` de una Raspberry Pi, pedile permiso explicito al usuario — una vez se corrompio una tarjeta por sacarla sin expulsarla primero.
> - Homepage (`core01`, `services.yaml`) esta detras de Cloudflare Tunnel en `home.oscarlab.com.ar` — las paginas se renderizan dinamicamente (no son un asset estatico cacheado), asi que normalmente NO hace falta purgar la cache de Cloudflare al editar `services.yaml`; si en cambio tocas `custom.css`/`custom.js`, si hace falta purgar (son estaticos y Cloudflare los cachea en el borde).
> - Cualquier edicion a `services.yaml` de Homepage: nunca con `sed -i` dentro del contenedor. Traer el archivo, editar local, validar YAML, subir por `base64 | ssh ... | base64 -d`, reiniciar el contenedor, y dejar un backup del archivo anterior en el propio host.
> - El widget nativo `prometheusmetric` de Homepage soporta PromQL arbitrario (confirmado contra `gethomepage.dev`) — es el camino para reemplazar las tarjetas de Beszel/Glances el dia que se decida retirarlas, pero **no las retires todavia** sin comparar con datos reales en Grafana primero.
>
> Pasos concretos, en orden (el detalle completo de cada uno esta en `REORGANIZACION_RACK.md`, seccion "Pasos de ejecucion"):
> 1. Verificar que OSCAR este arriba y sano (5 VMs del Dell, Argo CD con sus 8 aplicaciones `Synced`/`Healthy`, las 2 Raspberry Pi respondiendo).
> 2. Renombrar las Pi: `pinode01`→`network01` (192.168.0.213), `pinode02`→`monitor01` (192.168.0.214) — hostname + `/etc/hosts` en cada una, y actualizar `ansible/inventory/hosts.yml` en `oscar-gitops`.
> 3. Agregar al rol `monitoring_stack` de Ansible un exporter de Proxmox (`prometheus-pve-exporter`, instalado en `oscar-core` via `pip`/`pipx` ya que Proxmox no corre Docker) y sumarlo como target de Prometheus.
> 4. Correr el playbook (`ansible-playbook site.yml --limit monitor01:speedtest_host`) para desplegar lo que ya esta en el codigo: el monitor de Internet (Blackbox ICMP), el Speedtest exporter en `core01`, y el exporter de Proxmox nuevo.
> 5. Verificar en Grafana (`http://192.168.0.214:3006`, va a pasar a `192.168.0.214` con nombre `monitor01` si el paso 2 ya se hizo) que las series nuevas (`pve_*`, `speedtest_*`, `probe_success{job="blackbox_icmp"}`) muestran datos reales.
> 6. Renombrar la documentacion: `docs/hardware/pinode01.md`→`network01.md`, `pinode02.md`→`monitor01.md`, actualizar el sidebar y grep todo `docs/` por referencias cruzadas a los nombres viejos.
> 7. Commit + push de `oscar-gitops` y de `oscar-homelab` (con `yarn build` antes de commitear docs), siguiendo el estilo de mensajes de commit ya usado en el historial de ambos repos (en español, explicando el porque, no solo el que).
> 8. Actualizar `REORGANIZACION_RACK.md` marcando resuelto lo que se fue completando.
> 9. Recien al final, y solo si el usuario lo confirma en el momento: migrar Minecraft de `core01` a `lab01` (no es bloqueante, puede quedar para despues).
>
> No apagues ni reinicies ninguna VM o servicio en produccion sin avisar antes y explicar que se va a interrumpir. No tomes decisiones de "que herramienta de monitoreo sacar" — eso queda para cuando el usuario compare los dashboards nuevos con las herramientas viejas, con datos reales, en persona.
