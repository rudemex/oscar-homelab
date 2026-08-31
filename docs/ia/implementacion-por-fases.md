---
title: Implementación de IA por fases
sidebar_position: 6
---

# Implementar la capa de IA

## Fase AI-0 · Documentación consultable

Indexar solamente:

- docs;
- inventario no sensible;
- ADRs;
- runbooks.

Resultado: Q&A sin acceso a infraestructura.

## Fase AI-1 · Estado read-only

Agregar herramientas:

```text
get_service_catalog()
get_host_health()
query_prometheus()
search_logs()
get_backup_status()
```

No hay SSH ni write APIs.

## Fase AI-2 · Recomendaciones

El agente correlaciona métricas + logs + runbooks y devuelve:

```text
Síntoma
Evidencia
Hipótesis
Riesgo
Acción sugerida
Runbook
```

## Fase AI-3 · Safe actions

A través de n8n/MCP:

- restart de un contenedor de laboratorio;
- reintentar un backup una sola vez;
- abrir issue/PR;
- generar reporte.

Toda acción tiene allowlist, timeout y audit log.

## Fase AI-4 · Aprobación humana

Cambios sensibles se preparan pero no se ejecutan hasta aprobación:

- firewall;
- DNS global;
- borrar VM;
- cambios de storage;
- rotación amplia de secretos.

## Fase AI-5 · Evaluación

Crear casos de prueba para evitar que el agente “parezca inteligente” sin ser confiable:

- servicio caído;
- DNS roto;
- disco lleno;
- backup fallido;
- métrica falsa positiva.

Medir si identifica causa y elige el runbook correcto.
