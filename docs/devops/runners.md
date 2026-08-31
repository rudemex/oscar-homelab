---
title: Runners CI
sidebar_position: 3
---

# Runners

## Tipos

- runner estable para repos propios confiables;
- runner efímero para laboratorios;
- runner privilegiado solo para jobs que realmente lo necesitan.

## Riesgos

Un pipeline puede ejecutar código arbitrario. Dar acceso a Docker socket, red MGMT o credenciales de despliegue convierte ese pipeline en una superficie de administración.

## Secretos

Las credenciales de registry/GitOps se guardan en el sistema de CI o gestor de secretos, con scopes mínimos.

## Métricas

Observar:

- duración de builds;
- queue time;
- CPU/RAM;
- cache hit;
- espacio de trabajo;
- fallos por dependencia externa.
