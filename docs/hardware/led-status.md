---
title: Indicador LED de estado
sidebar_position: 7
---

# Indicador LED de estado (`oscar-led-controller`)

**Estado:** Actual — mapea los estados de O.S.C.A.R. (`healthy`, `critical`, `deploying`, `backup`, ...) a color y animación en la tira WS2812B real, de forma provider-agnóstica. Desde el 2026-09-25 corre en el worker `apps` de k3s con CI/CD real (build + push a Nexus, sin `pullPolicy: Never`).

No vive en `docs/` ni en `inventory/`: es una app propia dentro del monorepo, en [`apps/oscar-led-controller/`](https://github.com/rudemex/oscar-homelab/tree/develop/apps/oscar-led-controller), con su propio `package.json`, tests, Docker y un `README.md` extenso que documenta la arquitectura completa (motor de efectos, layout físico de la tira, protocolo KLAP de Tapo investigado desde cero, etc.). Esta página es solo el resumen y el punto de entrada — la fuente de verdad real es ese README.

## Qué hace hoy

- API HTTP (NestJS + Swagger) y CLI que controlan los estados de O.S.C.A.R. (`healthy`, `critical`, `deploying`, `backup`, `argentina`, `gamer`, ...), cada uno con color y efecto propio (respiración, pulso, rampa, rainbow, sparkle, cometas espaciales sobre `MirrorZone`).
- Provider real: **WLED** sobre un ESP32, tira WS2812B de 190 LEDs — ver [Geometría LED](#geometría-real-190-leds-95-por-lado) más abajo. La abstracción `LedProvider` sigue siendo provider-agnóstica (hubo pruebas de concepto previas con Philips Hue y TP-Link Tapo, ya retiradas).
- Persistencia del último estado real entre reinicios, y un mecanismo de alertas temporales que vuelven al estado anterior (no siempre a `healthy`).
- Layout físico modelado para una instalación con **dos tramos espejados** de la tira (uno por lateral del rack, 95 LEDs cada uno) — `OscarLedLayout`/`MirrorZone` traducen "fila lógica" (0-94) a los dos LEDs individuales reales que le corresponden en cada lado, vía overrides `seg[].i` de WLED (no segmentos WLED nativos — el dispositivo tiene `maxseg: 32`, muy por debajo de 190).

## Geometría real: 190 LEDs, 95 por lado

Instalación real (2026-09-20): una cadena WLED de 190 LEDs, 95 por lado. Cada lado es un lazo alrededor del marco: 14 abajo (atrás→frente), 34 frente (sube), 14 arriba (frente→atrás), 34 atrás (baja). Arranca en el lado izquierdo (visto de frente, LED 0-94) y un cable la une al derecho (LED 95-189), en el **mismo sentido** — ningún lado se invierte. Reemplaza el diseño anterior (tira de 300 cortada al medio, lado derecho invertido).

## `rackStatus`: estado real de todo el rack, no solo de O.S.C.A.R. (2026-09-25)

Todo lo anterior refleja **un único estado global** (el de O.S.C.A.R. mismo). `rackStatus` es un efecto manual distinto (`POST /effects {"effect":"rackStatus"}`, o el botón **Rack** en `/panel`) que pinta **toda la tira** — verde/rojo por host real del rack, no una fila puntual.

**Rediseñado (2026-09-25) tras ver la primera versión en vivo**: usa los 190 LEDs, no un grupo de filas cerca de un extremo. Cada host de `apps/oscar-led-controller/src/core/rackStatus/rackTargets.ts` — Proxmox, las 8 VMs/LXC del Dell y las 2 Raspberry Pi — recibe una **banda de filas `MirrorZone` de tamaño parejo**, calculada en runtime a partir de `layout.mirrorZoneCount` y la cantidad de targets (agregar/sacar un host redimensiona todo solo, sin tocar números a mano). El orden de la lista es de **dependencia**, no de posición física exacta: casi todo (Proxmox + 8 VMs/LXC) vive en el mismo Dell OptiPlex de U7 del rack, así que alinear por altura real no aportaría información.

Chequeo TCP puro (puerto 22 en las VMs/LXC/Pi, 8006 en Proxmox), sin exporters ni Prometheus de por medio, cada 15 s por defecto (`pollIntervalMs` configurable en el body). Una banda "arriba" queda fija y calma — misma filosofía que la respiración lenta de `healthy` — y una banda "caída" pulsa rápido, mismo registro de urgencia que el beacon de `critical` (reusando `dimHexColor`, el mismo primitivo de color de la cola del cometa de `mirrorSpin` — los efectos de alto nivel ya construidos no sirven tal cual acá porque todos animan un único estado sobre toda la tira, no N bandas independientes a la vez). Mientras todo está sano repinta solo al ritmo del poll (sin spam de HTTP); en cuanto algo cae, pasa a repintar cada 250 ms para que el pulso se vea fluido.

Es un efecto manual como `mirrorBlock`/`mirrorSparkle`: reemplaza lo que se ve en la tira hasta que algo lo cancele (`DELETE /effects/current`, o cualquier `POST /state/:state`), pero nunca toca `OscarState` ni la persistencia — es una vista sobre el resto de la infraestructura, no un estado propio de O.S.C.A.R.

## Código fuente y despliegue

El código del controlador vive en Forgejo: **`http://git.oscar.home/mdelgado/oscar-led-controller`** (repo privado, rama `main`; NestJS + WLED, ~60 archivos, con su propio README). Hasta el 2026-09-21 estaba **solo en el disco local**, sin ningún respaldo; ahora `apps/` está en el `.gitignore` de este repo de documentación para no mezclar las dos cosas.

**CI/CD real desde el 2026-09-25** (antes era manual, imagen importada a mano al containerd de `k3s01` con `pullPolicy: Never`): Forgejo Actions construye la imagen, corre `yarn verify` (lint + typecheck + tests unitarios + e2e + build) y la sube a Nexus (`192.168.0.151:8082/oscar-led-controller`, tag = SHA del commit). El deploy sigue siendo manual (`DEPLOY: 'false'` en el workflow): se actualiza `image.tag` en el `values.yaml` de [`oscar-gitops`](../servicios/argocd.md) y Argo CD sincroniza. Corre en el worker `apps` (no en el control-plane `k3s`), con `nodeSelector`. Suite de tests: 89/89 verdes.

## Panel táctil (2026-09-21)

El controlador tiene una página `/panel` con un botón grande por estado (Normal, Aurora, Noche, Argentina, Gamer, Pensando, Desplegando, Backup, Arrancando, Recuperando, Éxito, Aviso, Degradado, Crítico, Mantenimiento y Apagar), pensada para la [pantalla táctil del Dell](./dell-7060.md#pantalla-táctil-con-homepage-2026-09-21). La tarjeta *OSCAR LED Controller* de Homepage apunta a `https://led.oscarlab.com.ar/panel`; antes llevaba a la raíz de la API, que solo devuelve un JSON (`{"service":"oscar-led-controller","status":"ok"}`). El Swagger sigue en `/api`.

## Hardware real: WS2812B + ESP32 + WLED

La tira física es WS2812B, direccionable LED por LED, controlada por un ESP32 corriendo [WLED](https://kno.wled.ge/) (`WledProvider` en el código, único provider activo hoy — las pruebas de concepto anteriores con Philips Hue y TP-Link Tapo, sin control por LED individual, quedaron retiradas). `ZoneCapableProvider`/`MultiZoneCapableProvider` pintan LEDs individuales vía overrides `seg[].i` de la API de WLED, no vía sus segmentos nativos (el firmware tiene `maxseg: 32`, muy por debajo de los 190 LEDs reales).

## Integración con el resto de O.S.C.A.R.

El estado de O.S.C.A.R. (`OscarState`) se sigue cambiando manualmente (`POST /state/:state`, CLI, o un script que envuelve un deploy). El punto de extensión para que Proxmox/Prometheus/Grafana/Home Assistant/CI-CD/agentes de IA disparen cambios de estado automáticamente ya existe (`setState(state, { source, reason })`) pero **ninguna integración real está conectada todavía** para `OscarState`. El propio README trae un ejemplo listo de automatización desde Home Assistant vía `rest_command`.

La única integración automática real hoy es `rackStatus` (ver arriba): repintado periódico por TCP, sin depender de ningún sistema externo (ni Prometheus ni Kuma) — deliberado, para no acoplar esta feature a un stack de observabilidad que todavía no existe.

## Dónde profundizar

Todo lo demás — cómo emparejar el Hue Bridge, cómo funciona el protocolo KLAP de Tapo (con el detalle de ingeniería inversa real, no un resumen), el modelo completo de `MirrorZone`, los 8 efectos espaciales, el catálogo completo de `POST /effects`, por qué se compila con Rspack/SWC en vez de `tsx`/esbuild — está en `apps/oscar-led-controller/README.md`. Es intencionalmente un documento técnico distinto a esta guía: más cercano a un ADR + bitácora de ingeniería inversa que a documentación de usuario.
