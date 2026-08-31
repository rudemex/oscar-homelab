---
title: MinIO
sidebar_position: 19
---

# MinIO

**Estado:** Laboratorio · Object Storage  
**Dónde corre:** VM/storage de laboratorio  
**Sizing inicial:** depende fuertemente de I/O y capacidad  
**Red/puertos:** API S3 + consola, internas  
**Persistencia:** objetos; no usar como única copia de datos

## Rol dentro de O.S.C.A.R.

- aprender API S3
- backend de apps
- artefactos de laboratorio
- practicar políticas de buckets

## Ejemplo concreto

Una API NestJS sube archivos a un bucket S3-compatible sin depender de AWS durante el desarrollo.

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

No confundir object storage con backup. Si los objetos importan, también deben respaldarse.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Los datos viven en el volumen de almacenamiento configurado; en el modo de un solo nodo de laboratorio son archivos planos en disco, sin erasure coding real.

Al ser un laboratorio para aprender la API S3, el criterio por defecto es que **no vale la pena respaldarlo**: si se pierde el volumen, se recrea vacío y se vuelve a cargar lo que haga falta para el experimento en curso.

Nota: si en algún momento MinIO empieza a alojar algo que otro servicio consume de verdad (por ejemplo, como backend de Loki), esa dependencia deja de ser "laboratorio" y su backup hay que resolverlo en ese momento.

## Observabilidad

Laboratorio de bajo valor operativo: no se justifica alertar ni definir SLO. Alcanza con verificar manualmente, cuando se está usando, que el contenedor esté arriba y que la consola/API respondan.

## Troubleshooting

**No se puede subir un archivo** → bucket con política de solo lectura o disco lleno → revisar la política del bucket y el espacio en disco disponible.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://min.io/docs/
