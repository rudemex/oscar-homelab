---
title: Índice de laboratorios
sidebar_position: 1
---

# Laboratorios progresivos

Los labs deben poder romperse. Nunca usar datos importantes en ellos: cada uno documenta explícitamente cómo deshacerse (sección Cleanup) para no dejar VMs, namespaces o datos de prueba colgando de forma permanente.

Algunos labs son experimentos puramente descartables; otros coinciden con un paso real del [roadmap de construcción](../roadmap/roadmap-general.md) y, si se siguen sobre la infraestructura real de O.S.C.A.R. en vez de sobre recursos aislados de práctica, terminan dejando un servicio permanente en pie. Cada lab aclara esto en su Objetivo, con una etiqueta **Tipo**.

| Lab | Nivel | Tema | Tipo |
|---|---:|---|---|
| [01 · Linux y SSH](./01-linux-ssh.md) | básico | ciclo de vida de una VM y hardening SSH | descartable |
| [02 · Docker Compose](./02-docker-compose.md) | básico | imagen, contenedor, volumen, red y archivo Compose | mixto — Uptime Kuma puede quedar como servicio real |
| [03 · DNS y reverse proxy](./03-dns-proxy.md) | básico | flujo DNS → proxy → app con Traefik | descartable |
| [04 · Observabilidad](./04-observabilidad.md) | intermedio | node exporter, dashboard y una alerta disparada de verdad | mixto — el stack queda como servicio real (Fase 4) |
| [05 · CI + Nexus](./05-ci-nexus.md) | intermedio | pipeline, artefacto versionado y pull remoto | descartable — Nexus en sí es real, la imagen demo no |
| [06 · k3s](./06-k3s.md) | intermedio | reconciliación de Kubernetes (ReplicaSet, rollout, rollback) | descartable — namespace `oscar-lab` |
| [07 · GitOps](./07-gitops.md) | intermedio | Argo CD, drift manual, self-heal y rollback declarativo | mixto — puede quedar como demo permanente del repo GitOps |
| [08 · Backup y restore](./08-backup-restore.md) | avanzado | RTO real y dependencias no documentadas | descartable |
| [09 · Fallo controlado](./09-fallo-controlado.md) | avanzado | cadena alerta → diagnóstico → recuperación | no destructivo — valida monitoreo y runbooks reales |
| [10 · IA read-only](./10-ia-readonly.md) | avanzado | agente con herramientas de solo lectura | descartable — workflow de prueba |

## Orden sugerido

Los labs 01 a 07 siguen de cerca el orden del roadmap (VM → Docker → red → observabilidad → DevOps → Kubernetes → GitOps) y conviene resolverlos en secuencia, porque cada uno asume el anterior resuelto. Los labs 08, 09 y 10 son transversales: reutilizan lo que ya existe (backups, monitoreo, documentación) en vez de construir una capa nueva, y pueden repetirse periódicamente como ejercicio de mantenimiento en vez de hacerse una sola vez.
