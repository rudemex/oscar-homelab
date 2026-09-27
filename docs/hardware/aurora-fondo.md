---
title: Fondo aurora de la pantalla
sidebar_position: 8
---

# O.S.C.A.R. Aurora — NIGHT V1

**Estado (2026-09-26):** V1 nocturna implementada y medida en el Dell, pendiente de aprobación visual en pantalla.
**Sin instalar en el kiosco.** Código privado: [oscar-aurora](http://git.oscar.home/mdelgado/oscar-aurora).
Clon local independiente en `apps/oscar-aurora/`.

Para continuar, leer [HANDOFF.md](http://git.oscar.home/mdelgado/oscar-aurora/src/branch/main/HANDOFF.md) y
[README.md](http://git.oscar.home/mdelgado/oscar-aurora/src/branch/main/README.md), ambos en la raíz del repo.
Los enlaces requieren acceso a la red interna.

## Alcance aprobado para desarrollar

La instrucción vigente concentra el trabajo en **NIGHT**: cielo negro/azul oscuro, muchas estrellas y aurora procedural
violeta, azul y cyan. La referencia confirmada es `reference/ref-aurora.png`; se usa para comparar composición,
**nunca se carga como textura ni se anima la imagen**.

La escena tiene cinco capas con distintas profundidades: diagonal violeta principal, cinta cyan inferior, velo violeta bajo,
capa lejana a la izquierda y pliegue ascendente derecho integrado. Shader GLSL con ruido multiescala, domain warping y fibras verticales;
HDR, tone mapping y bloom suave configurable. Three.js y Vite, sin framework de UI.

Las estrellas ocupan **toda la pantalla**, permanecen fijas y titilan de forma visible. El 90 % se distribuye uniformemente;
el resto aporta un acento tenue arriba a la izquierda. Se conservan a resolución completa al bajar la calidad de la aurora.

Tras aprobar el realismo de la base, el usuario pidió **movimiento y cambios de color más visibles**, cortes suaves,
estrellas animadas y una curva ascendente en lugar de la V aislada. Se aumentó la velocidad a 0,24, se agregó mezcla
cromática local y titileo configurable. Las cintas ahora se superponen con extremos transparentes.

Horarios, otras paletas, Deep Night, estados del sistema e integraciones quedaron fuera del arranque de esta V1.
Los módulos antiguos siguen inactivos en el repo. Primero se aprueba NIGHT; las variantes vendrán después.

## Probar y calibrar

```bash
cd apps/oscar-aurora
NPM_CONFIG_USERCONFIG=/dev/null npm install --registry https://registry.npmjs.org/
npm run dev
```

El panel dev permite ajustar velocidad, intensidad, escala, warp, cortinas, brillo, saturación, cantidad/brillo/titileo de
estrellas y fuerza/radio/umbral del bloom. Tecla **D** para ocultarlo; `?panel=0` evita montarlo.
`?time=0`, `?time=10`, etc. fijan el tiempo para comparar capturas. El build de producción no incluye panel.
Los parámetros y colores están en `src/config.js`; canvas fullscreen sin scroll, objetivo 1280×720.

## Verificación de la primera NIGHT (histórico)

- Cero errores de consola, GLSL o warnings de Three.js en la prueba de Chrome.
- Capturas 1280×720 comparadas contra la referencia. Luminosidad media 0,142 frente a 0,127;
  casi negro en 29,1 % de píxeles frente a 30,1 %. La referencia conserva micropliegues más complejos.
- Diferencia media RGB entre capturas a 1 / 10 / 30 s: **0,31 / 2,31 / 5,61 sobre 255**.
- Estrellas en todas las celdas de una cuadrícula 4×3: entre 1.034 y 1.766 por celda.
- Resize comprobado a 1024×768, 720×1280, 1600×720 y 1280×720, sin scroll ni bandas vacías de estrellas.

**Dell 7060, Intel UHD 630 real, Chromium 154, headless con EGL surfaceless:**

| Caso | FPS promedio | Intervalo p95 | Canvas | Aurora HDR |
|---|---|---|---|---|
| Aurora a resolución fija 0,7 | 59,5 | 16,7 ms | 1280×720 | 896×504 |
| Calidad adaptable desde 0,7 | 59,6 | 16,8 ms | 1280×720 | 896×504 |

Se midieron 30 s por caso después del calentamiento; la adaptación no necesitó bajar la resolución.
El kiosco y las VMs siguieron funcionando. Son medidas de cadencia headless con GPU real: todavía falta verificar
presentación en Wayland y funcionamiento prolongado en la [pantalla del Dell](./dell-7060.md).

Scripts y método: `apps/oscar-aurora/scripts/`. Datos y capturas: `results/night-v1/` y `results/night-v1-dell/` en ese repo.
La medición del shader anterior (18,8 FPS a escala completa, 53,5 al mínimo) queda como histórico; no describe la NIGHT actual.

## Revisión de movimiento y continuidad

Capturas en `results/night-v2/`: diferencia media RGB a 1 / 10 / 30 s de **1,45 / 9,26 / 16,53 sobre 255**.
Cero errores de consola/GLSL; resize y cobertura estelar completos; panel ampliado a 17 controles.
La aprobación del realismo corresponde a la base anterior; falta revisar visualmente esta última iteración.

## Próximo paso

Revisar la NIGHT actual en la pantalla física y calibrar la fidelidad visual antes de agregar variantes o integraciones.
El kiosco sigue mostrando Homepage. El fondo hermano [O.S.C.A.R. Core](./oscar-core-fondo.md) es un proyecto independiente.
