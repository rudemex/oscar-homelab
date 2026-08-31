---
title: Agente operador
sidebar_position: 4
---

# Agente operador

## Ejemplo: contenedor caído

1. alerta llega a n8n;
2. agente consulta Uptime Kuma;
3. consulta métricas del host;
4. busca logs recientes;
5. identifica si es falla aislada o de infraestructura;
6. si es servicio de laboratorio y la política lo permite, reinicia una vez;
7. valida healthcheck;
8. registra resultado;
9. notifica con causa probable y acciones.

## Guardrails

- máximo un restart automático;
- no reiniciar host por una app;
- no tocar storage si hay error de filesystem;
- no cambiar firewall automáticamente;
- no ejecutar comandos inventados por el modelo sin una herramienta predefinida;
- registrar todo cambio.
