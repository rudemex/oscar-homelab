---
title: Indicador LED de estado
sidebar_position: 7
---

# Indicador LED de estado (`oscar-led-controller`)

**Estado:** Actual (código) — mapea los estados de O.S.C.A.R. (`healthy`, `critical`, `deploying`, `backup`, ...) a color y animación en una luz inteligente, de forma provider-agnóstica.

No vive en `docs/` ni en `inventory/`: es una app propia dentro del monorepo, en [`apps/oscar-led-controller/`](https://github.com/rudemex/oscar-homelab/tree/develop/apps/oscar-led-controller), con su propio `package.json`, tests, Docker y un `README.md` extenso que documenta la arquitectura completa (motor de efectos, layout físico de la tira, protocolo KLAP de Tapo investigado desde cero, etc.). Esta página es solo el resumen y el punto de entrada — la fuente de verdad real es ese README.

## Qué hace hoy

- API HTTP (NestJS + Swagger) y CLI que controlan trece estados de O.S.C.A.R., cada uno con color y efecto propio (respiración, pulso, rampa, rainbow, estático).
- Provider intercambiable por variable de entorno (`LED_PROVIDER`), sin tocar la lógica de efectos: **Philips Hue** (prueba de concepto original) o **TP-Link Tapo** (cinta L930-5, protocolo KLAP no oficial).
- Persistencia del último estado real entre reinicios, y un mecanismo de alertas temporales que vuelven al estado anterior (no siempre a `healthy`).
- Layout físico ya modelado para una instalación con **dos tramos espejados** de la tira (uno por lateral del rack) — `OscarLedLayout`/`MirrorZone` traducen "fila lógica" a los dos segmentos eléctricos reales que le corresponden.

## Panel táctil (2026-09-21)

El controlador tiene una página `/panel` con un botón grande por estado (Normal, Aurora, Noche, Argentina, Gamer, Pensando, Desplegando, Backup, Arrancando, Recuperando, Éxito, Aviso, Degradado, Crítico, Mantenimiento y Apagar), pensada para la [pantalla táctil del Dell](./dell-7060.md#pantalla-táctil-con-homepage-2026-09-21). La tarjeta *OSCAR LED Controller* de Homepage apunta a `https://led.oscarlab.com.ar/panel`; antes llevaba a la raíz de la API, que solo devuelve un JSON (`{"service":"oscar-led-controller","status":"ok"}`). El Swagger sigue en `/api`.

## Sobre el hardware final: WS2812B + ESP32

El objetivo físico es una tira WS2812B direccionable por LED controlada por un ESP32 (probablemente vía [WLED](https://kno.wled.ge/)) — eso es lo que permitiría de verdad pintar segmentos individuales (`ZoneCapableProvider` en el código). **Todavía no existe ese provider**: hoy el controlador corre contra Hue o Tapo (luces/tiras inteligentes convencionales, no direccionables por LED individual) mientras se termina de validar la arquitectura de efectos. Cuando exista el `WledProvider`, se conecta al mismo `EffectEngine` sin tocar `OscarState` ni la API — es justamente el punto de la separación `LedProvider` ↔ `EffectEngine` que ya está construida.

## Integración con el resto de O.S.C.A.R.

Hoy el estado se cambia manualmente (`POST /state/:state`, CLI, o un script que envuelve un deploy). El punto de extensión para que Proxmox/Prometheus/Grafana/Home Assistant/CI-CD/agentes de IA disparen cambios de estado automáticamente ya existe (`setState(state, { source, reason })`) pero **ninguna integración real está conectada todavía** — es exactamente el mismo patrón "Objetivo, no inventado" del resto de esta guía. El propio README trae un ejemplo listo de automatización desde Home Assistant vía `rest_command`.

## Dónde profundizar

Todo lo demás — cómo emparejar el Hue Bridge, cómo funciona el protocolo KLAP de Tapo (con el detalle de ingeniería inversa real, no un resumen), el modelo completo de `MirrorZone`, los 8 efectos espaciales, el catálogo completo de `POST /effects`, por qué se compila con Rspack/SWC en vez de `tsx`/esbuild — está en `apps/oscar-led-controller/README.md`. Es intencionalmente un documento técnico distinto a esta guía: más cercano a un ADR + bitácora de ingeniería inversa que a documentación de usuario.
