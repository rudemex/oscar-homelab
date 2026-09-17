# O.S.C.A.R. — Arquitectura Final Propuesta para Validación

> Documento de arquitectura objetivo para O.S.C.A.R.
>
> Este archivo representa una **propuesta final a validar**, no una orden de implementación automática. Claude debe contrastarlo con el estado real del repositorio, red, hardware y servicios antes de modificar nada.
>
> **Nota importante sobre la Raspberry Pi Zero W:** su incorporación es opcional. Puede no formar parte de la primera etapa. Si se utiliza, el rol propuesto es `edge01` para sensores, GPIO, MQTT y telemetría física del rack, salvo que durante la validación se encuentre una función mejor justificada.

---

## 1. Objetivo

O.S.C.A.R. debe evolucionar hacia una pequeña plataforma privada organizada por responsabilidades claras:

- Compute.
- Core services.
- DevOps.
- Kubernetes / Application Platform.
- Management y acceso remoto.
- Red crítica.
- Observabilidad.
- Automatización.
- Inteligencia Artificial.
- Integración física / Edge opcional.

Principios:

```text
reproducible
observable
resiliente
documentada
automatizada
modular
recuperable
```

El objetivo no es instalar la mayor cantidad posible de servicios, sino que cada componente tenga una responsabilidad concreta.

---

## 2. Hardware disponible

### Dell OptiPlex 7060 Micro — `oscar-core`

- Intel Core i7 8ª generación.
- 32 GB RAM.
- NVMe 1 TB.
- SATA SSD 1 TB.
- Proxmox VE 9.2.18.

Rol:

```text
COMPUTE PLANE
```

### Raspberry Pi

Disponibles:

```text
2 × Raspberry Pi 3
1 × Raspberry Pi Zero W
```

Distribución objetivo:

```text
Pi 3 #1      → monitor01
Pi 3 #2      → network01
Pi Zero W    → edge01 (OPCIONAL)
```

---

## 3. Estado actual de Proxmox

| VM/LXC | vCPU | RAM | Disco |
|---|---:|---:|---:|
| core01 | 2 | 8 GB | 60 GB |
| devops01 | 6 | 12 GB | 60 GB |
| k3s01 | 4 | 8 GB | 60 GB |
| haos-18.2 | 2 | 4 GB | 32 GB |
| AdGuard LXC | 1 | 512 MB | — |

Asignación nominal:

```text
core01       8 GB
devops01    12 GB
k3s01        8 GB
HAOS         4 GB
AdGuard    0.5 GB
----------------
            32.5 GB
```

Existe overcommit respecto de los 32 GB físicos.

Por lo tanto:

- medir uso real de RAM;
- evitar nuevas VMs pesadas;
- priorizar k3s para nuevas aplicaciones;
- agregar `requests` y `limits`;
- revisar presión de memoria en Proxmox.

---

# 4. Big Picture

```text
                                   INTERNET
                                      │
                                   ROUTER
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
               network01         SWITCH OSCAR         Wi-Fi
               Raspberry Pi 3         │
               directo router         │
                    │                 ├── Dell / Proxmox
            ┌───────┼───────┐         │
            │       │       │         ├── monitor01 / Pi 3
            ▼       ▼       ▼         │
         AdGuard   Kuma   Tailscale   ├── DVR
         PRIMARY          subnet      │
                          router      └── otros equipos
```

Dominios:

```text
COMPUTE
Dell / Proxmox

MANAGEMENT + NETWORK SURVIVAL
Pi 3 / network01

OBSERVABILITY
Pi 3 / monitor01

PHYSICAL / EDGE
Pi Zero W / edge01 (opcional)
```

---

# 5. Dell / `oscar-core`

El Dell contiene:

```text
Proxmox
├── core01
├── devops01
├── k3s01
├── HAOS
└── AdGuard Secondary
```

El Dell **no debe ser el único lugar** desde donde:

- se detecta si el propio Dell cayó;
- se accede remotamente a la LAN;
- se resuelve DNS;
- se almacenan las métricas principales.

---

# 6. `core01`

IP actual:

```text
192.168.0.156
```

Recursos:

```text
2 vCPU
8 GB RAM
60 GB
```

## Servicios objetivo

```text
core01
├── Homepage
├── Nginx Proxy Manager
├── n8n
├── PostgreSQL
├── Vaultwarden
├── SMTP Relay / Brevo
└── Cloudflare Tunnel
```

## Servicios a migrar

```text
Uptime Kuma
core01 → network01

Tailscale subnet router
core01 → network01
```

## Servicios a revisar más adelante

```text
Beszel Hub
Glances
MySpeed
ProxMenux Monitor
```

No eliminar ningún servicio hasta validar su reemplazo.

---

# 7. `devops01`

IP:

```text
192.168.0.151
```

Recursos:

```text
6 vCPU
12 GB RAM
60 GB
```

Rol:

```text
DEVOPS PLANE
```

Servicios:

```text
devops01
├── Forgejo
├── Forgejo Runner
├── Nexus
└── Beszel Agent
```

Flujo objetivo:

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
    ├── security scan
    └── push image
          │
          ▼
        Nexus
          │
          ▼
       GitOps
          │
          ▼
       Argo CD
          │
          ▼
         k3s
```

---

# 8. `k3s01`

IP:

```text
192.168.0.150
```

Recursos:

```text
4 vCPU
8 GB RAM
60 GB
```

Rol:

```text
APPLICATION PLATFORM
```

Mantener:

```text
k3s
Traefik
Argo CD
oscar-led-controller
ci-demo
Beszel Agent
```

Namespaces sugeridos:

```text
kube-system
argocd
oscar-system
oscar-tools
oscar-ai
oscar-apps
oscar-lab
```

Distribución propuesta:

```text
k3s01
│
├── oscar-tools
│   ├── IT-Tools
│   └── Stirling PDF
│
├── oscar-ai
│   ├── SearXNG
│   └── Open WebUI
│
└── oscar-lab
    ├── oscar-led-controller
    └── ci-demo
```

---

# 9. Política de recursos de Kubernetes

Todo workload nuevo debe definir:

```yaml
resources:
  requests:
    cpu: ...
    memory: ...
  limits:
    cpu: ...
    memory: ...
```

También deben revisarse los Deployments actuales.

No agregar workloads sin límites salvo justificación técnica explícita.

---

# 10. Aplicaciones aprobadas para corto plazo

## IT-Tools

Destino:

```text
k3s01 / oscar-tools
```

Rol:

```text
Toolbox técnica
JSON / YAML / Base64 / UUID / JWT / hashes / cron / subnetting / regex / converters
```

## SearXNG

Destino:

```text
k3s01 / oscar-ai
```

Rol:

```text
Private Search Engine
```

Integraciones futuras:

- Open WebUI.
- n8n.
- agentes IA.
- OSCAR AI.

## Open WebUI

Destino:

```text
k3s01 / oscar-ai
```

Rol:

```text
interfaz principal de OSCAR AI
```

Inicialmente debe utilizar APIs externas.

No asumir Ollama como requisito.

## Stirling PDF

Destino:

```text
k3s01 / oscar-tools
```

Funciones:

- OCR.
- merge.
- split.
- conversión.
- compresión.
- manipulación PDF.
- integración con n8n.

Debe tener límites estrictos por posibles picos de CPU/RAM.

---

# 11. Aplicaciones en evaluación

No están aprobadas automáticamente:

```text
DocuSeal
Nextcloud
Garage
Firefly III
Karakeep
Paperless-ngx
MinIO
Loki
Alertmanager
VictoriaMetrics
Thanos
Ollama
```

Separación recomendada:

### Aplicaciones de usuario

```text
Karakeep
DocuSeal
Nextcloud
Paperless-ngx
Firefly III
```

### Decisiones futuras de plataforma

```text
Garage
MinIO
Loki
Alertmanager
VictoriaMetrics
Thanos
Ollama
```

Solo incorporar cuando exista una necesidad real.

---

# 12. `network01` — Raspberry Pi 3 #2

Este es el nodo más crítico fuera del Dell.

## Conectividad

```text
Pi 3 #2
   │
Ethernet
   │
ROUTER
```

Debe conectarse **directamente al router**, no depender del switch de OSCAR.

## Servicios

```text
network01
│
├── AdGuard Home
│   └── DNS PRIMARY
│
├── Uptime Kuma
│
├── Tailscale
│   └── subnet router
│
└── node_exporter
```

Conceptualmente:

```text
network01
"¿OSCAR sigue accesible y la red sigue funcionando?"
```

---

# 13. DNS final

## DNS primario

```text
network01 / Raspberry Pi 3
AdGuard Home
```

Razones:

- mayor probabilidad de permanecer encendida que el Dell;
- independiente de Proxmox;
- conexión directa al router;
- independiente del switch principal.

## DNS secundario

```text
Dell / Proxmox
AdGuard LXC
```

Arquitectura:

```text
Router / DHCP
    │
    ├── DNS #1 → network01 / AdGuard PRIMARY
    │
    └── DNS #2 → Dell / AdGuard SECONDARY
```

### Importante

`DNS #1` y `DNS #2` no garantizan un failover estricto. Los clientes pueden utilizar cualquiera.

Por eso ambos AdGuard deben mantener configuración equivalente:

- filtros;
- blocklists;
- upstreams;
- rewrites locales;
- reglas relevantes;
- configuración de clientes cuando corresponda.

Evaluar una solución de sincronización automática.

### Bloqueado hasta diagnóstico — no ejecutar todavía (2026-09-17)

**"Queremos llegar a esta arquitectura" ≠ "podemos ejecutar este cambio hoy".**

Ya se intentó una vez poner AdGuard como DNS de toda la red vía DHCP (un solo AdGuard, ni siquiera primario+secundario) y coincidió con una caída real de throughput, `~600 Mbps → ~20 Mbps`, nunca diagnosticada — se revirtió sin entender la causa (ver `docs/red/dns-adguard.md`, sección del incidente). El diseño de arriba (primario en `network01`, secundario en el Dell) sigue siendo válido como objetivo — es mejor resiliencia que el estado actual — pero no se toca el DHCP del router hasta cerrar esto:

```text
ARQUITECTURA OBJETIVO

network01
└── AdGuard Primary

Proxmox
└── AdGuard Secondary

PERO:

❌ No modificar DHCP todavía

Fase 0
├── reproducir problema 600 → 20 Mbps
├── determinar si AdGuard era realmente la causa
├── revisar DNS upstream
├── revisar IPv4 / IPv6
├── revisar router
├── comparar resolución vs throughput
└── documentar causa raíz

↓ solo si queda validado

migrar DNS principal
```

---

# 14. Tailscale

Mover:

```text
core01 → network01
```

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

Objetivo:

```text
Dell OFF
Proxmox OFF

→ acceso remoto continúa funcionando
```

---

# 15. Uptime Kuma

Mover:

```text
core01 → network01
```

Motivo:

La herramienta encargada de detectar una caída no debe depender del host que está monitoreando.

Targets iniciales:

```text
Internet
Router
Proxmox
core01
devops01
k3s01
monitor01
network01
Home Assistant
AdGuard Primary
AdGuard Secondary
Forgejo
Nexus
n8n
Homepage
Nginx Proxy Manager
```

---

# 16. `monitor01` — Raspberry Pi 3 #1

Conectividad:

```text
Pi 3 #1
   │
Switch OSCAR
```

Rol:

```text
OBSERVABILITY PLANE
```

Servicios:

```text
monitor01
│
├── Prometheus
├── Grafana
├── Blackbox Exporter
├── Internet-Pi / Internet Monitoring
└── node_exporter
```

Conceptualmente:

```text
monitor01
"¿Cómo está OSCAR?"
```

---

# 17. Prometheus

Debe centralizar métricas de:

```text
Proxmox
core01
devops01
k3s01
network01
monitor01
Home Assistant
Traefik
Uptime Kuma
AdGuard
Internet
futuros servicios
```

Arquitectura:

```text
                         Grafana
                            ▲
                            │
                       Prometheus
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
       Proxmox          Linux Hosts           k3s
          │                 │                 │
          ├──── Home Assistant ───────────────┤
          ├──── Traefik ──────────────────────┤
          ├──── Uptime Kuma ──────────────────┤
          ├──── Internet ─────────────────────┤
          └──── Network ──────────────────────┘
```

---

# 18. Grafana

Dashboards sugeridos:

```text
OSCAR Overview
Network
Internet
Infrastructure
Proxmox
Linux Hosts
Kubernetes
Home Assistant
Services
OSCAR AI
```

Grafana debe convertirse en la interfaz histórica de observabilidad.

---

# 19. Internet Monitoring

Tomar Internet-Pi como referencia.

Métricas objetivo:

```text
Download
Upload
Ping
Jitter
Packet Loss
HTTP latency
DNS latency
Internet uptime
```

## Speedtest

La Raspberry Pi 3 no necesariamente debe ejecutar el Speedtest si la conexión supera la capacidad real de su interfaz.

Diseño preferido:

```text
monitor01
Prometheus + Grafana
        │
        │ scrape
        ▼
Speedtest exporter
host Gigabit
        │
        ▼
Internet
```

Claude debe validar dónde conviene ejecutar el Speedtest.

---

# 20. Persistencia de Prometheus

Evitar almacenamiento intensivo de largo plazo sobre microSD.

Preferir:

```text
Pi 3
├── microSD
│   └── Raspberry Pi OS Lite
│
└── USB Storage
    └── Prometheus data
```

Idealmente:

```text
USB SSD
```

Retención inicial sugerida:

```text
15 días
```

Valores de scraping orientativos:

```text
node_exporter       15s
kubernetes          15s
Home Assistant      30-60s
Uptime Kuma         30s
Internet ping       5-10s
Speedtest           30 min
```

Claude puede redefinirlos.

---

# 21. Raspberry Pi Zero W — `edge01` (OPCIONAL)

## Nota obligatoria

La Pi Zero W **puede no utilizarse**.

No debe inventarse una carga para justificar su uso.

Si se incorpora y no surge una función más valiosa durante la validación, su rol sugerido es:

```text
edge01
PHYSICAL / EDGE INTEGRATION
```

Servicios posibles:

```text
edge01
│
├── agente liviano Python/Node
├── MQTT client/publisher
├── sensores
├── GPIO
├── telemetría física
└── exporter liviano
```

Casos de uso posibles:

```text
temperatura del rack
humedad
puerta abierta/cerrada
estado de ventiladores
sensores ambientales
UPS
consumo energético
botones físicos
eventos GPIO
```

Arquitectura conceptual:

```text
Sensors
   │
edge01
   │
   ├── MQTT ───────► Home Assistant
   │
   └── metrics ────► Prometheus
                         │
                         ▼
                      Grafana
```

Ejemplo:

```text
Temperatura rack > límite
        │
        ▼
Home Assistant / n8n
        │
        ├── alerta
        │
        └── ESP32
              │
              ▼
          LEDs OSCAR
             rojo
```

---

# 22. Conectividad de `edge01`

La Pi Zero W no posee Ethernet integrado.

## Opción recomendada inicialmente

```text
Wi-Fi 2.4 GHz
```

Es suficiente para:

- sensores;
- MQTT;
- telemetría;
- métricas;
- GPIO.

No debe alojar servicios críticos.

## Ethernet opcional

Puede utilizar:

```text
Micro USB OTG
      │
USB Ethernet Adapter
      │
Switch
```

Solo si aparece una necesidad concreta.

## USB Gadget

También puede utilizar Ethernet sobre USB hacia otro host, pero no se recomienda como conexión principal porque crea una dependencia física adicional.

---

# 23. Distribución final de Raspberry Pi

```text
                 O.S.C.A.R.
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
     Pi 3 #1      Pi 3 #2      Pi Zero W
    monitor01    network01       edge01
        │            │            │
      SWITCH       ROUTER        Wi-Fi
        │          DIRECTO         │
        │            │             │
    Prometheus    AdGuard       Sensors
    Grafana       Primary       MQTT
    Blackbox      Kuma          GPIO
    Internet      Tailscale     Telemetry
    Monitoring    node_exp.     OPTIONAL
```

Responsabilidades:

```text
monitor01
"¿Cómo está OSCAR?"

network01
"¿OSCAR sigue accesible y la red sigue funcionando?"

edge01
"¿Qué está pasando físicamente en OSCAR?"
(OPCIONAL)
```

---

# 24. Home Assistant

Mantener como VM dedicada:

```text
HAOS
```

Responsabilidades:

```text
Home Assistant
├── dispositivos
├── sensores
├── automatizaciones
├── energía
└── IoT
```

Integraciones futuras:

```text
Prometheus
n8n
edge01
ESP32
```

---

# 25. OSCAR LED Controller

Mantener inicialmente en:

```text
k3s01 / oscar-lab
```

Puede recibir eventos desde:

```text
n8n
Home Assistant
monitoring
CI/CD
manual API
```

Estados disponibles / previstos:

```text
breathing
pulse
deploying
booting
success
aurora
rainbow
critical
```

Ejemplo conceptual:

```text
idle       → aurora
deploying  → amarillo
success    → verde
critical   → rojo
```

---

# 26. Homepage

Homepage continúa como portal principal de OSCAR.

Puede mostrar acceso y estado de:

```text
Grafana
Forgejo
n8n
Argo CD
Proxmox
Home Assistant
Uptime Kuma
Open WebUI
SearXNG
Stirling PDF
IT-Tools
Nexus
```

También puede ser la interfaz principal de la pantalla física de 9 pulgadas del rack.

---

# 27. OSCAR AI

Alineado con `docs/ia/vision-general.md` (fuente de verdad de esta sección — si diverge de acá, gana ese doc). Describe las **capacidades** de OSCAR AI, no el recorrido técnico de una request:

```text
                      Open WebUI
                          ▲
                          │
          ┌───────────────┼───────────────┐
          │               │               │
       SearXNG         Karakeep           n8n
          │               │               │
          ▼               ▼               ▼
       Internet        Knowledge        Actions
                                          │
                           ┌──────────────┼──────────────┐
                           ▼              ▼              ▼
                         HAOS         OSCAR APIs       Infra
```

Detrás de Open WebUI:

```text
LLM providers
├── OpenAI
├── Anthropic
└── otros
```

Roles:

```text
Open WebUI = interfaz
LLM APIs   = razonamiento
SearXNG    = búsqueda externa
Karakeep   = conocimiento guardado
n8n        = acciones / herramientas
HAOS       = hogar / IoT
```

**Salvedad:** `Karakeep` sigue sin estar aprobado para instalar (ver sección 11) — participa de la arquitectura conceptual de OSCAR AI sin que eso implique desplegarlo ahora.

No desplegar LLMs locales pesados inicialmente.

Posibles extensiones futuras:

```text
Qdrant / RAG
Ollama
MCP
Proxmox tooling
GitOps tooling
```

Solo incorporar según casos de uso concretos.

---

# 28. Herramientas de monitoreo existentes

## Beszel

Mantener inicialmente.

Separación conceptual:

```text
Beszel
→ estado rápido

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

Mover el Hub a `monitor01` solo si existe beneficio real.

## Glances

Revisar después de desplegar Prometheus.

```text
si aporta valor único / Homepage lo usa
→ mantener

si queda totalmente reemplazado
→ retirar
```

## MySpeed

```text
1. mantener
2. implementar Internet Monitoring
3. comparar
4. validar Grafana
5. retirar si queda redundante
```

## ProxMenux Monitor

Mantener temporalmente.

Evaluar después de construir dashboards de Proxmox en Grafana.

---

# 29. Arquitectura final consolidada

```text
                                  INTERNET
                                     │
                                  ROUTER
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              network01         SWITCH OSCAR        Wi-Fi
              Raspberry Pi 3         │
              directo router         │
                    │                ├── Dell 7060
            ┌───────┼───────┐        │     │
            │       │       │        │     └── Proxmox
            ▼       ▼       ▼        │
         AdGuard   Kuma   Tailscale  ├── monitor01
         PRIMARY          subnet     │    Raspberry Pi 3
                          router     │        │
                                    │     Prometheus
                                    │     Grafana
                                    │     Blackbox
                                    │     Internet Monitoring
                                    │
                                    ├── DVR
                                    └── otros equipos


Dell / Proxmox
│
├── core01
│   ├── Homepage
│   ├── Nginx Proxy Manager
│   ├── n8n
│   ├── PostgreSQL
│   ├── Vaultwarden
│   ├── SMTP Relay
│   └── Cloudflare Tunnel
│
├── devops01
│   ├── Forgejo
│   ├── Forgejo Runner
│   └── Nexus
│
├── k3s01
│   ├── Traefik
│   ├── Argo CD
│   ├── oscar-led-controller
│   ├── IT-Tools
│   ├── Stirling PDF
│   ├── SearXNG
│   └── Open WebUI
│
├── HAOS
│
└── AdGuard SECONDARY


OPCIONAL

Pi Zero W / edge01
│
├── Wi-Fi
├── Sensors
├── MQTT
├── GPIO
└── Telemetry
```

---

# 30. Capas finales

```text
1. HARDWARE
Dell + Raspberry Pi + ESP32 + networking + storage

2. VIRTUALIZATION
Proxmox

3. CORE SERVICES
core01

4. DEVOPS
Forgejo + Runner + Nexus + Argo CD

5. APPLICATION PLATFORM
k3s + Traefik + GitOps

6. MANAGEMENT
network01 + Tailscale + Uptime Kuma

7. NETWORK RESILIENCE
AdGuard Primary / Pi 3
AdGuard Secondary / Dell

8. OBSERVABILITY
monitor01 + Prometheus + Grafana + Blackbox + Internet Monitoring + Beszel

9. AUTOMATION
n8n + Home Assistant

10. AI
Open WebUI + SearXNG + LLM APIs + futuros agentes

11. PHYSICAL / EDGE
edge01 / Pi Zero W (OPCIONAL)
```

---

# 31. Orden de implementación recomendado

## Fase 1 — Validación

- [ ] Inventario real.
- [ ] Consumo de CPU/RAM.
- [ ] IPs y DHCP reservations.
- [ ] Topología router/switch.
- [ ] versiones.
- [ ] backups actuales.

## Fase 2 — `network01`

- [ ] Raspberry Pi OS Lite.
- [ ] Ethernet directo al router.
- [ ] hostname e IP reservada/fija.
- [ ] AdGuard Primary.
- [ ] sincronización con AdGuard Secondary.
- [ ] Tailscale subnet router.
- [ ] Uptime Kuma.
- [ ] node_exporter.
- [ ] validar funcionamiento con Proxmox apagado.

## Fase 3 — `monitor01`

- [ ] Raspberry Pi OS Lite.
- [ ] conexión al switch.
- [ ] Prometheus.
- [ ] Grafana.
- [ ] Blackbox Exporter.
- [ ] Internet monitoring.
- [ ] almacenamiento persistente.
- [ ] node_exporter.

## Fase 4 — Exporters / métricas

- [ ] Proxmox.
- [ ] core01.
- [ ] devops01.
- [ ] k3s01.
- [ ] network01.
- [ ] monitor01.
- [ ] Home Assistant.
- [ ] Traefik.
- [ ] Uptime Kuma.
- [ ] AdGuard si aplica.

## Fase 5 — Dashboards Grafana

- [ ] OSCAR Overview.
- [ ] Internet.
- [ ] Network.
- [ ] Proxmox.
- [ ] Linux Hosts.
- [ ] Kubernetes.
- [ ] Home Assistant.
- [ ] Services.

## Fase 6 — Limpieza

Evaluar:

- [ ] MySpeed.
- [ ] Glances.
- [ ] ProxMenux Monitor.
- [ ] Beszel Hub location.
- [ ] duplicaciones.

## Fase 7 — Kubernetes

- [ ] agregar requests/limits.
- [ ] ordenar namespaces.
- [ ] validar GitOps.
- [ ] IT-Tools.
- [ ] Stirling PDF.
- [ ] SearXNG.
- [ ] Open WebUI.

## Fase 8 — `edge01` OPCIONAL

Solo si existe caso de uso real:

- [ ] validar si `edge01` sigue siendo el rol correcto.
- [ ] Wi-Fi.
- [ ] agente mínimo.
- [ ] sensores.
- [ ] MQTT.
- [ ] métricas.
- [ ] Home Assistant.

Si no existe necesidad:

```text
NO desplegar edge01 todavía.
```

---

# 32. Resiliencia esperada

Si el Dell se apaga:

```text
OFF
Dell
Proxmox
core01
devops01
k3s01
HAOS
AdGuard Secondary
```

Deben seguir vivos:

```text
ON
network01
AdGuard Primary
Tailscale
Uptime Kuma
monitor01
Prometheus
Grafana
Internet Monitoring
```

Si falla el switch:

```text
network01
```

debe seguir conectado al router.

---

# 33. Criterios de aceptación

## Red

- [ ] DNS primario corre fuera del Dell.
- [ ] DNS funciona con Proxmox apagado.
- [ ] Tailscale funciona con Proxmox apagado.
- [ ] Uptime Kuma funciona con Proxmox apagado.

## Observabilidad

- [ ] Prometheus corre fuera del Dell.
- [ ] Grafana corre fuera del Dell.
- [ ] Internet está monitoreado.
- [ ] Proxmox está monitoreado.
- [ ] VMs están monitoreadas.
- [ ] k3s está monitoreado.

## Kubernetes

- [ ] workloads relevantes tienen requests/limits.
- [ ] Argo CD administra las apps correspondientes.
- [ ] estado deseado reproducible desde Git.

## DevOps

- [ ] Forgejo → Runner → Nexus → GitOps → Argo CD validado.

## Operación

- [ ] secretos fuera de Git.
- [ ] documentación actualizada.
- [ ] rollback definido para cambios importantes.
- [ ] backups de componentes persistentes.

---

# 34. Instrucciones para Claude

Usar este documento como **arquitectura objetivo propuesta**, no como especificación inmutable.

Antes de cambiar nada:

1. revisar estado real del repositorio;
2. revisar documentación existente;
3. validar hardware;
4. validar red;
5. detectar inconsistencias;
6. identificar riesgos y SPOFs;
7. proponer mejoras;
8. mantener separación de dominios de falla;
9. evitar complejidad innecesaria;
10. priorizar Ansible, GitOps y configuración reproducible.

Especialmente:

```text
Pi Zero W / edge01 = OPCIONAL
```

Su rol es solo una propuesta.

Puede:

- no utilizarse;
- incorporarse más adelante;
- cambiar de función;

si existe una justificación técnica mejor.

No inventar una carga solo para aprovechar hardware disponible.

---

# 35. Prompt sugerido para Claude

```text
Actuá como arquitecto DevOps/SRE encargado de validar y evolucionar mi homelab O.S.C.A.R.

Usá OSCAR_FINAL_INFRASTRUCTURE.md como arquitectura objetivo propuesta, pero no como una especificación inmutable.

Primero quiero que revises y valides la arquitectura completa.

Analizá:

1. el estado real del repositorio;
2. la distribución entre Dell, VMs, Kubernetes y Raspberry Pi;
3. network01 conectado directamente al router;
4. AdGuard Primary en network01 y Secondary en Proxmox;
5. Tailscale subnet router fuera del Dell;
6. Uptime Kuma fuera del Dell;
7. monitor01 con Prometheus/Grafana/Blackbox/Internet monitoring;
8. capacidad de las Raspberry Pi 3;
9. almacenamiento de Prometheus;
10. requests/limits de k3s;
11. redundancias actuales;
12. dominios de falla;
13. backups y rollback;
14. qué conviene automatizar con Ansible;
15. qué debe gestionarse con GitOps/Argo CD.

No implementes todo de golpe.

Primero entregame:

- evaluación de arquitectura;
- inconsistencias encontradas;
- riesgos;
- mejoras propuestas;
- dependencias;
- roadmap recomendado por fases.

IMPORTANTE SOBRE LA PI ZERO W:

La Pi Zero W es opcional.

Su función propuesta es:

edge01 = sensores + GPIO + MQTT + telemetría física.

No quiero usarla solo porque está disponible.

Si no aporta valor todavía, dejala sin desplegar.

Si encontrás un rol mejor, proponelo y explicá por qué.

APLICACIONES APROBADAS PARA CORTO PLAZO:

- IT-Tools
- SearXNG
- Open WebUI
- Stirling PDF

EL RESTO SIGUE EN EVALUACIÓN:

- DocuSeal
- Nextcloud
- Garage
- Firefly III
- Karakeep
- Paperless-ngx
- MinIO
- Loki
- Alertmanager
- VictoriaMetrics
- Thanos
- Ollama

No instales nada de esta segunda lista sin una necesidad explícita.

Para cada cambio importante quiero:

- objetivo;
- diseño;
- impacto;
- archivos a crear/modificar;
- procedimiento;
- validaciones;
- rollback;
- actualización de documentación.

Mantener secretos fuera del repositorio.
```

---

# 36. Principio final

Antes de incorporar cualquier componente, responder:

```text
¿Agrega una capacidad real,
reduce un riesgo
o mejora la operabilidad?
```

Si la respuesta es no:

```text
no instalarlo todavía.
```

La meta de O.S.C.A.R. es una plataforma pequeña, clara y sólida; no una colección de contenedores.
