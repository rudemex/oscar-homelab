---
title: n8n en O.S.C.A.R.
sidebar_position: 1
---

# n8n

n8n es la capa de orquestación de workflows entre sistemas. No reemplaza scripts simples, systemd timers o Kubernetes CronJobs cuando una tarea lineal se resuelve mejor con esas herramientas.

## Casos ideales

- integra varias APIs;
- necesita retries/ramas;
- requiere notificación;
- combina IA con reglas determinísticas;
- recibe webhooks;
- necesita aprobación humana.

## Arquitectura de producción doméstica

```text
n8n (modo queue, desde 2026-09-23)
├── n8n main       — UI + webhooks, encola ejecuciones
├── n8n worker     — toma las ejecuciones de la cola (concurrency 10)
├── Redis          — cola (BullMQ)
├── PostgreSQL     — datos: workflows, credenciales, ejecuciones
├── encryption key respaldada (compartida entre main y worker)
├── webhooks selectivos
└── backup de workflows/DB
```

Corre en `automation` (`/srv/oscar/apps/n8n/`, ver [estado actual](../arquitectura/estado-actual.md)). El modo *queue* separa la recepción de triggers/webhooks (proceso `main`) de la ejecución real de los workflows (proceso `worker`) — un workflow pesado no bloquea la UI ni la llegada de nuevos webhooks, y agregar más workers después no requiere tocar `main`.

## Workflows objetivo

- resumen diario de salud;
- aviso de backup fallido;
- inventario de hosts;
- clasificación de alertas con IA;
- actualización controlada de documentación/inventario;
- tareas Home Assistant no críticas.
