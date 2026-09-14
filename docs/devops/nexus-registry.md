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

## Otros stacks tecnológicos

Nexus Repository **OSS** (la edición gratuita, sin licencia Pro) soporta como hosted/proxy/group, además de npm y Docker: Maven/Java, PyPI, NuGet, RubyGems, Go, APT, YUM, Conda, Helm charts y `raw` (para artefactos genéricos, ej. binarios propios o backups). El mismo servicio cubre cualquier stack que se sume más adelante (Python, Go, un chart de Helm propio) sin necesidad de otro producto — solo hay que dar de alta el repositorio del formato correspondiente cuando haga falta.

No confundir con las features que sí son Pro-only: SAML/LDAP avanzado, blob store con cifrado, staging/release workflows de Maven y soporte comercial — ninguna bloquea el uso como registry+proxy multi-stack de un homelab.

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
