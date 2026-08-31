---
title: Lab 03 · DNS y reverse proxy
sidebar_position: 4
---

# Lab 03 · DNS y reverse proxy

## Objetivo

Crear un nombre DNS interno para una app y publicarla detrás del proxy interno con TLS si la PKI elegida lo permite.

## Preparación

- usar namespace/VM de laboratorio;
- no utilizar credenciales productivas innecesarias;
- verificar que existe una forma de limpiar todos los recursos;
- capturar baseline antes de empezar.

## Ejecución

1. documentar estado inicial;
2. realizar el cambio;
3. observar métricas/logs/eventos;
4. provocar al menos una falla controlada;
5. recuperar;
6. limpiar recursos;
7. escribir qué aprendimos.

## Criterio de éxito

Acceder por nombre sin recordar IP/puerto y comprender el flujo DNS → proxy → app.

## Evidencia

Guardar en el issue/PR del lab:

- comandos relevantes;
- screenshot/dashboard si aporta;
- tiempos;
- problema encontrado;
- mejora propuesta para la guía.
