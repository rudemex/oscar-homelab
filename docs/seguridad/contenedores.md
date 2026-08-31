---
title: Seguridad de contenedores
sidebar_position: 4
---

# Contenedores

## Baseline

- imágenes oficiales/confiables;
- tags versionados o digests para servicios críticos;
- usuario no-root cuando sea viable;
- filesystem read-only cuando la app lo soporte;
- capabilities mínimas;
- no `--privileged` por comodidad;
- no Docker socket salvo necesidad;
- scan de imágenes en pipeline futuro;
- secrets fuera de imagen — nunca como variable de entorno en texto plano en `compose.yaml` versionado; usar `.env` fuera de Git ([ver gestión de secretos](./secretos.md)) o `secrets:` de Compose.

## Ejemplo aplicado (Docker Compose)

```yaml
services:
  app:
    image: registry.oscar.home/app:1.4.2   # tag fijo, nunca :latest en servicios importantes
    user: "1000:1000"                       # no-root
    read_only: true                         # filesystem raíz de solo lectura
    tmpfs:
      - /tmp                                 # ruta escribible mínima si la app la necesita
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    environment:
      - APP_ENV=production
    env_file:
      - .env                                 # fuera de Git; solo .env.example se versiona
    restart: unless-stopped
```

Equivalente con `docker run` para pruebas puntuales:

```bash
docker run -d \
  --name app \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --env-file .env \
  registry.oscar.home/app:1.4.2
```

## Supply chain

El pipeline debería poder incorporar un scanner como Trivy para practicar políticas de vulnerabilidades y SBOM sin bloquear toda experimentación desde el primer día:

```bash
trivy image --severity HIGH,CRITICAL registry.oscar.home/app:1.4.2
```

Integrarlo como paso no bloqueante al principio (solo reporta) y recién exigir "sin CRITICAL" como gate una vez que el pipeline es estable — ver [pipeline de referencia](../devops/pipeline-ejemplo.md).
