---
title: Fondo aurora de la pantalla
sidebar_position: 8
---

# Fondo aurora de la pantalla (`oscar-aurora`)

**Estado:** primera versión funcionando (2026-09-26), **sin desplegar** en el kiosco. Vive en `apps/oscar-aurora/` (repositorio git local, todavía sin remoto en Forgejo), con un `README.md` completo que es la fuente de verdad; esta página es el resumen.

Fondo animado **procedural** para la [pantalla del Dell](./dell-7060.md): aurora y estrellas hechas con WebGL (Three.js + GLSL), sin imágenes ni video, a 1280×720 y fullscreen en Chromium. Es solo el *background*: la UI de O.S.C.A.R. (hora, fecha, clima, estado) va encima. La referencia visual es la lámina `bg-aurora.png` (variantes por momento del día), guardada en `apps/oscar-aurora/reference/`.

## Fidelidad a la referencia

Se comparó lado a lado con cada panel de la lámina. Coincide en luminosidad (noche 0,12 vs 0,11 de la referencia, día 0,27 vs 0,31, etc.), paletas, densidad de estrellas, cresta diagonal con base irregular, rayos finos altos, abanico en V a la derecha y resplandor de horizonte en amanecer/atardecer. **No es idéntico**: a la referencia le falta parecerse en volumen (nubes de gas), nitidez de los rayos y brillo blanco-magenta en los núcleos. Es una aproximación procedural, no una copia.

## Qué hace

- **Ciclo horario continuo** con cinco paletas (madrugada 00–06, amanecer 06–09, día 09–17, atardecer 17–20, noche 20–24). Alrededor de cada cambio se mezcla durante 60 minutos (30 antes y 30 después): colores, brillo, velocidad e intensidad, nunca a saltos.
- **Deep Night** opcional (manual o por horario): brillo ×0.35, velocidad ×0.4, estrellas ×0.5, aurora ×0.4. La pantalla "duerme" pero sigue funcionando.
- **Movimiento muy lento**: una captura parece estática y a los 10–20 s se nota que las ondas se movieron. Estrellas en tres capas, con titileo raro y sutil.
- **Dos capas** preparadas: *hora del día* + *estado del sistema* (`NORMAL`, `PROCESSING`, `DEPLOYING`, `SUCCESS`, `WARNING`, `ERROR`, `STANDBY`). Los estados existen pero todavía son neutros; se pueden ir activando sin tocar las paletas.
- Paletas y parámetros son **datos** (`palettes.js`, `config.js`), no están en el shader. En `npm run dev` hay un panel de debug para forzar cada momento, simular la hora y ajustar intensidad, velocidad, brillo, estrellas y ruido; no existe en el build.

## Cómo probarlo

```bash
cd apps/oscar-aurora
export NPM_CONFIG_USERCONFIG=/dev/null        # el ~/.npmrc de la Mac apunta a un registry privado con token vencido
npm install --registry https://registry.npmjs.org/
npm run dev                                    # http://localhost:5173 (?palette=atardecer, ?hour=8.5, ?deep=1)
```

## Pendiente

- **Medir en el Dell.** La GPU integrada (Intel UHD 630) es mucho más lenta que la de la Mac de desarrollo (~4,6 ms por cuadro a 1280×720 allá). Hay calidad adaptable (`renderScale` baja sola si no se llega a ~50 fps), pero hay que ver cómo anda en el kiosco real antes de instalarlo.
- **Integrarlo en la UI del kiosco** (hoy el kiosco muestra Homepage). El README explica cómo: canvas `z-index: -1`, API `window.OscarAurora`.
- **Conectar `SystemState` con la tira LED** (`GET led.oscar.home/state`) si se quiere que el fondo refleje `deploying`/`critical`, etc.
- Subirlo a un repositorio de Forgejo (`oscar-aurora`).
- La luminosidad de amanecer/día/atardecer sigue la referencia y es mayor que "oscuro"; si se prefiere más oscuro, se baja `brightness` de esas paletas.
