---
title: Nexus como registry
sidebar_position: 2
---

# Nexus: npm, Docker y artefactos

## Repositories sugeridos

### npm

- `npm-proxy`: cache upstream;
- `npm-hosted`: paquetes propios;
- `npm-group`: endpoint unificado.

### Docker/OCI

- hosted para imágenes propias;
- proxy para cache si el caso lo justifica;
- cleanup policies por antigüedad/uso.

## Naming de imagen

```text
nexus.oscar.home/<proyecto>/<imagen>:<semver-o-sha>
```

Evitar depender de `latest` para deployments reproducibles.

## Prueba

1. build de una API;
2. push al registry;
3. borrar imagen local;
4. pull desde otro host;
5. validar digest.
