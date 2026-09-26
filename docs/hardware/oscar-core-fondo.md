---
title: Fondo O.S.C.A.R. Core
sidebar_position: 9
---

# Fondo O.S.C.A.R. Core (`oscar-core`)

**Estado:** primera versión funcionando (2026-09-26), **sin desplegar** en el kiosco. Código en Forgejo: **`http://git.oscar.home/mdelgado/oscar-core`** (privado); clon de trabajo en `apps/oscar-core/`, con un `README.md` completo que es la fuente de verdad. Esta página es el resumen.

Segundo fondo animado para la [pantalla del Dell](./dell-7060.md), hermano de la [aurora](./aurora-fondo.md): el **O.S.C.A.R. Core**, una estructura de energía formada por anillos, filamentos y partículas alrededor de un **centro negro** (donde después irá la UI). **100 % procedural** en WebGL (Three.js + GLSL), sin imágenes ni videos; la referencia visual es la lámina `bg-nucleo.png` (seis variantes por momento del día), guardada en `apps/oscar-core/reference/`. Es solo el *background*: la UI de O.S.C.A.R. va encima.

## Qué hace

- **Capas independientes**: 3–5 anillos de energía (contorno irregular, tramos apagados, giro muy lento en sentidos distintos), hasta 36 filamentos que aparecen y se apagan por opacidad (nunca parpadean), puntos de energía que recorren los filamentos, partículas (órbita, libres, micro y chispas) y resplandor.
- **Respiración orgánica** (ciclo ~6,5 s): combina brillo, glow, radio, partículas y filamentos con desfases propios; no es un simple escalar arriba y abajo.
- **Ciclo horario continuo** con las cinco paletas de la referencia y mezcla de ±30 min alrededor de cada cambio; **Deep Night** (brillo ×0.35, partículas ×0.30, giro ×0.30, filamentos ×0.40) que sigue respirando.
- **Siete estados del sistema**, separados de la hora: `NORMAL`, `PROCESSING`, `DEPLOYING` (pulsos en secuencia y anillos que se alinean), `SUCCESS` (pulso verde de centro a afuera; vuelve solo), `WARNING` (ámbar), `ERROR` (rojo, latido lento) y `STANDBY`. Nunca strobe ni flashes.
- Los shaders no toman decisiones de negocio: la hora y los estados solo modifican uniforms. Paletas y parámetros son datos (`palettes.js`, `config.js`). Panel de debug solo en `npm run dev`.

## Cómo probarlo

```bash
cd apps/oscar-core
export NPM_CONFIG_USERCONFIG=/dev/null        # el ~/.npmrc de la Mac apunta a un registry privado con token vencido
npm install --registry https://registry.npmjs.org/
npm run dev                                    # http://localhost:5173 (?palette=atardecer, ?state=SUCCESS, ?hour=8.5, ?deep=1)
```

## Pendiente

- **Medir en el Dell.** La GPU integrada (Intel UHD 630) es mucho más lenta que la de la Mac de desarrollo, donde no se pudo medir con precisión. El fragment shader recorre hasta 5 anillos (con 3 hilos cada uno) y 36 filamentos por píxel; hay calidad adaptable (`renderScale` baja sola si no se llega a ~50 fps) y se puede bajar `filamentCount`, pero hay que verlo en el kiosco real antes de instalarlo.
- **Integrarlo en la UI del kiosco** (hoy muestra Homepage). El README explica cómo: canvas `z-index: -1` y API `window.OscarCore`. En la referencia el Core está a la derecha y la UI a la izquierda; por defecto está centrado (`coreCenter`).
- **Conectar el estado del sistema con la tira LED** (`GET led.oscar.home/state`) si se quiere que el Core refleje `deploying`, `critical`, etc.
- Es una aproximación: la referencia tiene aún más densidad de filamentos (con nodos brillantes en las intersecciones) y una nube de partículas más marcada a la izquierda; el bloom es analítico, no un postproceso real.
