# Reorganización del rack

**Estado:** arquitectura objetivo definida y aprobada (2026-09-22). Nada de la parte nueva (VMs/LXC nuevas,
migraciones de servicios) está ejecutado todavía — sí está hecho el stack de observabilidad en `pinode02`, y el
renombrado real de las Pi sigue pendiente de aplicar.

**Por qué existe:** meses de sesiones agregando cosas de a una dejaron herramientas repetidas midiendo lo mismo,
`core01` como cajón de sastre (borde de red + apps de usuario + automatización + monitoreo, todo junto), y un
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
│   │   └── n8n workers (arranca con 0-1)
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
│   ├── services                    [LXC nueva unprivileged, Dell]
│   │   ├── Vaultwarden
│   │   ├── SearXNG
│   │   └── DocuSeal
│   │
│   └── apps                        [diferido — ver Fase 2, será VM/worker de k3s]
│       └── (futuro) ci-demo, oscar-led-controller, como worker del cluster k3s
│
└── SPECIAL PURPOSE
    ├── games                       [VM nueva, Dell — apagada salvo cuando se usa]
    │   ├── Minecraft
    │   └── CS2
    │
    └── lab                         [VM, Dell — ex lab01, reutilizada]
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
| core01 → **core** | 8GB | ~1,5GB | **4GB** | VM (existente) |
| devops01 → **devops** | 12GB | ~4,3GB | **6GB** | VM (existente) |
| k3s01 → **k3s** | 8GB | ~2GB | **4GB** | VM (existente) |
| lab01 → **lab** | 6GB | ~466MB | **2GB** | VM (existente, reutilizada) |
| — → **automation** | — | — | **4GB** | VM nueva |
| — → **services** | — | — | **2GB** | LXC unprivileged nueva |
| — → **games** | — | — | **6GB** (apagada salvo uso) | VM nueva |
| VM106 (HA) | 4GB | — | 4GB (sin cambios) | VM (existente) |

Total con todo prendido salvo `games` (que se enciende solo para jugar): **26GB de 31GB**, deja ~5GB de margen
para el propio host. Con `games` prendida sube a 32GB — al límite, por eso se recomienda mantenerla apagada salvo
uso activo (ya es el patrón actual con `lab01`).

**Recomendación adicional:** activar memory ballooning (`balloon: <min>`) en las VMs del Dell — hoy ninguna lo
tiene, así que Proxmox no puede reclamar RAM no usada de una VM para dársela a otra bajo presión.

## Migraciones necesarias

```text
core01
├── Homepage             → core (sin cambios funcionales)
├── NPM                  → core (sin cambios funcionales)
├── SMTP Relay           → core (sin cambios funcionales)
├── Vaultwarden          → services (nueva LXC) — migrar datos
├── n8n + Postgres       → automation (nueva VM) — migrar datos
├── Minecraft             → games (nueva VM)
├── Cloudflare Tunnel      → network (centralizar ahí, hoy vive en core01)
├── Portainer Server      → ELIMINAR
├── Beszel Server         → se queda (política de monitoreo: esperar datos)
├── Glances                → se queda (ídem)
└── MySpeed                → se queda en core (corrección respecto al diseño original)

devops01
├── Forgejo / Nexus / Infisical → devops (sin cambios funcionales, solo rename)
├── Portainer Agent              → ELIMINAR
└── Beszel Agent                  → se queda (política de monitoreo)

k3s01
├── Argo CD / Traefik / Headlamp / Infisical Operator → k3s (sin cambios funcionales, solo rename)
├── ci-demo / oscar-led-controller                      → se quedan en k3s (Fase 2 los mueve a `apps`)
└── SearXNG                                               → services (nueva LXC) — hoy corre en k3s01 vía Argo CD,
                                                             evaluar si migra a k8s-manifest en `services` o se
                                                             redeploya como contenedor Docker suelto

lab01
├── CS2         → games (nueva VM)
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
- **Al renombrar `core01`/`devops01`/`k3s01`/`lab01`:** `docs/hardware/dell-7060.md`,
  `docs/proxmox/crear-vm-core01.md` (posible rename de archivo), `docs/arquitectura/vision-general.md`,
  `docs/arquitectura/stack.md`, `docs/arquitectura/decisiones-arquitectonicas.md`, `docs/despliegues/indice.md`,
  y el resto que aparece en el grep de `core01|devops01|k3s01|lab01` sobre `docs/`.

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
   `core01`, que proxea por LAN hacia la Pi. Pendiente decidir en el paso 9 si se le da uso real al túnel
   `pinode01` o se da de baja.
3. ⚠️ **Parcial (2026-09-22).** Right-sizing de RAM en `core01`/`devops01`/`k3s01`/`lab01` según la tabla de arriba,
   antes de crear hosts nuevos. Aplicado con reboot uno por uno (sin hotplug/balloon configurado, el cambio de
   memoria no toma efecto en caliente), verificando servicios sanos antes de seguir con el siguiente:
   - ✅ `lab01`: 6→2GB, reiniciada, sana.
   - ✅ `core01`: 8→4GB, reiniciada, Homepage/NPM verificados, ~1,3GB en uso real de 3,8GB disponibles.
   - ✅ `devops01`: 6 horas sin jobs de CI corriendo verificado antes de reiniciar; 12→6GB, reiniciada, Forgejo
     verificado, todos los contenedores (Nexus, Infisical, forgejo-runner, Beszel-agent) arriba.
   - ❌ **`k3s01`: pendiente, sigue en 8GB sin tocar.** Se cortó la sesión acá — baja tensión real, el usuario pidió
     apagar todo OSCAR por precaución antes de un corte de luz. **Al retomar: chequear que Argo CD tenga sus
     aplicaciones `Synced`/`Healthy` antes de bajarle la memoria a 4GB y reiniciarla — es la más sensible de las
     cuatro (Traefik resuelve todo `*.oscar.home`, tarda más en volver por el propio arranque de k3s).**
4. Crear `automation` (VM), migrar n8n+Postgres desde `core01` con sus datos.
5. Crear `services` (LXC unprivileged), migrar Vaultwarden desde `core01` con sus datos; evaluar SearXNG y sumar
   DocuSeal.
6. Crear `games` (VM, apagada por defecto), mover Minecraft desde `core01` y CS2 desde `lab01`.
7. Renombrar `core01`→`core`, `devops01`→`devops`, `k3s01`→`k3s`, `lab01`→`lab` (vaciada de CS2).
8. Eliminar Portainer Server/Agent de todos los hosts.
9. Centralizar `cloudflared` en `network` (hoy hay instancias en `core01` y una dedicada en `pinode01`).
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

## Estado al momento de escribir esto (2026-09-22)

- ⚠️ **OSCAR está apagado (2026-09-22, a propósito).** Baja tensión real en la casa — el usuario pidió apagar todo
  por precaución antes de un corte de luz, en medio del paso 3 (right-sizing). Nada se perdió (no había backups ni
  jobs corriendo). **Al retomar: prender el Dell primero, después las 2 Pi, y verificar que todo vuelva sano antes
  de seguir con `k3s01`** (mismo primer paso que ya se hizo la vez anterior que se apagó todo).
- El SSD SATA de `Backups` del Dell se resolvió: `sda` (WD Green, interno SATA) es `Backups`, `sdb`
  (`FTM1TN325H`, el que venía fallando, ahora externo USB) es `Documentos`, y se sumó un tercer disco nuevo
  (SanDisk 1TB, externo USB) como `Storage` general sin uso fijo — ver `docs/arquitectura/estado-actual.md`.
- `oscar-gitops` (Forgejo, `mdelgado/oscar-gitops`, rama `main`) tiene: el control node de Ansible completo
  (`ansible/`), con el stack de observabilidad **ya desplegado y funcionando** en `pinode02` (Prometheus, Grafana,
  Blackbox HTTP), y el Speedtest exporter + Blackbox ICMP **preparados en el código pero sin desplegar**.
- **Paso 1 hecho (2026-09-22):** las Pi ya se llaman `network`/`monitor` a nivel de SO, `hosts.yml` de Ansible y la
  doc de `oscar-homelab` están al día. **Pendiente:** `git push` del commit `969feb8` en `oscar-gitops` — el clon
  de trabajo vive en un scratchpad fuera de este repo, y el push desde ahí quedó bloqueado por el clasificador de
  Claude Code ("Out-of-Place Publication"). Hay que pushearlo desde un checkout normal de `oscar-gitops`, o el
  usuario lo autoriza explícitamente.
- **Paso 2 hecho (2026-09-22):** Uptime Kuma migrado de `network` a `monitor`, con el ingress rule de Cloudflare
  corregido — ver detalle en el paso 2 de "Pasos de ejecución" y en `docs/servicios/uptime-kuma.md`.
- **Paso 3 parcial (2026-09-22):** right-sizing de RAM — `lab01`/`core01`/`devops01` ya en sus valores nuevos y
  verificados sanos; **`k3s01` pendiente** (sigue en 8GB), cortado por el apagado de emergencia de arriba. Retomar
  ahí, chequeando Argo CD antes de reiniciarla.
- El resto de la arquitectura nueva de este documento (VMs/LXC nuevas, migraciones restantes, rename de
  `core01`/`devops01`/`k3s01`/`lab01`) no está ejecutado todavía — sigue el orden de "Pasos de ejecución" de arriba.

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
