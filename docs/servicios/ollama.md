---
title: Ollama
sidebar_position: 16
---

# Ollama

**Estado:** Laboratorio · IA local  
**Dónde corre:** Dell/VM solo para modelos compatibles con recursos; hardware futuro para cargas mayores  
**Sizing inicial:** muy dependiente del modelo; RAM es la limitación central sin GPU  
**Red/puertos:** API interna; no publicar sin autenticación/proxy  
**Persistencia:** modelos descargados y cache

## Rol dentro de O.S.C.A.R.

- probar LLM local
- resumir logs no sensibles
- clasificar alertas
- RAG sobre documentación

## Ejemplo concreto

Un agente consulta docs de O.S.C.A.R. y explica un incidente sin enviar datos a un servicio externo, si el modelo local tiene capacidad suficiente.

## Checklist de despliegue

- [ ] hostname y ubicación decididos;
- [ ] imagen/versión fijada, evitando tags flotantes en servicios importantes;
- [ ] puertos documentados;
- [ ] volumen/persistencia definida;
- [ ] `.env.example` sin secretos en Git;
- [ ] credenciales reales fuera de Git;
- [ ] backup definido antes de cargar datos importantes;
- [ ] healthcheck o monitor de disponibilidad;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado.

## Seguridad

No diseñar la operación crítica asumiendo que el Dell actual correrá modelos grandes con buena latencia.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El volumen grande son los modelos descargados bajo `~/.ollama/models`: pesan gigabytes pero son 100% re-descargables desde el registry de Ollama (`ollama pull <modelo>`), así que **no se respaldan**.

Lo único que sí vale la pena versionar en Git son los `Modelfile` personalizados que se hayan creado (definiciones de modelos custom), porque son trabajo propio que no se recrea automáticamente.

## Observabilidad

Laboratorio de bajo valor operativo: no se justifica alertar ni definir SLO. Alcanza con verificar manualmente que el contenedor esté arriba y que `ollama list` responda con los modelos esperados.

## Troubleshooting

**El modelo responde muy lento** → hardware insuficiente para el tamaño del modelo elegido → probar un modelo más chico y revisar uso de CPU/RAM durante la inferencia.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://ollama.com/
