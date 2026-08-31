---
title: Instalar Nexus
sidebar_position: 5
---

# Nexus Repository paso a paso

## 1. Capacidad

Nexus consume RAM e I/O y sus blobs crecen. Antes de desplegar:

- asignar storage con margen;
- definir retención;
- evitar alojarlo en el mismo filesystem sin alertas.

## 2. Directorio

```bash
mkdir -p /srv/oscar/apps/nexus
cd /srv/oscar/apps/nexus
```

## 3. Compose conceptual

```yaml
services:
  nexus:
    image: sonatype/nexus3:${NEXUS_VERSION}
    restart: unless-stopped
    volumes:
      - nexus-data:/nexus-data
    ports:
      - "127.0.0.1:8081:8081"
    mem_limit: 6g

volumes:
  nexus-data:
```

El límite de memoria se ajusta según RAM real y recomendaciones de la versión instalada.

## 4. Primer acceso

```bash
docker compose up -d
```

Nexus genera una contraseña inicial de `admin` y la guarda en un archivo dentro del volumen — leerla desde el contenedor:

```bash
docker compose exec nexus cat /nexus-data/admin.password
```

Entrar a `http://127.0.0.1:8081` (o vía el reverse proxy interno una vez configurado) con usuario `admin` y esa contraseña. El asistente de primer inicio pide cambiarla — hacerlo, y en el mismo asistente deshabilitar **anonymous access** si no se necesita que repos públicos respondan sin autenticación.

## 5. npm

Crear:

```text
npm-proxy
npm-hosted
npm-group
```

Apuntar un proyecto demo a `npm-group` y comprobar cache.

## 6. Docker/OCI

Definir hosted repo y método de exposición interno. Probar:

```bash
docker login <registry>
docker tag demo:1.0 <registry>/demo:1.0
docker push <registry>/demo:1.0
```

## 7. Cleanup

Crear política de cleanup antes de llenar el registry. Medir blob store desde Grafana/host.

## 8. Backup

Ver el procedimiento concreto (qué respaldar, con qué frecuencia, cómo restaurar) en [Sonatype Nexus Repository — Backup y restore](../servicios/nexus.md#backup-y-restore); no lo repetimos acá para no mantenerlo en dos lugares.
