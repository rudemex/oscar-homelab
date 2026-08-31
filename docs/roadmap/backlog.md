---
title: Backlog técnico
sidebar_position: 2
---

# Backlog

## Prioridad alta (barato/rápido, desbloquea el resto)

- **integrar el UPS/estabilizador existente** al rack (reubicar + NUT) — ya está pagado, es la tarea de menor costo/mayor impacto del backlog, ver [Fase 1 del roadmap](./roadmap-general.md#fase-1--rack-red-y-energía);
- **destino off-site de backup** — no requiere NAS ni hardware nuevo, alcanza con una cuenta de object storage barata; hoy es el mayor riesgo activo porque todo vive en un solo Dell (ver [estrategia 3-2-1](../backup-dr/estrategia-321.md));
- switch >8 puertos definitivo para RackMate T2 (cualquier gigabit gestionable que entre en 10" resuelve esto — no requiere tanta deliberación como las demás decisiones de esta lista).

## Resueltas recientemente

- **RAM del Dell**: ampliada de 16 GB a 32 GB (ambos slots ocupados — sin margen para ampliar más sin reemplazar módulos), y de paso el M.2 de 512 GB a 1 TB (slot único, reemplazo en vez de suma). Desbloquea separar observabilidad en su propia VM — ver [distribución con 32 GB](../hardware/dell-7060.md#distribución-con-32-gb).

## Decisiones pendientes

- hardware N100/OPNsense;
- NAS (Raspberry Pi vs equipo dedicado vs comercial);
- plataforma Git local (ADR: Forgejo vs. alternativas);
- motor de CI runner (depende de la plataforma Git elegida — ver [CI Runner](../servicios/ci-runner.md));
- gestor de secretos;
- ubicación final de Home Assistant;
- proveedor/backends de IA.

## Mejoras futuras

- Ansible;
- Terraform provider Proxmox;
- Renovate/Dependabot para imágenes y manifests;
- SBOM/Trivy en pipelines;
- Proxmox Backup Server;
- segundo host Proxmox;
- HA k3s;
- PKI interna;
- SSO interno;
- sensores ambientales del rack.
