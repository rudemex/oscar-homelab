---
title: RAG sobre la documentación
sidebar_position: 3
---

# RAG de O.S.C.A.R.

Este repositorio puede convertirse en la base de conocimiento del agente.

## Fuentes

- Markdown de Docusaurus;
- inventario YAML;
- ADRs;
- runbooks;
- diagramas/textos;
- historial de incidentes sanitizado.

## Preguntas útiles

- “¿Dónde está desplegado Nexus?”
- “¿Cuál es el procedimiento de restore de n8n?”
- “¿Qué VLAN debería tener el DVR?”
- “¿Qué depende de DNS1?”
- “Dame el runbook para disco lleno.”

## Indexación

Evitar indexar:

- `.env`;
- claves;
- tokens;
- dumps con información privada;
- logs sin sanitizar.
