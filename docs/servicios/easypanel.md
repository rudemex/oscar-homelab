---
title: EasyPanel
sidebar_position: 3
---

# EasyPanel

**Estado:** Laboratorio · Plataforma de apps (evaluar redundancia)  
**Dónde corre:** VM Docker dedicada o `core01` durante la etapa inicial  
**Sizing inicial:** 2+ vCPU, 4+ GB RAM recomendados para plataforma + apps  
**Red/puertos:** HTTP/HTTPS y administración según configuración  
**Persistencia:** configuración de plataforma, volúmenes de apps y bases de datos

:::info Laboratorio, no Objetivo
Aunque `pve01` ya tiene 32 GB de RAM y hay margen de sobra, correr EasyPanel **además** de Docker Compose manual **y** k3s + Argo CD sigue siendo redundante: los tres resuelven "cómo llevo una app a producción", y tener más RAM no cambia que sea el mismo problema resuelto tres veces. El stack GitOps (Nexus → Argo CD → k3s) ya es el camino objetivo para despliegues serios; EasyPanel se documenta como laboratorio para comparar experiencia de desarrollador, no como plataforma paralela permanente. Si tras probarlo no aporta algo que Compose/k3s no den, se descarta.
:::

## Rol dentro de O.S.C.A.R.

- comparar experiencia "PaaS casero" contra el flujo GitOps
- desplegar proyectos Node/Next/Nest rápidamente para probar una idea
- crear servicios desde imágenes Docker sin escribir Compose a mano
- entender qué automatiza un PaaS y qué esconde

## Ejemplo concreto

Ejemplo de uso: desplegar una API NestJS, un PostgreSQL y un frontend Next.js como tres servicios separados, con dominio interno y volúmenes persistentes.

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

EasyPanel simplifica operación pero no reemplaza Git, backups ni observabilidad. Los datos de bases deben tener backup independiente.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

Documentar específicamente:

1. qué directorios/DB contienen estado;
2. si la aplicación necesita dump consistente;
3. dónde se guarda la copia;
4. cómo restaurarla en una instancia aislada;
5. cuánto tarda una recuperación real.

## Observabilidad

Como mínimo:

- disponibilidad HTTP/TCP;
- consumo de CPU/RAM;
- tamaño del volumen;
- reinicios del proceso/contenedor;
- logs de errores.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://easypanel.io/docs
