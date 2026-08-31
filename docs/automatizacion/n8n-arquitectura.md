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
n8n
├── PostgreSQL
├── encryption key respaldada
├── webhooks selectivos
└── backup de workflows/DB
```

## Workflows objetivo

- resumen diario de salud;
- aviso de backup fallido;
- inventario de hosts;
- clasificación de alertas con IA;
- actualización controlada de documentación/inventario;
- tareas Home Assistant no críticas.
