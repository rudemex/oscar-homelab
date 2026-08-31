---
title: IA local vs remota
sidebar_position: 5
---

# IA local y remota

## Realidad del hardware actual

El único cómputo serio de O.S.C.A.R. hoy es el Dell OptiPlex 7060 Micro: **Intel Core i7 de 8ª generación, sin GPU dedicada**. Eso condiciona la conversación de forma concreta, no abstracta:

- inferencia local corre **100% sobre CPU** (integrada Intel UHD 630 no es utilizable para inferencia LLM de forma práctica);
- en la práctica esto limita a modelos pequeños cuantizados (del orden de 3B–8B parámetros, cuantización q4), con latencia de varios segundos por respuesta y sin margen para servir más de una consulta a la vez;
- ese mismo Dell también hospeda Proxmox y el resto de los servicios core — dedicarle CPU a inferencia compite directamente con el resto de la plataforma, no es un recurso "sobrante";
- una GPU dedicada (incluso una de gama baja) es hardware **no adquirido y no planificado** en el inventario actual — cualquier plan que asuma "correr un modelo capaz localmente" es aspiracional, no un plan ejecutable hoy.

Esto no descarta IA local — la vuelve una elección deliberada de alcance chico (clasificación, resumen corto, RAG sobre pocos documentos), no de "asistente general" comparable a un modelo remoto.

## Local

Ventajas:

- datos permanecen en casa;
- funciona sin proveedor externo;
- excelente laboratorio para entender cuantización, contexto y límites reales de inferencia en CPU.

Costos, concretos para este hardware:

- CPU compartida con el resto de O.S.C.A.R. (no hay margen para modelos "grandes" sin degradar otros servicios);
- modelos limitados a ~3B–8B parámetros cuantizados;
- latencia de segundos por respuesta, no apta para uso interactivo intensivo;
- consumo eléctrico sostenido durante la inferencia;
- mantenimiento de versiones de modelo/runtime (Ollama).

## Remota

Ventajas:

- modelos más capaces (razonamiento, contexto largo, código);
- no compite por CPU/RAM con el resto de O.S.C.A.R.;
- mejor para tareas complejas — en este hardware, es la única opción realista para eso.

Costo principal: los datos enviados salen del homelab. Antes de mandar logs/configuraciones hay que sanitizar secretos y entender política de datos del proveedor.

## Diseño híbrido (recomendado dado el hardware actual)

Dado que el Dell no tiene GPU, el diseño híbrido no es una preferencia estética sino la única combinación viable hoy:

- **local** (Ollama + modelo pequeño): clasificación simple, extracción de campos, RAG sobre pocos documentos, tareas donde la latencia de segundos es aceptable y el dato no debe salir de casa;
- **remota** (Claude/OpenAI vía API): diagnóstico complejo, razonamiento sobre múltiples fuentes (logs + métricas + config), y cualquier interacción donde la calidad de respuesta importa más que la latencia.

Si en el futuro se suma una GPU dedicada (fuera del inventario actual — sería una decisión de hardware nueva, no una mejora del Dell existente), esta recomendación se revisita explícitamente en lugar de asumir que "más adelante alcanza".
