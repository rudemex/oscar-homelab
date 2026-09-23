# Reorganización del rack

**Estado:** ✅ **Reorganización completa (2026-09-23).** Los 7 pasos de "Pasos de ejecución" están hechos — ver
"Estado al momento de escribir esto" abajo para el detalle de cada uno. Queda solo la Fase 2 (diferida, sin fecha:
VM `apps` como worker de `k3s`) y las decisiones explícitamente fuera de alcance (ver esa sección).

**Por qué existe:** meses de sesiones agregando cosas de a una dejaron herramientas repetidas midiendo lo mismo,
`core` como cajón de sastre (borde de red + apps de usuario + automatización + monitoreo, todo junto), y un
servicio en el lugar que no corresponde (Minecraft mezclado con infra en vez de con los juegos).

## Objetivo

Que cada host tenga una responsabilidad clara, evitando: servicios duplicados, hosts "cajón de sastre", mezclar
infraestructura con aplicaciones, mezclar software propio con software de terceros, mezclar experimentación con
servicios estables, y dependencias innecesarias entre componentes.

## Convención de nombres

Se elimina el sufijo `01` de los hosts cuando existe una única instancia real del rol (detalle y ejemplos en
[`docs/referencia/naming.md`](docs/referencia/naming.md)). La numeración se usa solo cuando existen múltiples
instancias reales (ej. `k3s-worker01`, `k3s-worker02` — no aplica todavía).

## Las cuatro áreas

```text
O.S.C.A.R.
│
├── INFRASTRUCTURE   → core, network, monitor
├── PLATFORM         → devops, automation, k3s
├── WORKLOADS        → services, apps
└── SPECIAL PURPOSE  → games, lab
```

## Arquitectura objetivo (hosts y servicios)

```text
O.S.C.A.R.
│
├── INFRASTRUCTURE
│   ├── core                        [VM, Dell]
│   │   ├── Homepage
│   │   ├── Nginx Proxy Manager
│   │   └── SMTP Relay
│   │
│   ├── network                     [Raspberry Pi]
│   │   ├── AdGuard
│   │   ├── Tailscale
│   │   └── cloudflared (tunneles centralizados)
│   │
│   └── monitor                     [Raspberry Pi]
│       ├── Prometheus
│       ├── Grafana
│       ├── Blackbox Exporter
│       └── Uptime Kuma
│
├── PLATFORM
│   ├── devops                      [VM, Dell]
│   │   ├── Forgejo
│   │   ├── Forgejo Actions Runner (ya corre acá, contenedor `forgejo-runner`)
│   │   ├── Nexus
│   │   └── Infisical
│   │
│   ├── automation                  [VM nueva, Dell]
│   │   ├── n8n main
│   │   ├── PostgreSQL
│   │   ├── Redis
│   │   └── n8n workers (✅ 1 worker activo desde 2026-09-23, concurrency 10)
│   │
│   └── k3s                         [VM, Dell]
│       ├── Argo CD
│       ├── Traefik
│       ├── Headlamp
│       ├── Infisical Operator
│       └── ⚠️ PROVISIONAL: ci-demo, oscar-led-controller — pertenecen conceptualmente a `apps`,
│           se quedan acá hasta la Fase 2 (ver nota "apps" más abajo). No agregar más apps propias
│           a `k3s` asumiendo que se van a quedar — nacen ya marcadas para migrar.
│
├── WORKLOADS
│   ├── services                    [✅ LXC 108 unprivileged, Dell, 192.168.0.154 — desde 2026-09-23]
│   │   ├── Vaultwarden       (migrado de core)
│   │   ├── SearXNG           (migrado de k3s)
│   │   └── DocuSeal          (nuevo, falta setup inicial)
│   │
│   └── apps                        [diferido — ver Fase 2, será VM/worker de k3s]
│       └── (futuro) ci-demo, oscar-led-controller, como worker del cluster k3s
│
└── SPECIAL PURPOSE
    ├── games                       [✅ VM 109, Dell, 192.168.0.155 — desde 2026-09-23, uso activo]
    │   ├── Minecraft   (migrado de core)
    │   └── CS2         (migrado de lab)
    │
    └── lab                         [VM, Dell — ex lab, reutilizada]
        └── experimentos y pruebas (incluye Docker/K8s/acceso a kernel sin restricciones)
```

**Fuera de esta lista, sin cambios de fondo:** VM 106 (Home Assistant / HAOS) — es un appliance, no un stack Docker
propio; no encaja limpio en ninguna de las 4 áreas (es "software de terceros" pero corre su propio SO, no
contenedores nuestros). Se deja como host independiente, sin renombrar por ahora.

## VM vs LXC — criterio, no regla general

Decisión explícita: **no** se adopta LXC como regla general solo para ahorrar RAM. Se usa LXC únicamente cuando el
servicio es liviano, estable, y no necesita aislamiento ni capacidades especiales del kernel. Por host:

| Host | Tipo | Por qué |
|---|---|---|
| `core`, `devops`, `k3s` | VM (sin cambios) | ya son VM, sin motivo para migrarlas |
| `automation` | **VM** | tiene estado real (Postgres+Redis), es un componente importante de OSCAR y va a crecer (workers) — se prioriza aislamiento y kernel propio sobre ahorro de RAM |
| `services` | **LXC unprivileged** | Vaultwarden/SearXNG/DocuSeal son livianos y estables, sin necesidad de capacidades especiales de kernel — Docker/Compose adentro del LXC si no complica la config |
| `games` | **VM** | máximo aislamiento y compatibilidad; se enciende/apaga entera bajo demanda sin afectar a nadie más |
| `lab` | **VM** (ya lo era) | tiene que permitir experimentar libremente, incluso con Docker, Kubernetes o configuraciones que requieran acceso al kernel |
| `apps` (Fase 2) | VM | worker de k3s, necesita cgroups prolijos |

Los LXC que se creen van **unprivileged** siempre que sea posible.

## Monitoreo de Internet — throughput y caídas son dos cosas distintas

Internet real: 600Mb simétrico. El requisito es medir **cuánto anda** (throughput) y **si corta** (disponibilidad) —
son dos mediciones con requisitos técnicos distintos, y van en hosts distintos a propósito:

| Qué mide | Dónde | Por qué ahí |
|---|---|---|
| Throughput real (Mbps) | `core` (MySpeed hoy, Speedtest exporter después) | Necesita NIC gigabit. La Pi 3 tiene Ethernet limitado a ~100Mbps (comparte bus con USB 2.0) — medir desde ahí reportaría un techo falso muy por debajo de los 600Mb reales |
| Caídas/cortes (¿hay internet o no?) | `monitor` (Blackbox Exporter, módulo `icmp`, ya preparado en el rol `monitoring_stack` de Ansible, pinguea `1.1.1.1`/`8.8.8.8`) | Un ping no pesa nada — el techo de 100Mbps de la Pi no es un problema para esto. Además Uptime Kuma (que se muda a `monitor`) puede sumar su propio monitor de "Internet" con notificación push si se corta |

`monitor` grafica el throughput real via el dato que le manda `core`, pero la medición en sí no se mueve de ahí.

## AdGuard — no se activa como DNS de toda la LAN (decisión firme)

**No reactivar el DHCP-wide de AdGuard.** Ya se probó (2026-09-18): coincidió con una caída real de velocidad
percibida (600→20Mbps). La causa raíz se diagnosticó y se corrigió técnicamente (`ratelimit: 20` en la config de
AdGuard descartaba en silencio consultas DNS por encima de ese límite agregado por subred — se subió a `300`, ver
[`docs/red/dns-adguard.md`](docs/red/dns-adguard.md)), pero **la decisión es no volver a activarlo** de todos
modos. Se queda como DNS opt-in por dispositivo (`192.168.0.213` hoy, la IP de `network` después del rename), no
como default del router. El router sigue repartiendo `8.8.8.8`/`8.8.4.4` por DHCP.

Esto es relevante para la sección de acceso de abajo: sin AdGuard como DNS por defecto, ningún dispositivo nuevo
resuelve `*.oscar.home` solo — necesita `/etc/hosts` o apuntar su DNS a mano.

## Acceso y exposición — cómo llega cada servicio

Clasificación de cómo se accede a lo que corre en O.S.C.A.R., para no tener que redescubrirlo cada vez:

| Forma de acceso | Qué significa | Requiere |
|---|---|---|
| **IP directa LAN** | `192.168.0.x:puerto`, sin DNS de por medio | nada, funciona siempre dentro de la LAN |
| **`*.oscar.home` (AdGuard)** | nombre resuelto por AdGuard en `network`, wildcard a Traefik (`k3s`) o rewrites puntuales a NPM (`core`) | el dispositivo tiene que apuntar su DNS a `192.168.0.213` a mano — **no es el default de la LAN** (ver decisión de arriba) |
| **`/etc/hosts`** | entrada manual `IP nombre.oscar.home` en el dispositivo cliente | para un dispositivo puntual que no quiere cambiar su DNS pero sí usar el nombre corto |
| **Cloudflare Tunnel + Access** | hostname público (`*.oscarlab.com.ar`), pero pide login (Cloudflare Access) antes de llegar al servicio | cuenta autorizada en Cloudflare Access; el servicio nunca expone su puerto directo a Internet |
| **Cloudflare Tunnel público** | hostname público sin Access — cualquiera que lo conozca entra | usar solo para algo pensado para ser público de verdad |

Estado real hoy, por servicio (ver también la tabla de "Redundancias"/inventario más arriba y
[`docs/seguridad/exposicion-internet.md`](docs/seguridad/exposicion-internet.md) para el detalle de seguridad):

| Servicio | LAN directo | `*.oscar.home` | Cloudflare Access | Público sin Access |
|---|---|---|---|---|
| Homepage | ✅ `:3005` | — | ✅ `home.oscarlab.com.ar` | — |
| Vaultwarden | — | — | ✅ `vault.oscarlab.com.ar` | — |
| n8n | — | — | ✅ `n8n.oscarlab.com.ar` | — |
| Beszel | — | — | ✅ `beszel.oscarlab.com.ar` | — |
| ProxMenux Monitor | ✅ `:8008` | — | ✅ `monitor.oscarlab.com.ar` | — |
| Home Assistant | — | — | ✅ `ha.oscarlab.com.ar` | — |
| oscar-led-controller | ✅ (Traefik, `k3s`) | ✅ `led.oscar.home` | ✅ `led.oscarlab.com.ar` | — |
| Uptime Kuma | ✅ `:3001` (hoy en `network`, después `monitor`) | — | ✅ `kuma.oscarlab.com.ar` (túnel propio) | — |
| Forgejo, Nexus, Infisical, Argo CD, Headlamp, SearXNG, ci-demo | ✅ vía IP o `*.oscar.home` | ✅ | — | — |
| Proxmox VE, AdGuard UI, Grafana, Prometheus | ✅ solo IP directa | — | — | — (deliberado: nunca exponer gestión de infra a Internet) |

**Regla para todo lo nuevo:** ¿lo necesita alguien fuera de la LAN? → Cloudflare Tunnel, con Access salvo que
exista una razón concreta para que sea público. ¿Es solo para uso dentro de casa? → IP directa o `*.oscar.home` (a
mano por `/etc/hosts` o DNS del dispositivo, mientras AdGuard no sea el default de la LAN), nunca expuesto afuera.
Paneles de gestión de infraestructura (Proxmox, AdGuard, Grafana, Prometheus) **nunca** salen a Internet, ni con
Access.

## `apps` como worker de k3s — Fase 2, diferida

El diseño a futuro separa `k3s` (control plane: Argo CD, Traefik, Headlamp, operators) de `apps` (worker: los pods
de las aplicaciones propias). Hoy no existe ese segundo nodo. **Para esta pasada**, `ci-demo` y
`oscar-led-controller` se quedan corriendo en el cluster `k3s` tal cual están (Argo CD los sigue desplegando sin
cambios). Crear el VM `apps`, unirlo al cluster como worker, y taintear `k3s` para que no reciba pods de
aplicación, queda como una fase separada y posterior — no bloquea el resto de esta reorganización.

## Portainer — se elimina

Portainer Server y Portainer Agent se dan de baja de todos los hosts. La administración pasa a: Docker Compose +
Ansible (hosts sueltos), Git + Argo CD (Kubernetes).

## Uptime Kuma — una sola instancia, se muda a `monitor`

Hoy vive en `pinode01` (futuro `network`). Se muda a `monitor` (futuro `pinode02`) junto con el resto de la
observabilidad. Implica migrar su base SQLite y actualizar el `cloudflared` dedicado que hoy solo enruta
`kuma.oscarlab.com.ar` (el túnel se centraliza en `network`, pero puede seguir apuntando a Kuma donde sea que viva,
no tiene que ser local). Separación infra vs apps vs juegos dentro de Kuma se hace con grupos/tags, no con
instancias separadas.

## Observabilidad — sigue la política ya acordada: nada se apaga todavía

La cadena oficial es `node_exporter → Prometheus → Grafana`. Beszel, Glances, ProxMenux Monitor y MySpeed **no se
apagan en esta pasada** — se espera a tener datos reales corriendo en paralelo un tiempo antes de decidir, función
por función, qué se retira. Uptime Kuma no es redundante con Prometheus/Grafana: responde "¿está arriba?" (Kuma) vs
"¿cómo está funcionando?" (Prometheus/Grafana), son objetivos distintos y ambos se quedan.

## Presupuesto de recursos (Dell, `oscar-core`)

Host: 31GB RAM físicos, 6 núcleos / 12 hilos. Estado actual (2026-09-22, sin balloon configurado en ninguna VM):

| VM/host | RAM configurada hoy | Uso real observado | Propuesta nueva | Tipo |
|---|---|---|---|---|
| `core01` → **core** (✅ renombrado) | 8GB | ~1,5GB | **4GB** | VM (existente) |
| `devops01` → **devops** (✅ renombrado) | 12GB | ~4,3GB | **6GB** | VM (existente) |
| `k3s01` → **k3s** (✅ renombrado) | 8GB | ~2GB | **4GB** | VM (existente) |
| `lab01` → **lab** (✅ renombrado) | 6GB | ~466MB | **2GB** | VM (existente, reutilizada) |
| — → **automation** | — | — | **4GB** | VM nueva |
| — → **services** | — | — | **2GB** | LXC unprivileged nueva |
| — → **games** | — | — | **6GB** (apagada salvo uso) | VM nueva |
| VM106 (HA) | 4GB | — | 4GB (sin cambios) | VM (existente) |

Total con todo prendido salvo `games` (que se enciende solo para jugar): **26GB de 31GB**, deja ~5GB de margen
para el propio host. Con `games` prendida sube a 32GB — al límite, por eso se recomienda mantenerla apagada salvo
uso activo (ya es el patrón actual con `lab`).

**Recomendación adicional:** activar memory ballooning (`balloon: <min>`) en las VMs del Dell — hoy ninguna lo
tiene, así que Proxmox no puede reclamar RAM no usada de una VM para dársela a otra bajo presión.

## Migraciones necesarias

```text
core
├── Homepage             → core (sin cambios funcionales)
├── NPM                  → core (sin cambios funcionales)
├── SMTP Relay           → core (sin cambios funcionales)
├── Vaultwarden          → services (nueva LXC) — ✅ hecho (2026-09-23)
├── n8n + Postgres       → automation (nueva VM) — ✅ hecho (2026-09-23)
├── Minecraft             → games (nueva VM) — ✅ hecho (2026-09-23)
├── Cloudflare Tunnel      → network (centralizar ahí, hoy vive en core)
├── Portainer Server      → ELIMINAR
├── Beszel Server         → se queda (política de monitoreo: esperar datos)
├── Glances                → se queda (ídem)
└── MySpeed                → se queda en core (corrección respecto al diseño original)

devops
├── Forgejo / Nexus / Infisical → devops (sin cambios funcionales, solo rename)
├── Portainer Agent              → ELIMINAR
└── Beszel Agent                  → se queda (política de monitoreo)

k3s
├── Argo CD / Traefik / Headlamp / Infisical Operator → k3s (sin cambios funcionales, solo rename)
├── ci-demo / oscar-led-controller                      → se quedan en k3s (Fase 2 los mueve a `apps`)
└── SearXNG                                               → services (nueva LXC) — ✅ hecho (2026-09-23), como
                                                             contenedor Docker suelto

lab
├── CS2         → games (nueva VM) — ✅ hecho (2026-09-23)
└── VM en sí    → se reutiliza como lab (rename, se vacía)

pinode01 → network
├── hostname, AdGuard, Tailscale, cloudflared → sin cambios funcionales, solo rename

pinode02 → monitor
├── hostname, Prometheus, Grafana, Blackbox   → sin cambios funcionales, solo rename
└── + Uptime Kuma (migra desde network)
```

## Documentación a actualizar — cuándo, no todo junto

Hay ~80 páginas en `docs/` que mencionan nombres/servicios afectados. Actualizarlas todas ahora describiría un
estado que todavía no existe. Se actualiza en el momento en que cada migración se ejecuta de verdad, no antes:

- **Ya actualizado (2026-09-22):** este archivo, `docs/referencia/naming.md`.
- **Al renombrar las Pi:** `docs/hardware/pinode01.md`→`network.md`, `pinode02.md`→`monitor.md`, y grep de
  referencias cruzadas (`docs/red/dns-adguard.md`, `docs/arquitectura/estado-actual.md`, etc.).
- **Al crear `automation`:** `docs/automatizacion/*.md` (instalacion-n8n.md, n8n-arquitectura.md,
  workflow-salud.md), `docs/backup-dr/backup-n8n.md`.
- **Al crear `services` y migrar Vaultwarden:** `docs/servicios/vaultwarden.md`.
- **Al migrar SearXNG:** referencias en `docs/kubernetes/` si las tiene.
- **Al eliminar Portainer:** `docs/servicios/portainer.md` (marcar como retirado, no borrar el archivo — dejar el
  historial de por qué se usó y por qué se sacó).
- **Al crear `games` y mover Minecraft/CS2:** `docs/juegos/minecraft.md`, `docs/juegos/vision-general.md`.
- **Al renombrar `core`/`devops`/`k3s`/`lab`:** `docs/hardware/dell-7060.md`,
  `docs/proxmox/crear-vm-core.md` (posible rename de archivo), `docs/arquitectura/vision-general.md`,
  `docs/arquitectura/stack.md`, `docs/arquitectura/decisiones-arquitectonicas.md`, `docs/despliegues/indice.md`,
  y el resto que aparece en el grep de `core|devops|k3s|lab` sobre `docs/`.

## Pasos de ejecución (orden)

1. ✅ **Hecho (2026-09-22).** Renombrar las Pi: `pinode01`→`network`, `pinode02`→`monitor` (hostname + `/etc/hosts`
   + `preserve_hostname: true` en cloud-init en las dos — `monitor` no la tenía, se agregó). Actualizado
   `oscar-gitops/ansible/inventory/hosts.yml` (commit `969feb8`, **pendiente de `git push`**, ver nota abajo) y
   `docs/hardware/pinode01.md`→`network.md`, `pinode02.md`→`monitor.md` en `oscar-homelab` (commit `87e8557`).
   Verificado: `ansible -m ping` contra los 5 hosts responde `pong` con los nombres nuevos; Prometheus/Grafana/
   AdGuard siguen respondiendo tras el rename.
2. ✅ **Hecho (2026-09-22).** Migrar Uptime Kuma de `network` a `monitor`: datos copiados con checksum verificado,
   Homepage repuntado, e ingress rule de Cloudflare actualizado (ver hallazgo abajo). Detalle en
   `docs/servicios/uptime-kuma.md#migración-a-monitor-2026-09-22`.
   **Hallazgo en el camino:** el túnel dedicado `pinode01` de Cloudflare (pensado para que `kuma.oscarlab.com.ar`
   sobreviva a una caída del Dell) nunca enrutó nada en la práctica — el DNS real siempre apuntó al túnel de
   `core`, que proxea por LAN hacia la Pi. Pendiente decidir en el paso 9 si se le da uso real al túnel
   `pinode01` o se da de baja.
3. ✅ **Hecho (2026-09-23).** Right-sizing de RAM en `core`/`devops`/`k3s`/`lab` según la tabla de arriba.
   Aplicado con reboot uno por uno (sin hotplug/balloon configurado, el cambio de memoria no toma efecto en
   caliente), verificando servicios sanos antes de seguir con el siguiente:
   - ✅ `lab`: 6→2GB, reiniciada, sana.
   - ✅ `core`: 8→4GB, reiniciada, Homepage/NPM verificados, ~1,3GB en uso real de 3,8GB disponibles.
   - ✅ `devops`: sin jobs de CI corriendo verificado antes de reiniciar; 12→6GB, reiniciada, Forgejo verificado,
     todos los contenedores (Nexus, Infisical, forgejo-runner, Beszel-agent) arriba.
   - ✅ `k3s`: Argo CD verificado con sus 8 aplicaciones `Synced`/`Healthy` antes de tocarla; 8→4GB, reiniciada,
     nodo `Ready`, las 8 aplicaciones siguen `Synced`/`Healthy`, Headlamp/SearXNG/ci-demo/oscar-led-controller
     responden `200` vía Traefik. 2GB en uso real de 3,8GB — más ajustado que las otras (overhead propio de k3s),
     pero con margen.
4. ✅ **Hecho (2026-09-23).** Creado `automation` (VM 107, `192.168.0.153/24`, 2 vCPU/4GB/60GB, mismo patrón de
   clon que las demás). n8n+Postgres migrados desde `core`: contenedores parados, volúmenes empaquetados con
   checksum SHA-256 verificado en origen/Mac/destino, recreados y levantados en `automation`. Repuntados: Homepage
   (siteMonitor), el ingress rule de Cloudflare (`n8n.oscarlab.com.ar` → `192.168.0.153:5678`), y el monitor de
   Kuma. `n8n` en `core` queda detenido (no borrado) como respaldo. Detalle en
   `docs/arquitectura/estado-actual.md`.
   **Gotcha real, corregido en `docs/proxmox/crear-vm-core.md`:** el clon del template no hereda el tamaño de
   disco de la tabla de sizing, solo el tamaño original del template (~3.5GB) — faltaba un `qm resize` que no
   estaba en la receta. Se agregó el paso.
5. ✅ **Hecho (2026-09-23).** Creado `services` (LXC 108 unprivileged, `192.168.0.154/24`, Debian 13, `nesting=1,
   keyctl=1`, 2vCPU/2GB/16GB — Docker probado real con `docker run hello-world`, no asumido). Migrado Vaultwarden
   desde `core` (checksum verificado, ingress de Cloudflare repuntado). **Decisión del usuario: migrar SearXNG
   también** (no solo evaluar) — sacado de k3s/Argo CD, recreado en Compose con su config y secret intactos, app y
   recursos viejos borrados de k3s y de `oscar-gitops`. **Decisión del usuario: sumar DocuSeal ahora** — instalado
   en modo standalone (SQLite embebida, sin Postgres separado), falta que el usuario haga el setup inicial (cuenta
   admin) por la web. Los tres accesibles vía NPM + rewrite de AdGuard (`vault` además por Cloudflare Tunnel).
   Detalle completo en `docs/arquitectura/estado-actual.md`.
   **De paso (pedido fuera de este paso, mismo momento):** se borraron VM 101 (`haos-18.2`, HA vieja) y LXC 100
   (`adguard`, viejo) — ya no hacían falta, sus rescates de datos siguen en
   `/var/lib/vz/rescate-ssd-2026-09-22/`.
6. ✅ **Hecho (2026-09-23).** Creada `games` (VM 109, `192.168.0.155/24`, 4 vCPU/6GB/100GB). Minecraft migrado desde
   `core` (382MB, checksum verificado) y CS2 desde `lab` (67GB, ver detalle de la migración abajo). Homepage
   repuntado a las IPs nuevas. **No quedó apagada por defecto** como decía el plan original — el usuario la usa
   activamente, se deja encendida; se puede apagar manualmente cuando no se use.
   **Gotcha real (CPU):** la VM se creó sin `cpu: host` (quedó en el default `kvm64`, sin SSE4.2) — CS2 fallaba al
   arrancar con `"A CPU that supports the SSE4.2 processor feature is required"`. `lab` (el host original de
   CS2) ya tenía `cpu: host` seteado a propósito y no se replicó al crear `games`. Corregido con `qm set 109 --cpu
   host` + reboot. **Cualquier VM que corra juegos necesita `cpu: host` desde el vamos.**
   **Incidente real durante la migración de CS2:** la primera transferencia (73GB) se hizo con
   `docker run --rm alpine tar` en pipe — extremadamente lento (~1MB/s vía relay por la Mac, ~17MB/s directo por la
   falta de esto), y en el medio `lab` se quedó sin espacio en disco (el tar local de prueba llenó los 35GB
   libres). Se resolvió usando `rsync` **directo sobre el path del volumen en el host** (`/var/lib/docker/volumes/
   .../_data`), sin pasar por el wrapper de `docker run` — ahí sí a ~150MB/s reales de LAN, terminó en 7 minutos.
   **Lección: para volúmenes grandes, `rsync` directo sobre el filesystem del host, nunca `docker run --rm alpine
   tar` en pipe.** Después de la copia, CS2 igual necesitó reverificar/re-descargar ~73GB desde Steam (su propio
   manifiesto no confía en archivos copiados por fuera de Steam) — **coincidió con un cuelgue de red del Dell**
   (el mismo incidente recurrente ya documentado, ver `docs/arquitectura/estado-actual.md`) que cortó la descarga
   a mitad de camino; tras el reinicio físico, SteamCMD retomó solo desde donde había quedado, sin perder todo el
   progreso.
7. ✅ **Hecho (2026-09-23).** Renombrado `core01`→`core`, `devops01`→`devops`, `k3s01`→`k3s`, `lab01`→`lab`
   (vaciada de CS2, que ya está en `games`). Hostname + `/etc/hosts` + `preserve_hostname: true` en cloud-init en
   las 4 VMs (mismo patrón que las Pi). Inventario de Ansible actualizado y pusheado. Homepage repuntado (categoría
   "Kubernetes", tarjetas de Beszel, descripciones). **Barrido completo de documentación**: renombrado en bloque
   con un script Python (regex con límites de palabra, no `sed` — BSD `sed` en macOS no soporta `\b`) en 66
   archivos de `docs/` + este archivo; `docs/proxmox/crear-vm-core01.md` renombrado a `crear-vm-core.md` (sin
   links entrantes que corregir). Verificado: `yarn build` limpio, `grep` confirma cero referencias viejas
   restantes en toda la documentación.
   **Caso especial: `k3s`.** Es el node de un cluster Kubernetes de un solo nodo — se fijó `node-name: k3s01` en
   `/etc/rancher/k3s/config.yaml` **antes** de tocar el hostname del SO, para que el objeto `Node` de Kubernetes no
   dependa del hostname y no genere un nodo duplicado si el servicio de `k3s` se reinicia alguna vez (`kubectl get
   nodes` sigue mostrando `k3s01` a propósito, es interno y estable). El grupo de Ansible `k3s` y el host `k3s`
   ahora comparten nombre (warning no fatal de Ansible), se aceptó en vez de reestructurar el grupo.
8. Eliminar Portainer Server/Agent de todos los hosts.
9. Centralizar `cloudflared` en `network` (hoy hay instancias en `core` y una dedicada en `pinode01`).
10. Actualizar documentación según la tabla de arriba, commit + push en `oscar-homelab` y `oscar-gitops`.
11. Actualizar este archivo marcando cada paso como resuelto.
12. **Fase 2 (separada, sin fecha):** crear el VM `apps` como worker de `k3s`, mover `ci-demo` y
    `oscar-led-controller` ahí, taintear `k3s` para que no reciba pods de aplicación.

## Fuera de alcance, a propósito

- Apagar Beszel, Glances, ProxMenux Monitor o MySpeed — se decide más adelante con datos reales.
- La Fase 2 de `apps` (worker de k3s) — separada, no bloquea el resto.
- Reparación/reemplazo del tercer SSD SATA del Dell — pendiente de que el usuario lo conecte.
- VLANs / re-direccionamiento IP (`docs/red/plan-direccionamiento.md` es un ejemplo futuro, no aplica todavía) —
  los hosts nuevos usan una IP libre del mismo `192.168.0.0/24` plano de hoy, con reservation DHCP.

## Verificación

- `hostname` en cada Pi devuelve el nombre nuevo; `ansible -i inventory/hosts.yml all -m ping` sin errores contra
  los nombres nuevos.
- Uptime Kuma sigue notificando y su status page pública sigue funcionando tras la migración.
- Vaultwarden y n8n responden igual que antes tras migrar (login, workflows corriendo) desde su nuevo host.
- `pvesm`/`df` confirman que ningún host quedó sin espacio tras el right-sizing.
- Argo CD sigue con sus aplicaciones `Synced`/`Healthy` (el rename de `k3s01`→`k3s` no debería tocar nada del
  cluster en sí, pero se verifica).
- `yarn build` sin errores tras renombrar/crear páginas de doc.

## Estado al momento de escribir esto (2026-09-23)

- OSCAR está encendido y sano. El apagado de emergencia del 2026-09-22 (baja tensión) no dejó nada roto — se
  retomó sin problemas al día siguiente.
- El SSD SATA de `Backups` del Dell se resolvió: `sda` (WD Green, interno SATA) es `Backups`, `sdc`
  (`FTM1TN325H`, el que venía fallando, ahora externo USB) es `Documentos`, y se sumó un disco nuevo (SanDisk
  1TB, externo USB) como `Storage` general sin uso fijo — ver `docs/arquitectura/estado-actual.md`. **Límite real
  encontrado (2026-09-23): el controlador USB del Dell solo aguanta 2 discos externos alimentados por bus a la
  vez** — un tercero (probado con un `HS-SSD-WAVE` 240GB) entra en loop de reset, aunque esté en un puerto físico
  distinto. No se integró a la arquitectura.
- `oscar-gitops` (Forgejo, `mdelgado/oscar-gitops`, rama `main`) tiene: el control node de Ansible completo
  (`ansible/`), con el stack de observabilidad **ya desplegado y funcionando** en `monitor` (Prometheus, Grafana,
  Blackbox HTTP, Uptime Kuma), y el Speedtest exporter + Blackbox ICMP **preparados en el código pero sin
  desplegar**.
- **Paso 1 hecho (2026-09-22):** las Pi ya se llaman `network`/`monitor` a nivel de SO, `hosts.yml` de Ansible y la
  doc de `oscar-homelab` están al día. **Pendiente:** `git push` del commit `969feb8` en `oscar-gitops` — el clon
  de trabajo vive en un scratchpad fuera de este repo, y el push desde ahí quedó bloqueado por el clasificador de
  Claude Code ("Out-of-Place Publication"). Hay que pushearlo desde un checkout normal de `oscar-gitops`, o el
  usuario lo autoriza explícitamente.
- **Paso 2 hecho (2026-09-22):** Uptime Kuma migrado de `network` a `monitor`, con el ingress rule de Cloudflare
  corregido — ver detalle en el paso 2 de "Pasos de ejecución" y en `docs/servicios/uptime-kuma.md`.
- **Paso 3 hecho (2026-09-23):** right-sizing de RAM en las 4 VMs (`core`=4GB, `devops`=6GB, `k3s`=4GB,
  `lab`=2GB), todas reiniciadas y verificadas sanas.
- **Paso 4 hecho (2026-09-23):** VM `automation` creada (192.168.0.153) y n8n+Postgres migrados desde `core`,
  con Homepage/Cloudflare/Kuma repuntados. `core` conserva los contenedores viejos detenidos como respaldo. n8n
  además pasó a modo *queue* (Redis + worker) el mismo día, a pedido del usuario.
- **Paso 5 hecho (2026-09-23):** LXC `services` (192.168.0.154) creado y Vaultwarden migrado desde `core`.
  SearXNG migrado de k3s (no solo evaluado) y DocuSeal sumado — ambas decisiones del usuario, más allá de lo
  mínimo que pedía el paso. De paso: VM 101 y LXC 100 (viejos, sin uso) se borraron.
- **Paso 6 hecho (2026-09-23):** VM `games` (192.168.0.155) creada, Minecraft y CS2 migrados. Encontrado y
  corregido un gotcha real de `cpu: host` (sin eso, CS2 no arranca — falta SSE4.2). Un cuelgue de red del Dell
  (incidente recurrente ya documentado) interrumpió la descarga de reverificación de CS2 a mitad de camino; tras
  el reinicio físico, todo volvió sano solo (autostart de las VMs, Argo CD necesitó un refresh manual) y CS2
  retomó la descarga sin perder el progreso previo.
- **Paso 7 hecho (2026-09-23):** `core01`→`core`, `devops01`→`devops`, `k3s01`→`k3s`, `lab01`→`lab` renombrados a
  nivel de SO, inventario de Ansible pusheado, Homepage repuntado, y barrido completo de los 66 archivos de
  `docs/` que mencionaban los nombres viejos (más este archivo). `yarn build` limpio, sin referencias viejas
  restantes.
- **Con esto, los 7 pasos de la reorganización del rack están completos.** Lo único que queda es la Fase 2
  (diferida, VM `apps`) y lo explícitamente fuera de alcance (ver esa sección más arriba).

## Prompt para Codex (continuar la ejecución)

Copiar y pegar tal cual como prompt inicial:

> Segui el plan de reorganizacion de la infraestructura homelab "O.S.C.A.R." documentado en
> `REORGANIZACION_RACK.md` (raiz de este repo, `oscar-homelab`). Ese archivo tiene la arquitectura objetivo completa
> (4 areas: INFRASTRUCTURE/PLATFORM/WORKLOADS/SPECIAL PURPOSE), el criterio VM vs LXC por host, el presupuesto de
> recursos del Dell, la tabla de migraciones, y el orden de ejecucion en la seccion "Pasos de ejecucion". No
> propongas alternativas a esa arquitectura salvo que encuentres algo que la contradiga en la practica — ya fue
> discutida y aprobada con el usuario.
>
> Contexto que necesitas saber antes de tocar nada:
> - Todo el proyecto se documenta y se conversa en **español**.
> - Hay un repo hermano `oscar-gitops` en Forgejo (`http://git.oscar.home/mdelgado/oscar-gitops`, rama `main`) con
>   el control node de Ansible (`ansible/`) y los charts de Argo CD (`apps/`, `infra/`). Cloná ese repo tambien; las
>   credenciales de Forgejo estan en Vaultwarden ("O.S.C.A.R." token), no las pidas por otro lado.
> - La contraseña que descifra `ansible/group_vars/*/vault.yml` esta en Vaultwarden, item "Ansible Vault
>   (oscar-gitops)".
> - **No rotes ninguna credencial** aunque las veas en texto plano en algun lado — decision explicita del usuario,
>   entorno domestico que considera seguro.
> - Antes de escribir en cualquier microSD o tocar `/etc/hosts`/`cmdline.txt` de una Raspberry Pi, pedile permiso
>   explicito al usuario — una vez se corrompio una tarjeta por sacarla sin expulsarla primero.
> - Antes de crear una VM/LXC nueva, migrar datos de un servicio con estado (Vaultwarden, n8n+Postgres, Uptime
>   Kuma), o apagar/reiniciar algo en produccion, avisa antes y explica que se va a interrumpir.
> - Los LXC nuevos van **unprivileged** siempre que sea posible; VM vs LXC por host ya esta decidido, no lo
>   re-evalues (ver tabla "VM vs LXC" en `REORGANIZACION_RACK.md`).
> - Homepage (`core`, `services.yaml`) esta detras de Cloudflare Tunnel en `home.oscarlab.com.ar` — se renderiza
>   dinamicamente, no hace falta purgar cache al editar `services.yaml`; si tocas `custom.css`/`custom.js` si hace
>   falta purgar.
> - Cualquier edicion a `services.yaml` de Homepage: nunca con `sed -i` dentro del contenedor. Traer el archivo,
>   editar local, validar YAML, subir por `base64 | ssh ... | base64 -d`, reiniciar el contenedor, dejar backup del
>   archivo anterior en el propio host.
> - **No apagues las herramientas de monitoreo redundantes** (Beszel, Glances, ProxMenux Monitor, MySpeed) — la
>   politica acordada es esperar datos reales en Grafana antes de decidir, funcion por funcion.
> - La Fase 2 (VM `apps` como worker de k3s) es un trabajo aparte, no la empieces salvo que el usuario lo pida
>   explicitamente — por ahora `ci-demo` y `oscar-led-controller` se quedan en el cluster `k3s` tal cual estan.
> - La seccion "Documentacion a actualizar" de `REORGANIZACION_RACK.md` dice exactamente que pagina de `docs/`
>   tocar en cada paso — no reescribas las ~80 paginas que mencionan nombres viejos de una sola vez, solo las que
>   correspondan al paso que estas ejecutando en ese momento (la documentacion debe describir lo que ya paso, no lo
>   que todavia no).
>
> Segui el orden de "Pasos de ejecucion" de `REORGANIZACION_RACK.md`, empezando por el paso 1 (renombrar las Pi).
> Commiteá con mensajes en español explicando el porqué, no solo el qué, siguiendo el estilo ya usado en el
> historial de `oscar-homelab` y `oscar-gitops`. Actualizá este archivo marcando cada paso como resuelto a medida
> que lo completes.
