---
title: Fondo aurora de la pantalla
sidebar_position: 8
---

# Fondo aurora de la pantalla (`oscar-aurora`)

**Estado:** primera versión funcionando (2026-09-26), **sin desplegar** en el kiosco. Código en Forgejo: **`http://git.oscar.home/mdelgado/oscar-aurora`** (privado); clon de trabajo en `apps/oscar-aurora/`, con un `README.md` completo que es la fuente de verdad; esta página es el resumen.

Fondo animado para la [pantalla del Dell](./dell-7060.md): WebGL (Three.js + GLSL) a 1280×720 y fullscreen en Chromium. Es solo el *background*: la UI de O.S.C.A.R. (hora, fecha, clima, estado) va encima.

**Cómo está hecho (2026-09-26).** Aurora **100 % procedural**: sin imágenes ni texturas, todo se calcula en un shader con ruido que evoluciona en el tiempo. Un intento intermedio copiaba la imagen de referencia y la movía; se descartó porque se veía como una foto animada. De la referencia (`ref-aurora.png`) solo se tomó la **composición**, escrita como curvas medidas: una cinta principal en diagonal con rayos altos, una segunda cinta más baja, un abanico en "V" y nubes bajas. Cada cinta se dibuja como varias láminas con profundidad (rayos, pliegues, pulsos, cresta luminosa). Las paletas de cada momento del día salen de la lámina `bg-aurora.png`. Las estrellas van aparte: procedurales, discretas y animadas.

## Qué hace

- **Ciclo horario continuo** con cinco paletas (madrugada 00–06, amanecer 06–09, día 09–17, atardecer 17–20, noche 20–24). Alrededor de cada cambio se mezcla durante 60 minutos (30 antes y 30 después): colores, brillo, velocidad e intensidad, nunca a saltos.
- **Deep Night** opcional (manual o por horario): brillo ×0.35, velocidad ×0.4, estrellas ×0.5, aurora ×0.4. La pantalla "duerme" pero sigue funcionando.
- **Cielo oscuro y estrellas discretas**, con movimiento que se ve a simple vista (balanceo, pulsos y ondas de brillo); no es agresivo: es ambiental.
- **Dos capas** preparadas: *hora del día* + *estado del sistema* (`NORMAL`, `PROCESSING`, `DEPLOYING`, `SUCCESS`, `WARNING`, `ERROR`, `STANDBY`). Los estados existen pero todavía son neutros.
- Paletas y parámetros son **datos** (`palettes.js`, `config.js`), no están en el shader. En `npm run dev` hay un panel de debug; no existe en el build.

Hay un segundo fondo hermano: el [O.S.C.A.R. Core](./oscar-core-fondo.md).

## Cómo probarlo

```bash
cd apps/oscar-aurora
export NPM_CONFIG_USERCONFIG=/dev/null        # el ~/.npmrc de la Mac apunta a un registry privado con token vencido
npm install --registry https://registry.npmjs.org/
npm run dev                                    # http://localhost:5173 (?palette=atardecer, ?hour=8.5, ?deep=1)
```

## Pendiente

- **Medir en el Dell.** La GPU integrada (Intel UHD 630) es mucho más lenta que la de la Mac de desarrollo, donde no se pudo medir con precisión. El shader es pesado para una GPU integrada (hasta 7 cortinas por píxel, con salidas tempranas) y hay calidad adaptable (`renderScale` baja sola si no se llega a ~50 fps), pero hay que verlo en el kiosco real antes de instalarlo.
- **Integrarlo en la UI del kiosco** (hoy el kiosco muestra Homepage). El README explica cómo: canvas `z-index: -1`, API `window.OscarAurora`.
- **Conectar `SystemState` con la tira LED** (`GET led.oscar.home/state`) si se quiere que el fondo refleje `deploying`/`critical`, etc.
- La composición es una aproximación medida a mano sobre la referencia, no una copia; la forma general es fija y lo que cambia es la estructura interna.
