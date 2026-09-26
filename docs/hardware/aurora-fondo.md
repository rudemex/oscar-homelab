---
title: Fondo aurora de la pantalla
sidebar_position: 8
---

# Fondo aurora de la pantalla (`oscar-aurora`)

**Estado:** primera versión funcionando (2026-09-26), **sin desplegar** en el kiosco. Vive en `apps/oscar-aurora/` (repositorio git local, todavía sin remoto en Forgejo), con un `README.md` completo que es la fuente de verdad; esta página es el resumen.

Fondo animado para la [pantalla del Dell](./dell-7060.md): WebGL (Three.js + GLSL) a 1280×720 y fullscreen en Chromium. Es solo el *background*: la UI de O.S.C.A.R. (hora, fecha, clima, estado) va encima.

**Cómo está hecho (2026-09-26).** Las versiones anteriores generaban la aurora de forma completamente procedural y no se parecían a la referencia. El actual **copia la imagen de referencia** (`ref-aurora.png`): un script (`tools/make_plate.py`) le quita las estrellas y la descompone en intensidad, "rol de color" y blancura (una *placa* de datos); el shader la vuelve a pintar con la paleta de cada momento del día (tomadas de la lámina `bg-aurora.png`) y la **anima** con balanceo lento, destellos que suben por los rayos, ondas de brillo y corrimiento del color. Las estrellas van aparte: procedurales, discretas y animadas (titilan y el campo gira imperceptiblemente).

## Qué hace

- **Ciclo horario continuo** con cinco paletas (madrugada 00–06, amanecer 06–09, día 09–17, atardecer 17–20, noche 20–24). Alrededor de cada cambio se mezcla durante 60 minutos (30 antes y 30 después): colores, brillo, velocidad e intensidad, nunca a saltos.
- **Deep Night** opcional (manual o por horario): brillo ×0.35, velocidad ×0.4, estrellas ×0.5, aurora ×0.4. La pantalla "duerme" pero sigue funcionando.
- **Cielo oscuro y estrellas discretas**; movimiento lento (una captura parece estática y a los 10–20 s se nota).
- **Dos capas** preparadas: *hora del día* + *estado del sistema* (`NORMAL`, `PROCESSING`, `DEPLOYING`, `SUCCESS`, `WARNING`, `ERROR`, `STANDBY`). Los estados existen pero todavía son neutros.
- Paletas y parámetros son **datos** (`palettes.js`, `config.js`), no están en el shader. En `npm run dev` hay un panel de debug; no existe en el build.

## Cómo probarlo

```bash
cd apps/oscar-aurora
export NPM_CONFIG_USERCONFIG=/dev/null        # el ~/.npmrc de la Mac apunta a un registry privado con token vencido
npm install --registry https://registry.npmjs.org/
npm run dev                                    # http://localhost:5173 (?palette=atardecer, ?hour=8.5, ?deep=1)
```

## Pendiente

- **Medir en el Dell.** La GPU integrada (Intel UHD 630) es mucho más lenta que la de la Mac de desarrollo, donde no se pudo medir con precisión. El shader es liviano (2 lecturas de textura y unas 20 de ruido por píxel) y hay calidad adaptable (`renderScale` baja sola si no se llega a ~50 fps), pero hay que verlo en el kiosco real antes de instalarlo.
- **Integrarlo en la UI del kiosco** (hoy el kiosco muestra Homepage). El README explica cómo: canvas `z-index: -1`, API `window.OscarAurora`.
- **Conectar `SystemState` con la tira LED** (`GET led.oscar.home/state`) si se quiere que el fondo refleje `deploying`/`critical`, etc.
- Subirlo a un repositorio de Forgejo (`oscar-aurora`).
- La forma es fija (la de la imagen); si se quisieran varias composiciones, hay que generar más placas.
