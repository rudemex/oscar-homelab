---
title: Helm
sidebar_position: 3
---

# Helm

Helm permite empaquetar aplicaciones Kubernetes y parametrizar instalaciones.

## Filosofía

No modificar un chart de terceros copiándolo entero salvo necesidad. Preferir:

```text
chart upstream + values-oscar.yaml
```

## Ejemplo de values

```yaml
ingress:
  enabled: true
  hosts:
    - host: app.oscar.home
      paths:
        - path: /
          pathType: Prefix

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    memory: 256Mi
```

## Qué versionar

- versión del chart;
- repository URL;
- `values.yaml` propios;
- namespace;
- notas de upgrade.

## Laboratorio

Instalar un chart, exportar los manifests renderizados con `helm template`, comparar con lo que realmente aplica Argo CD y entender qué valores cambian el Deployment/Service.
