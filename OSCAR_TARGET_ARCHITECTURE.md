# O.S.C.A.R. — Arquitectura objetivo y plan de reorganización

> [!WARNING]
> **DEPRECATED (2026-09-17)**
>
> Este documento fue reemplazado por `OSCAR_FINAL_INFRASTRUCTURE.md` como fuente de verdad de arquitectura. No usar para nuevos planes o implementaciones — se conserva solo como registro histórico de por qué se tomaron ciertas decisiones (ej. ADR-010/ADR-012 en `docs/arquitectura/decisiones-arquitectonicas.md` referencian el razonamiento original acá).

> Documento de referencia para planificar la evolución de O.S.C.A.R.
>
> Objetivo: reorganizar los servicios actuales por función, mejorar resiliencia, desacoplar monitoreo/acceso remoto del Dell principal y preparar la plataforma para futuras aplicaciones, observabilidad centralizada e IA.

---

## 1. Resumen ejecutivo

O.S.C.A.R. ya cuenta con una base sólida de infraestructura:

- Proxmox VE como hipervisor principal.
- Servicios core sobre una VM dedicada.
- DevOps sobre una VM separada.
- Kubernetes k3s para aplicaciones.
- Home Assistant.
- AdGuard.
- Forgejo + Runner.
- Nexus.
- Argo CD.
- Uptime Kuma.
- Beszel.
- n8n.
- Nginx Proxy Manager.
- Cloudflare Tunnel.
- Tailscale.
- Raspberry Pi 3 y Raspberry Pi Zero W disponibles.

La siguiente etapa no consiste en agregar servicios indiscriminadamente, sino en **ordenar responsabilidades por host** y mejorar la independencia entre:

1. Compute.
2. Observabilidad.
3. Management / acceso remoto.
4. Servicios de red críticos.
5. Aplicaciones.
6. DevOps.
7. Automatización.
8. IA.

La idea central es que, aun si el Dell principal o Proxmox quedan fuera de servicio, O.S.C.A.R. conserve:

- Acceso remoto.
- Uptime monitoring.
- Métricas.
- Dashboard de observabilidad.
- Monitoreo de Internet.
- DNS secundario.

---

# 2. Hardware principal

## 2.1 oscar-core

**Equipo:** Dell OptiPlex 7060 Micro  
**CPU:** Intel Core i7 8ª generación  
**RAM:** 32 GB  
**Storage:**

- NVMe 1 TB
- SATA SSD 1 TB

**Hipervisor:** Proxmox VE 9.2.18

---

## 2.2 Raspberry Pi disponibles

### Raspberry Pi 3

Disponibles para servicios auxiliares independientes del Dell.

Roles previstos:

- `monitor01`
- `network01`

### Raspberry Pi Zero W

Disponibles para:

- DNS secundario.
- Sensores.
- Telemetría.
- IoT.
- Laboratorio.
- Automatizaciones físicas.

---

# 3. Estado actual del Dell

## 3.1 VMs / LXC

| VM/LXC | vCPU | RAM | Disco |
|---|---:|---:|---:|
| core01 | 2 | 8 GB | 60 GB |
| devops01 | 6 | 12 GB | 60 GB |
| k3s01 | 4 | 8 GB | 60 GB |
| haos-18.2 | 2 | 4 GB | 32 GB |
| AdGuard LXC | 1 | 512 MB | — |

### Observación de capacidad

La memoria asignada nominalmente suma aproximadamente:

```text
core01       8 GB
devops01    12 GB
k3s01        8 GB
HAOS         4 GB
AdGuard    0.5 GB
----------------
            32.5 GB
```

Esto implica overcommit respecto de los 32 GB físicos.

No necesariamente es un problema si el uso real es menor, pero obliga a:

- Medir consumo real.
- Aplicar `requests` y `limits` en Kubernetes.
- Evitar nuevas VMs pesadas.
- Preferir nuevos workloads sobre k3s cuando tenga sentido.
- Revisar periódicamente presión de memoria en Proxmox.

---

# 4. Estado actual por host

## 4.1 core01

**IP:** `192.168.0.156`  
**Recursos:** 2 vCPU / 8 GB RAM

Servicios actuales:

| Aplicación | Puerto |
|---|---:|
| Homepage | 3005 |
| Nginx Proxy Manager | 80 / 81 / 443 |
| Uptime Kuma | 3001 |
| Beszel Hub | 8090 |
| Vaultwarden | 127.0.0.1:8082 |
| n8n + PostgreSQL | 5678 |
| Glances | 61208 |
| MySpeed | 5216 |
| Relay SMTP (Brevo) | — |
| Cloudflare Tunnel | saliente |
| Tailscale | subnet router |
| ProxMenux Monitor | 8008 |

Actualmente los contenedores no tienen cuotas CPU/RAM individuales.

---

## 4.2 devops01

**IP:** `192.168.0.151`  
**Recursos:** 6 vCPU / 12 GB RAM

Servicios:

| Aplicación | Puerto |
|---|---:|
| Forgejo | 3000 / SSH 2222 |
| Forgejo Runner | — |
| Nexus | 8081 / registry 8082 |
| Beszel Agent | 45876 |

---

## 4.3 k3s01

**IP:** `192.168.0.150`  
**Recursos:** 4 vCPU / 8 GB RAM

Servicios:

| Aplicación | Namespace |
|---|---|
| k3s + Traefik | kube-system |
| Argo CD | argocd |
| oscar-led-controller | oscar-lab |
| ci-demo | oscar-lab |
| Beszel Agent | host |

Actualmente no hay `resources.requests` ni `resources.limits` definidos para los Deployments.

---

# 5. Arquitectura objetivo

La plataforma se reorganizará en cuatro planos principales:

```text
CONTROL / MANAGEMENT PLANE
Pi 3 #2
Tailscale + Uptime Kuma

OBSERVABILITY PLANE
Pi 3 #1
Prometheus + Grafana + Internet monitoring

COMPUTE PLANE
Dell 7060
Proxmox + VMs + k3s

NETWORK SAFETY
Pi Zero W
DNS secundario
```

---

# 6. Distribución objetivo de servicios

## 6.1 oscar-core / Proxmox

Responsabilidad:

- Hipervisor principal.
- Compute.
- VMs.
- LXC.
- HAOS.

No debería depender de sí mismo para:

- Saber si está caído.
- Mantener acceso remoto.
- Mantener el único DNS disponible.

---

## 6.2 core01

Rol objetivo:

**Servicios core de aplicación, automatización y acceso HTTP.**

Mantener:

- Homepage.
- Nginx Proxy Manager.
- n8n.
- PostgreSQL de n8n.
- Vaultwarden.
- Relay SMTP.
- Cloudflare Tunnel.

Revisar/migrar:

- Uptime Kuma → `network01`.
- Tailscale subnet router → `network01`.
- MySpeed → retirar luego de migrar Internet monitoring.
- Glances → revisar redundancia.
- Beszel Hub → mantener inicialmente; evaluar mover a `monitor01`.
- ProxMenux Monitor → revisar después de implementar Grafana/Prometheus.

Objetivo final aproximado:

```text
core01
├── Homepage
├── Nginx Proxy Manager
├── n8n
├── PostgreSQL
├── Vaultwarden
├── SMTP Relay
└── Cloudflare Tunnel
```

---

## 6.3 devops01

Rol objetivo:

**Plataforma DevOps.**

Mantener:

```text
devops01
├── Forgejo
├── Forgejo Runner
├── Nexus
└── Beszel Agent
```

Responsabilidades:

- Git privado.
- CI/CD.
- Docker Registry.
- Package repository.
- Pipelines.
- Construcción de imágenes.
- Integración con Argo CD.

---

## 6.4 k3s01

Rol objetivo:

**Cluster de aplicaciones de O.S.C.A.R.**

Mantener:

- k3s.
- Traefik.
- Argo CD.
- oscar-led-controller.
- aplicaciones internas.

Agregar progresivamente:

- IT-Tools.
- SearXNG.
- Open WebUI.
- Stirling PDF.
- otras apps internas.

Namespaces sugeridos:

```text
argocd
kube-system

oscar-system
oscar-tools
oscar-ai
oscar-lab
oscar-apps
```

Ejemplo:

```text
k3s01
├── oscar-system
├── oscar-tools
│   ├── it-tools
│   └── stirling-pdf
├── oscar-ai
│   ├── searxng
│   └── open-webui
├── oscar-lab
│   ├── oscar-led-controller
│   └── ci-demo
└── argocd
```

---

# 7. Raspberry Pi 3 #1 — monitor01

Hostname sugerido:

```text
monitor01
```

Rol:

**Nodo independiente de métricas y observabilidad.**

Servicios previstos:

```text
monitor01
├── Prometheus
├── Grafana
├── Blackbox Exporter
├── Internet-Pi / Internet monitoring
└── node_exporter
```

Opcionalmente, más adelante:

```text
├── Alertmanager
└── Beszel Hub
```

---

# 8. Raspberry Pi 3 #2 — network01

Hostname sugerido:

```text
network01
```

Rol:

**Nodo independiente de management y disponibilidad.**

Servicios:

```text
network01
├── Uptime Kuma
├── Tailscale
│   └── subnet router
└── node_exporter
```

Posibles servicios futuros:

```text
├── health checks de red
├── herramientas de diagnóstico
└── utilidades de administración
```

---

# 9. Raspberry Pi Zero W — DNS secundario

Hostname sugerido:

```text
dns02
```

Servicio:

```text
AdGuard Home
```

Arquitectura:

```text
Router / DHCP
    │
    ├── DNS #1 → AdGuard LXC / Proxmox
    │
    └── DNS #2 → AdGuard / Pi Zero W
```

Objetivo:

Si el Dell o Proxmox están apagados, la red doméstica sigue teniendo resolución DNS.

---

# 10. Independencia ante caída del Dell

Objetivo principal de la reorganización:

Si se apaga completamente el Dell:

```text
Dell OFF
Proxmox OFF
core01 OFF
devops01 OFF
k3s01 OFF
HAOS OFF
AdGuard primario OFF
```

deben seguir operativos:

```text
✅ network01
✅ Tailscale
✅ Uptime Kuma
✅ monitor01
✅ Prometheus
✅ Grafana
✅ Internet monitoring
✅ DNS secundario
✅ Raspberry Pis
```

Esto permite:

- Seguir accediendo remotamente.
- Confirmar que el Dell está caído.
- Continuar monitoreando Internet.
- Mantener histórico de métricas.
- Mantener DNS básico.
- Diagnosticar la infraestructura sin depender del host principal.

---

# 11. Arquitectura de observabilidad

Prometheus deberá convertirse en el almacén central de métricas de O.S.C.A.R.

Esquema:

```text
                        Grafana
                           ▲
                           │
                      Prometheus
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
    Proxmox             Linux Hosts             k3s
    exporter            node_exporter       kube metrics
       │                   │                    │
       │             ┌─────┼─────┐              │
       │             ▼     ▼     ▼              │
       │          core01 devops01 k3s01         │
       │                                        │
       ├──────── Home Assistant metrics ────────┤
       ├──────── Uptime Kuma metrics ───────────┤
       ├──────── Traefik metrics ───────────────┤
       ├──────── Network metrics ───────────────┤
       └──────── Internet metrics ──────────────┘
```

---

# 12. Dashboards Grafana sugeridos

## 12.1 Network

```text
🌐 Network
├── Download
├── Upload
├── Ping
├── Jitter
├── Packet loss
├── DNS latency
├── HTTP latency
└── Internet uptime
```

---

## 12.2 Infrastructure

```text
🖥 Infrastructure
├── Proxmox
├── core01
├── devops01
├── k3s01
├── monitor01
├── network01
└── Raspberry Pis
```

---

## 12.3 Kubernetes

```text
☸ Kubernetes
├── Cluster
├── Nodes
├── Pods
├── Namespaces
├── CPU
├── Memory
├── Traefik
└── Applications
```

---

## 12.4 Home

```text
🏠 Home
├── Home Assistant
├── Temperaturas
├── Sensores
├── Energía
└── Automatizaciones
```

---

## 12.5 Services

```text
🔧 Services
├── Forgejo
├── Nexus
├── n8n
├── Uptime Kuma
├── AdGuard
├── Vaultwarden
└── Cloudflare Tunnel
```

---

## 12.6 OSCAR

```text
🤖 O.S.C.A.R.
├── LED Controller
├── AI
├── Automation
├── Deployments
└── System Overview
```

---

# 13. Internet-Pi

Internet-Pi servirá como base para el monitoreo de conectividad.

Componentes a aprovechar:

- Prometheus.
- Grafana.
- Speedtest.
- Ping.
- HTTP checks.
- histórico.

## Consideración sobre Raspberry Pi 3

La Pi 3 no debe ser necesariamente el equipo que ejecute el Speedtest si la conexión supera las capacidades de su interfaz Ethernet.

Diseño preferido:

```text
monitor01
Prometheus + Grafana
        │
        │ scrape
        ▼
Speedtest Exporter
en host Gigabit
        │
        ▼
Internet
```

Esto permite que la Pi almacene y visualice los resultados mientras el test se ejecuta desde un host con mejor conectividad.

---

# 14. Política de métricas sugerida

Valores iniciales:

```text
node metrics        cada 15 s
kubernetes          cada 15 s
Home Assistant      cada 30-60 s
Uptime Kuma         cada 30 s
Internet ping       cada 5-10 s
Speedtest           cada 30 min
```

No se busca alta frecuencia innecesaria.

---

# 15. Persistencia de Prometheus

Evitar, si es posible, que Prometheus realice escrituras intensivas durante años sobre una microSD.

Opciones preferidas:

```text
Pi 3
├── microSD
│   └── Raspberry Pi OS Lite
│
└── USB storage
    └── datos de Prometheus
```

Idealmente:

- SSD USB.
- Pendrive de buena calidad como alternativa transitoria.
- Retención inicial limitada.

Retención inicial sugerida:

```text
15 días
```

Después se evaluará:

- almacenamiento más grande.
- backup.
- Thanos.
- VictoriaMetrics.
- otra solución de largo plazo.

No implementar esto inicialmente salvo necesidad real.

---

# 16. Uptime Kuma

Mover desde:

```text
core01
```

hacia:

```text
network01
```

Motivo:

La herramienta encargada de detectar una caída no debería depender del host que está monitoreando.

Targets iniciales:

```text
Proxmox
core01
devops01
k3s01
Home Assistant
AdGuard primario
AdGuard secundario
Forgejo
Nexus
n8n
Homepage
Nginx Proxy Manager
Cloudflare Tunnel
Internet
monitor01
network01
```

---

# 17. Tailscale

Mover subnet router desde:

```text
core01
```

hacia:

```text
network01
```

Motivo:

Si Proxmox se encuentra fuera de servicio, se debe conservar acceso remoto a la LAN.

Arquitectura:

```text
Internet
   │
Tailscale
   │
network01
   │
OSCAR LAN
```

El subnet router deberá anunciar la red LAN de O.S.C.A.R.

---

# 18. Beszel

Mantener.

Rol conceptual:

```text
Beszel
→ estado rápido del host

Prometheus + Grafana
→ histórico y análisis

Uptime Kuma
→ disponibilidad
```

Agentes sugeridos:

```text
core01
devops01
k3s01
monitor01
network01
```

El Hub permanecerá inicialmente en `core01`.

Evaluar más adelante moverlo a `monitor01`.

---

# 19. Glances

Revisar una vez implementado Prometheus.

Actualmente existe solapamiento entre:

- Glances.
- Beszel.
- Prometheus.
- Proxmox monitoring.

No retirar inmediatamente.

Criterio de decisión:

- Si Homepage utiliza datos útiles de Glances, mantener.
- Si Beszel + Prometheus reemplazan completamente su función, retirar.

---

# 20. MySpeed

Plan:

1. Mantener durante despliegue de Internet-Pi.
2. Comparar resultados.
3. Validar dashboards de Grafana.
4. Si Internet-Pi cubre el caso de uso, retirar MySpeed.

Objetivo:

Reducir servicios redundantes.

---

# 21. ProxMenux Monitor

Mantener inicialmente.

Después de implementar dashboards de Proxmox en Grafana:

Evaluar si entrega información única.

Si Grafana cubre:

- CPU.
- RAM.
- storage.
- temperaturas.
- VMs.
- LXC.
- networking.
- IO.
- uptime.

entonces evaluar retirar ProxMenux Monitor.

---

# 22. Política de recursos para k3s

Todo Deployment nuevo debe definir:

```yaml
resources:
  requests:
    cpu: ...
    memory: ...
  limits:
    cpu: ...
    memory: ...
```

No crear nuevos workloads sin límites.

Ejemplo genérico:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Cada aplicación deberá ajustar valores según consumo real.

---

# 23. Futuras aplicaciones para k3s

Orden tentativo:

## 23.1 IT-Tools

Namespace:

```text
oscar-tools
```

Características:

- Muy liviano.
- Stateless.
- Útil para tareas técnicas.

---

## 23.2 SearXNG

Namespace:

```text
oscar-ai
```

Rol:

- Motor de búsqueda privado.
- Backend de búsqueda para agentes IA.
- Integración futura con n8n/Open WebUI.

---

## 23.3 Open WebUI

Namespace:

```text
oscar-ai
```

Rol:

- Front-end principal de OSCAR AI.
- Conexión con APIs externas.
- Conexión futura con modelos locales.

No desplegar inicialmente modelos LLM pesados en el Dell.

---

## 23.4 Stirling PDF

Namespace:

```text
oscar-tools
```

Rol:

- Manipulación de PDFs.
- OCR.
- conversión.
- compresión.
- integración con n8n.

Debe tener límites de recursos porque operaciones OCR pueden generar picos importantes.

---

# 24. Apps futuras en evaluación

No desplegar todavía salvo necesidad concreta:

```text
Karakeep
Paperless-ngx
MinIO
Loki
Alertmanager
VictoriaMetrics
Thanos
Ollama
```

Primero estabilizar:

- arquitectura.
- backups.
- monitoreo.
- límites.
- almacenamiento.

---

# 25. Flujo DevOps objetivo

La infraestructura de aplicaciones debe seguir:

```text
Developer
    │
    ▼
Forgejo
    │
    ▼
Forgejo Actions / Runner
    │
    ├── test
    ├── build
    ├── scan
    └── push
          │
          ▼
        Nexus
          │
          ▼
GitOps repository
          │
          ▼
       Argo CD
          │
          ▼
         k3s
```

Objetivo:

Todo servicio de k3s deberá quedar reproducible desde Git.

---

# 26. Repositorios sugeridos

Ejemplo:

```text
oscar-homelab
oscar-infra
oscar-ansible
oscar-kubernetes
oscar-monitoring
oscar-homepage
oscar-led-controller
oscar-ai
```

No es obligatorio separarlos desde el primer día.

Claude deberá evaluar si conviene:

- monorepo de infraestructura.
- repositorios independientes.
- combinación.

---

# 27. Gestión mediante Ansible

Las Raspberry Pi deberían quedar gestionadas declarativamente.

Objetivo:

```text
Ansible
├── monitor01
├── network01
├── dns02
└── futuras Raspberry Pi
```

Roles sugeridos:

```text
common
docker
node_exporter
prometheus
grafana
internet_monitor
uptime_kuma
tailscale
adguard
```

La instalación manual debe evitarse siempre que sea razonable.

---

# 28. Backups

Antes de incorporar servicios con información importante, definir estrategia de backup.

Servicios prioritarios:

```text
Vaultwarden
n8n
PostgreSQL
Forgejo
Nexus
Home Assistant
Grafana
Prometheus
AdGuard
Argo CD / manifests GitOps
```

Considerar:

- Proxmox Backup Server en el futuro.
- backup de DB.
- export/config backups.
- backup fuera del Dell.
- backup off-site.
- pruebas periódicas de restore.

---

# 29. Orden de implementación recomendado

## Fase 1 — Inventario y medición

- [ ] Medir consumo real de RAM en Proxmox.
- [ ] Medir RAM/CPU real por VM.
- [ ] Documentar uso de discos.
- [ ] Confirmar IP fija/reserva DHCP de cada host.
- [ ] Confirmar nombres DNS internos.

---

## Fase 2 — Preparar Raspberry Pi

- [ ] Instalar Raspberry Pi OS Lite 64-bit.
- [ ] Crear `monitor01`.
- [ ] Crear `network01`.
- [ ] Configurar SSH.
- [ ] Configurar hostname.
- [ ] Configurar IP fija/reserva DHCP.
- [ ] Configurar actualización base.
- [ ] Configurar Ansible.

---

## Fase 3 — Management plane

En `network01`:

- [ ] Instalar Tailscale.
- [ ] Configurar subnet router.
- [ ] Validar acceso remoto.
- [ ] Instalar Uptime Kuma.
- [ ] Migrar configuración de Kuma.
- [ ] Validar checks.
- [ ] Eliminar Kuma de `core01`.
- [ ] Eliminar subnet router Tailscale de `core01`.

---

## Fase 4 — Observability plane

En `monitor01`:

- [ ] Instalar Prometheus.
- [ ] Instalar Grafana.
- [ ] Instalar Blackbox Exporter.
- [ ] Instalar componentes de Internet-Pi.
- [ ] Instalar node_exporter.
- [ ] Configurar persistencia.
- [ ] Definir retención inicial.

---

## Fase 5 — Exporters

Agregar:

- [ ] node_exporter en `core01`.
- [ ] node_exporter en `devops01`.
- [ ] node_exporter en `k3s01`.
- [ ] node_exporter en `network01`.
- [ ] exporter de Proxmox.
- [ ] métricas de Traefik.
- [ ] métricas de Home Assistant.
- [ ] métricas de Uptime Kuma.
- [ ] métricas adicionales según necesidad.

---

## Fase 6 — Grafana

Crear dashboards:

- [ ] OSCAR Overview.
- [ ] Internet.
- [ ] Proxmox.
- [ ] Linux Hosts.
- [ ] Kubernetes.
- [ ] Home Assistant.
- [ ] Services.
- [ ] Network.

---

## Fase 7 — DNS resiliente

En Pi Zero W:

- [ ] Instalar Raspberry Pi OS Lite.
- [ ] Instalar AdGuard Home.
- [ ] Configurar como secundario.
- [ ] Sincronizar reglas/configuración cuando corresponda.
- [ ] Configurar DHCP/router con DNS primario + secundario.
- [ ] Probar apagando Proxmox.

---

## Fase 8 — Limpieza

Evaluar:

- [ ] MySpeed.
- [ ] Glances.
- [ ] ProxMenux Monitor.
- [ ] duplicaciones de dashboards.
- [ ] servicios no utilizados.

No retirar hasta que exista reemplazo probado.

---

## Fase 9 — Kubernetes

- [ ] Agregar requests/limits a workloads actuales.
- [ ] Revisar `ci-demo`.
- [ ] Revisar `oscar-led-controller`.
- [ ] Crear namespaces finales.
- [ ] Definir repositorio GitOps.
- [ ] Integrar Argo CD.
- [ ] Deploy IT-Tools.
- [ ] Deploy SearXNG.
- [ ] Deploy Open WebUI.
- [ ] Deploy Stirling PDF.

---

# 30. Criterios de aceptación

La reorganización se considerará exitosa cuando:

### Resiliencia

- [ ] Apagar Proxmox no elimina el acceso Tailscale.
- [ ] Uptime Kuma continúa funcionando.
- [ ] Grafana continúa funcionando.
- [ ] Prometheus continúa recolectando métricas externas.
- [ ] El monitoreo de Internet continúa funcionando.
- [ ] DNS continúa resolviendo mediante el secundario.

### Observabilidad

- [ ] Grafana muestra Proxmox.
- [ ] Grafana muestra hosts Linux.
- [ ] Grafana muestra Internet.
- [ ] Grafana muestra k3s.
- [ ] Grafana muestra Home Assistant.
- [ ] Grafana muestra estado general de servicios.

### Kubernetes

- [ ] Todos los Deployments tienen requests/limits.
- [ ] Aplicaciones gestionadas mediante GitOps.
- [ ] Argo CD puede reconstruir el estado deseado.

### Automatización

- [ ] Raspberry Pi configurables mediante Ansible.
- [ ] Documentación actualizada.
- [ ] Cambios reproducibles.

---

# 31. Diagrama final

```text
                               INTERNET
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
               Cloudflare                    Tailscale
                Tunnel                           │
                    │                        network01
                    │                       Raspberry Pi 3
                    │                             │
                    │                      ┌──────┴──────┐
                    │                      │             │
                    │                     Kuma       Subnet Router
                    │
                    ▼
               OSCAR LAN
                    │
       ┌────────────┼───────────────────────────────────┐
       │            │                                   │
       ▼            ▼                                   ▼
    Dell 7060    monitor01                            dns02
     Proxmox     Raspberry Pi 3                    Pi Zero W
       │            │                                   │
       │        Prometheus                           AdGuard
       │        Grafana                             Secondary
       │        Blackbox
       │        Internet-Pi
       │
 ┌─────┼───────────┬───────────┬─────────────┐
 │     │           │           │             │
 ▼     ▼           ▼           ▼             ▼
core01 devops01   k3s01       HAOS      AdGuard Primary

core01
├── Homepage
├── Nginx Proxy Manager
├── n8n
├── PostgreSQL
├── Vaultwarden
├── SMTP Relay
└── Cloudflare Tunnel

devops01
├── Forgejo
├── Forgejo Runner
└── Nexus

k3s01
├── Traefik
├── Argo CD
├── oscar-led-controller
├── IT-Tools
├── SearXNG
├── Open WebUI
└── Stirling PDF
```

---

# 32. Instrucciones para Claude

Usar este documento como **estado objetivo de arquitectura**, no como orden de ejecutar todo de una sola vez.

Para cada fase:

1. Revisar el estado actual del repositorio.
2. Compararlo con este documento.
3. Proponer cambios mínimos.
4. Crear un plan antes de modificar.
5. Evitar destruir servicios existentes sin migración validada.
6. Priorizar IaC / Ansible / GitOps.
7. Documentar cada cambio.
8. No almacenar secretos en Git.
9. Incorporar health checks.
10. Incorporar backups cuando exista estado persistente.
11. Definir CPU/RAM limits.
12. Verificar compatibilidad ARM64/ARMv7 antes de desplegar en Raspberry Pi.
13. Validar la arquitectura de red antes de cambiar DNS o Tailscale.
14. Mantener posibilidad de rollback.
15. Actualizar este documento cuando cambie la arquitectura real.

---

# 33. Prompt sugerido para Claude

```text
Actuá como arquitecto DevOps/SRE encargado de evolucionar mi homelab O.S.C.A.R.

Usá el archivo "OSCAR_TARGET_ARCHITECTURE.md" como arquitectura objetivo.

No quiero que implementes todo de golpe.

Primero:

1. revisá el estado actual del repositorio;
2. comparalo con la arquitectura objetivo;
3. identificá diferencias;
4. proponé un roadmap por fases;
5. indicá dependencias y riesgos;
6. priorizá cambios de bajo riesgo y alto impacto;
7. proponé qué automatizar con Ansible, Docker Compose, Kubernetes y Argo CD;
8. evitá duplicar servicios;
9. no elimines nada hasta que su reemplazo esté validado;
10. mantené documentación y rollback.

Cada implementación debe incluir:

- objetivo;
- arquitectura;
- archivos a crear/modificar;
- procedimiento;
- validaciones;
- rollback;
- documentación.

La prioridad inicial debe ser:

1. preparar monitor01;
2. preparar network01;
3. mover Tailscale subnet router;
4. mover Uptime Kuma;
5. desplegar Prometheus/Grafana/Internet monitoring;
6. incorporar exporters;
7. desplegar DNS secundario;
8. revisar redundancias;
9. ordenar recursos de k3s;
10. continuar con aplicaciones de OSCAR.

Antes de ejecutar cualquier cambio importante, mostrame el plan.
```

---

# 34. Principio general

O.S.C.A.R. debe evolucionar hacia una infraestructura:

```text
reproducible
observable
resiliente
documentada
automatizada
modular
recuperable
```

El objetivo no es tener la mayor cantidad posible de servicios.

El objetivo es que cada componente tenga una responsabilidad clara y que la plataforma pueda crecer sin perder control operativo.
