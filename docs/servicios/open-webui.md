---
title: Open WebUI
sidebar_position: 17
---

# Open WebUI

**Estado:** Laboratorio · IA  
**Dónde corre:** Docker Core conectado a proveedor/modelo permitido  
**Sizing inicial:** 1–2 GB RAM + recursos del backend LLM  
**Red/puertos:** interfaz web interna  
**Persistencia:** usuarios, chats y configuración según features usadas

## Rol dentro de O.S.C.A.R.

- UI para Ollama
- probar modelos
- RAG local
- experimentos con herramientas

## Ejemplo concreto

Crear una colección con la documentación del homelab y consultar “¿qué debo revisar si core01 no resuelve DNS?”.

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

Revisar qué datos se almacenan y qué backend recibe prompts antes de cargar secretos o logs sensibles.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El estado (usuarios, historial de chats, documentos cargados para RAG) vive en una base SQLite bajo `/app/backend/data`.

Es un laboratorio, así que por defecto ese historial es descartable. Solo vale la pena respaldar ese directorio si se está usando para RAG sobre documentación real de O.S.C.A.R. (uno de los casos de uso del roadmap de IA) y se quiere conservar el trabajo de indexado; en ese caso, un backup simple del directorio con [Restic](./restic.md) alcanza.

## Observabilidad

Laboratorio de bajo valor operativo: no se justifica alertar ni definir SLO. Alcanza con verificar manualmente que el contenedor esté arriba y que la interfaz responda.

## Troubleshooting

**No conecta con Ollama** → URL del backend mal configurada o red Docker distinta → verificar que ambos contenedores compartan red y que la variable de entorno de la URL de Ollama sea correcta.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://docs.openwebui.com/
