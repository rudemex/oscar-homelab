---
title: Decisiones arquitectónicas
sidebar_position: 5
---

# Decisiones arquitectónicas

Esta página funciona como un índice liviano de ADRs (Architecture Decision Records). Cada decisión importante debe registrar contexto, elección y consecuencias.

## ADR-001 · Proxmox como base de virtualización

**Status:** Aceptado.

**Context:** el Dell OptiPlex 7060 es el único host de cómputo serio del laboratorio. Hay que decidir si corre Docker directo sobre Debian/Ubuntu, o un hypervisor que lo virtualice.

**Decision:** el Dell principal utiliza Proxmox en lugar de instalar Docker directamente sobre el host.

**Alternatives considered:**
- Docker directo sobre Debian/Ubuntu — más simple, pero sin aislamiento entre plataformas ni snapshots por carga.
- otro hypervisor (ESXi, XCP-ng) — descartado por licenciamiento (ESXi) o comunidad/documentación más chica (XCP-ng) frente a Proxmox para un homelab.

**Consequences:**
- (+) snapshots y backups por VM/LXC, aislamiento entre plataformas, laboratorios desechables, posibilidad de crecer a más nodos, administración centralizada;
- (-) más capas y consumo base de recursos (RAM/CPU reservados para el hypervisor).

## ADR-002 · Docker dentro de VM, no en el host Proxmox

**Status:** Aceptado.

**Context:** con Proxmox como hypervisor (ADR-001), hay que decidir si los contenedores de aplicación corren sobre el propio host Proxmox o dentro de una VM dedicada.

**Decision:** Docker de aplicaciones corre siempre dentro de una VM (`core01`), nunca sobre el host Proxmox.

**Alternatives considered:**
- Docker sobre el host Proxmox directamente — más liviano, pero mezcla el ciclo de vida del hypervisor con el de las aplicaciones y complica backups/rollback independientes.

**Consequences:**
- (+) el host de virtualización se mantiene simple y estable; los contenedores de aplicación no modifican paquetes, reglas o discos del hypervisor; la VM Docker se puede snapshotear/recrear sin tocar Proxmox;
- (-) overhead adicional de una capa de virtualización para lo que podría ser un proceso nativo.

## ADR-003 · k3s como distribución de Kubernetes

**Status:** Aceptado.

**Context:** se quiere aprender Kubernetes real (Deployments, Services, Ingress, GitOps) sin el overhead operativo de una distribución completa, sobre un único nodo inicial con recursos compartidos con el resto de O.S.C.A.R. (16 GB RAM al momento de esta decisión, ampliado luego a 32 GB — ver [Dell OptiPlex 7060](../hardware/dell-7060.md)).

**Decision:** usar k3s (Rancher/SUSE) como distribución de Kubernetes.

**Alternatives considered:**
- Kubernetes "completo" (kubeadm) — mismo control plane pero mucho mayor consumo de recursos base, más piezas para mantener manualmente (etcd, componentes del control plane por separado); no se justifica en un nodo único de homelab, con 16 o con 32 GB — el problema no es la RAM disponible sino la carga operativa de mantener un control plane completo a mano.
- k0s / MicroK8s — alternativas livianas válidas; se descartan por menor adopción/documentación relativa a k3s en el ecosistema homelab, no por una limitación técnica concreta.

**Consequences:**
- (+) instalación de un solo binario, bajo consumo base, compatible con Helm/manifiestos estándar, camino claro a multi-nodo si crece el hardware;
- (-) algunas diferencias menores respecto de Kubernetes "upstream" (ej. Traefik y ServiceLB por defecto) que hay que conocer al comparar con documentación genérica de Kubernetes.

## ADR-004 · Argo CD como motor de GitOps

**Status:** Aceptado.

**Context:** con k3s decidido (ADR-003), los workloads persistentes deben tender a ser declarativos y reconciliados desde Git en lugar de `kubectl apply` manual.

**Decision:** usar Argo CD como motor de GitOps, sincronizando desde un repositorio Git (`oscar-gitops`) hacia el cluster k3s. `kubectl apply` manual queda para bootstrap y troubleshooting puntual, no como flujo normal.

**Alternatives considered:**
- Flux CD — igual de válido técnicamente; se elige Argo CD por su UI web (útil para aprender visualmente el estado de sync/health en un contexto de aprendizaje) y mayor familiaridad previa.
- sin GitOps, solo `kubectl apply`/`helm upgrade` manual — descartado porque no deja rastro auditable ni permite rollback declarativo (contradice el principio de reproducibilidad de [la introducción](../intro.md)).

**Consequences:**
- (+) todo cambio de infraestructura declarativa queda versionado y auditable; un revert en Git revierte el cluster;
- (-) introduce el problema de secrets-en-GitOps, que requiere una solución explícita — ver [gestión de secretos](../seguridad/secretos.md); curva de aprendizaje adicional (App of Apps, sync waves, health checks).

## ADR-005 · Exposición externa mínima

**Status:** Aceptado.

No se abren puertos arbitrarios en el router para paneles administrativos. Cuando un servicio deba accederse desde fuera se evalúan, según el caso:

- VPN;
- Cloudflare Tunnel + Access;
- autenticación fuerte de la propia aplicación.

Ver detalle en [exposición a Internet](../seguridad/exposicion-internet.md).

## ADR-006 · Cloudflare Tunnel + Access para acceso remoto

**Status:** Aceptado (target state — no desplegado hoy).

**Context:** dado ADR-005 (exposición mínima), se necesita un mecanismo concreto para acceder a paneles internos (Grafana, etc.) desde fuera de la LAN sin abrir puertos en el router.

**Decision:** usar Cloudflare Tunnel (conexión saliente desde O.S.C.A.R. hacia el borde de Cloudflare, sin inbound port-forward) combinado siempre con Cloudflare Access (identidad + MFA + políticas) delante de cualquier panel administrativo.

**Alternatives considered:**
- VPN propia (WireGuard/Tailscale) — sigue siendo el camino preferido para acceso administrativo tipo SSH/Proxmox UI (ver tabla en [exposición a Internet](../seguridad/exposicion-internet.md)); Tunnel+Access se reserva para HTTP(S) donde tiene sentido una identidad de aplicación en vez de una identidad de red.
- port-forward directo en el router — descartado por ADR-005.

**Consequences:**
- (+) cero puertos abiertos en el router para HTTP(S); identidad y MFA centralizados en Access; fácil de revocar por usuario/dispositivo;
- (-) dependencia de un proveedor externo (Cloudflare) para el acceso remoto; un Tunnel sin Access configurado explícitamente NO es privado — riesgo real si se despliega apurado (ver [exposición a Internet](../seguridad/exposicion-internet.md)).

## ADR-007 · Prometheus + Grafana como base de observabilidad

**Status:** Aceptado.

**Context:** antes de sumar muchos servicios se necesita una base de métricas y disponibilidad — ver ADR-008. Hay que elegir el stack concreto.

**Decision:** Prometheus (métricas, pull-based) + Grafana (visualización) como base, con Loki para logs y Uptime Kuma para chequeos HTTP/TCP externos al stack de métricas.

**Alternatives considered:**
- Zabbix/Nagios (monitoreo clásico) — modelo más orientado a alertas/agentes que a series temporales flexibles; menos natural para dashboards ricos y para aprender el modelo pull de Prometheus, que es el estándar de facto en el ecosistema Kubernetes/CNCF.
- InfluxDB + Telegraf — alternativa válida; se descarta por preferir el ecosistema Prometheus, que integra mejor con exporters ya estándar (node_exporter, kube-state-metrics) y con Argo CD/k3s.

**Consequences:**
- (+) ecosistema de exporters maduro, integración directa con k3s/Argo CD, un solo lenguaje de consulta (PromQL) para host y cluster;
- (-) retención de métricas de alta cardinalidad consume disco rápido en un solo host — requiere política de retención explícita (ver [instalación del stack](../observabilidad/instalacion-stack.md)).

## ADR-008 · Observabilidad antes de escala

**Status:** Aceptado.

Antes de sumar muchos servicios se instala una base de métricas y disponibilidad. Crecer sin visibilidad convierte cualquier falla en adivinanza — ver [fase 4 del roadmap](../roadmap/roadmap-general.md).

## ADR-009 · Nexus Repository como artifact registry

**Status:** Aceptado.

**Context:** el pipeline objetivo (Git → CI → build → registry → GitOps → k3s) necesita un lugar donde publicar imágenes OCI y, opcionalmente, cachear paquetes npm.

**Decision:** usar Sonatype Nexus Repository OSS como registry de imágenes y proxy/cache de npm.

**Alternatives considered:**
- registry de contenedores mínimo (Docker Registry v2 / `registry:2`) — más simple, pero sin UI, sin proxy de npm y sin políticas de limpieza — hay que reconstruir esas features a mano.
- Harbor — más completo (scanning integrado, RBAC) pero significativamente más pesado para un solo operador; se revisita si el laboratorio de seguridad de supply chain crece.

**Consequences:**
- (+) un solo servicio cubre registry de imágenes y proxy npm; UI de administración; políticas de cleanup evitan que el datastore crezca sin control (ver runbook [Nexus lleno](../runbooks/nexus-lleno.md));
- (-) más pesado que un registry mínimo; requiere su propia política de backup/retención (ver [matriz de backup](../backup-dr/matriz-backup.md)).

## Próximas ADR

- elección del switch gestionable definitivo;
- firewall dedicado y hardware N100 (OPNsense);
- NAS y estrategia de storage compartido;
- gestor de secretos para GitOps (SOPS+age vs. Sealed Secrets — ver [gestión de secretos](../seguridad/secretos.md));
- plataforma Git local definitiva (Forgejo vs. alternativas — ver [Forgejo / Git local](../servicios/forgejo.md));
- motor de CI runner, dependiente de la decisión anterior (ver [CI Runner](../servicios/ci-runner.md));
- motor de IA local cuando exista hardware adecuado (ver [IA local vs. remota](../ia/local-vs-remoto.md)).
