# O.S.C.A.R. AI — Especificación de Hermes Agent

> **Estado:** Propuesta para validación e implementación por fases  
> **Fecha:** 2026-09-17  
> **Objetivo:** incorporar Hermes Agent como runtime/orquestador principal de la capa de IA de O.S.C.A.R.
>
> Este documento debe tratarse como una **especificación objetivo a validar**, no como una instrucción para desplegar todo automáticamente.
>
> Claude debe comparar esta propuesta con el estado real del repositorio, la infraestructura, las versiones instaladas y las capacidades de hardware antes de implementar cambios.

---

# 1. Decisión propuesta

Incorporar **Hermes Agent** como el agente principal de O.S.C.A.R.

Hermes será el componente encargado de:

- recibir consultas desde Open WebUI;
- razonar sobre el estado de O.S.C.A.R.;
- consultar Internet mediante SearXNG;
- consultar observabilidad;
- consultar disponibilidad;
- consultar Home Assistant;
- delegar tareas de coding a Codex y Claude Code;
- invocar acciones controladas mediante n8n/MCP;
- utilizar memoria/skills de manera acotada;
- convertirse progresivamente en la capa conversacional-operativa de O.S.C.A.R.

Hermes **NO** debe desplegarse inicialmente con permisos administrativos irrestrictos.

Principio:

```text
Hermes puede observar mucho.
Hermes puede modificar poco.
```

La capacidad de escritura se ampliará solamente después de validar cada integración y sus guardrails.

---

# 2. Objetivo conceptual

O.S.C.A.R. AI no debe ser simplemente:

```text
Open WebUI
    ↓
LLM
```

La arquitectura objetivo es:

```text
                         USUARIO
                            │
               ┌────────────┴────────────┐
               │                         │
          Open WebUI                 Telegram*
               │                         │
               └────────────┬────────────┘
                            ▼
                  ┌──────────────────┐
                  │   HERMES AGENT   │
                  │      OSCAR       │
                  └────────┬─────────┘
                           │
       ┌───────────────────┼─────────────────────┐
       │                   │                     │
       ▼                   ▼                     ▼
     LLMs               SearXNG                 n8n
  Reasoning             Internet              Actions
       │                                          │
       │                           ┌──────────────┼──────────────┐
       │                           ▼              ▼              ▼
       │                         HAOS          GitOps        OSCAR APIs
       │
       ├──────────────► Prometheus
       ├──────────────► Uptime Kuma
       ├──────────────► Grafana / availability
       ├──────────────► Forgejo
       ├──────────────► k3s read-only
       └──────────────► Karakeep*
```

`*` Opcional / futuro / todavía no aprobado para instalación.

---

# 3. Qué representa cada componente

```text
Open WebUI
= interfaz humana

Hermes Agent
= cerebro/orquestador

LLM providers
= razonamiento

Codex
= agente especializado en coding

Claude Code
= agente especializado en coding/review

SearXNG
= búsqueda externa

Prometheus
= métricas históricas

Uptime Kuma
= disponibilidad de servicios

Grafana
= visualización y análisis

n8n
= action broker / automatización

Home Assistant
= hogar / IoT

Forgejo
= código y Git

Argo CD
= GitOps

Karakeep
= knowledge layer futuro
```

---

# 4. Ubicación en la infraestructura

Hermes NO debe instalarse en:

```text
network01
monitor01
edge01
```

Estos nodos tienen otras responsabilidades y deben mantenerse simples y estables.

Ubicación propuesta:

```text
k3s01
namespace: oscar-ai
```

Arquitectura inicial:

```text
k3s01

oscar-ai
├── hermes-agent
├── open-webui
└── searxng
```

Open WebUI y SearXNG ya estaban considerados como aplicaciones aprobadas para corto plazo.

Hermes se incorpora como el runtime que conecta ambas piezas con el resto de O.S.C.A.R.

---

# 5. Recursos iniciales sugeridos

Los valores deben validarse midiendo consumo real.

Punto de partida para Hermes:

```yaml
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: "1"
    memory: 2Gi
```

Esto NO es un requerimiento oficial.

Es solamente un punto de partida para evitar que Hermes compita sin límites con el resto de k3s01.

Claude debe medir y ajustar.

---

# 6. Persistencia

Hermes necesitará persistencia para elementos como:

- configuración;
- perfiles;
- skills;
- memoria;
- autenticaciones OAuth;
- MCP configuration;
- estado propio que deba sobrevivir reinicios.

No almacenar datos persistentes importantes dentro del filesystem efímero del Pod.

Debe definirse un PVC específico.

Ejemplo conceptual:

```text
hermes-data
```

No guardar secretos directamente en ConfigMaps ni en Git.

---

# 7. Open WebUI

Open WebUI será la interfaz web principal para hablar con OSCAR.

Flujo:

```text
Usuario
   │
   ▼
Open WebUI
   │
   │ OpenAI-compatible API
   ▼
Hermes API Server
   │
   ▼
Hermes Agent
```

Hermes dispone de API compatible con OpenAI para integrarse con Open WebUI.

Puerto por defecto documentado actualmente:

```text
8642
```

El servicio debe quedar accesible solamente dentro del cluster o la red interna correspondiente.

No exponer la API de Hermes directamente a Internet.

---

# 8. Flujo de una consulta

Ejemplo:

```text
"OSCAR, ¿cómo está el homelab?"
```

Flujo esperado:

```text
Open WebUI
    │
    ▼
Hermes
    │
    ├── consulta Prometheus
    ├── consulta Uptime Kuma
    ├── consulta disponibilidad
    ├── consulta k3s
    └── consulta otros targets permitidos
            │
            ▼
       respuesta consolidada
```

Ejemplo de salida conceptual:

```text
Todos los servicios críticos están disponibles.

Disponibilidad global 24h: 99.98 %
Disponibilidad global 7d: 99.91 %

k3s01
CPU: 31 %
RAM: 5.6 / 8 GB

Internet
Ping: 12 ms

Advertencias:
- Nexus alcanzó uso elevado de disco.
- Stirling PDF tuvo una interrupción breve durante las últimas 24 h.
```

Los números siempre deben provenir de métricas reales.

Hermes NO debe inferir disponibilidad a partir del lenguaje del usuario ni del historial del chat.

---

# 9. Medidor de disponibilidad — REQUERIMIENTO OBLIGATORIO

Además de monitorear estado actual, O.S.C.A.R. debe incorporar un **medidor histórico de disponibilidad**.

Este medidor debe responder:

```text
¿Está funcionando ahora?
¿Durante cuánto tiempo estuvo disponible?
¿Qué servicio tuvo más caídas?
¿Cuánto downtime tuvo?
¿Cuál fue la disponibilidad global?
```

Ventanas iniciales:

```text
24 horas
7 días
30 días
```

Opcionalmente después:

```text
90 días
1 año
```

---

# 10. Fuente del medidor de disponibilidad

Fuente primaria propuesta:

```text
Uptime Kuma
      │
      │ /metrics
      ▼
Prometheus
      │
      ▼
Grafana
```

Uptime Kuma expone métricas compatibles con Prometheus, incluyendo:

```text
monitor_status
monitor_response_time
```

Prometheus debe scrapear el endpoint `/metrics` de Uptime Kuma.

No exponer `/metrics` públicamente.

---

# 11. Métricas de disponibilidad

Crear métricas/dashboards para:

```text
availability_current
availability_24h
availability_7d
availability_30d

downtime_24h
downtime_7d
downtime_30d

incident_count_24h
incident_count_7d
incident_count_30d
```

No necesariamente deben existir como nuevas métricas almacenadas.

Pueden calcularse mediante PromQL/dashboard queries cuando corresponda.

Claude debe validar primero la semántica real de `monitor_status` en la versión instalada de Uptime Kuma.

Ejemplo conceptual si el estado es binario 0/1:

```promql
avg_over_time(monitor_status{monitor_name="Forgejo"}[7d]) * 100
```

NO copiar esta consulta sin validarla contra los datos reales.

---

# 12. Disponibilidad global de OSCAR

Debe existir una vista agregada.

No todos los servicios tienen la misma importancia.

Separar al menos:

## Critical

```text
Internet
Router
network01
AdGuard Primary
Tailscale
Proxmox
```

## Core

```text
core01
k3s01
devops01
Home Assistant
Nginx Proxy Manager
n8n
```

## Applications

```text
Forgejo
Nexus
Homepage
Open WebUI
Hermes
SearXNG
Stirling PDF
IT-Tools
otros
```

La disponibilidad global NO debe ocultar una caída de un servicio crítico mediante el promedio de servicios secundarios.

Claude debe proponer una fórmula clara.

Opciones posibles:

```text
- disponibilidad del conjunto Critical;
- worst-service availability;
- promedio ponderado;
- porcentaje por categoría;
```

Preferencia inicial:

```text
mostrar categorías por separado
+
un indicador global claramente documentado
```

No definir un SLO rígido todavía.

Primero medir.

---

# 13. Dashboard de disponibilidad

Crear un dashboard específico:

```text
OSCAR Availability
```

Debe mostrar como mínimo:

```text
Disponibilidad global actual

Critical
├── 24h
├── 7d
└── 30d

Core
├── 24h
├── 7d
└── 30d

Applications
├── 24h
├── 7d
└── 30d

Top downtime
Top incidents
Response time
Timeline de incidentes
```

Semáforo visual:

```text
UP
DEGRADED
DOWN
UNKNOWN
```

Los thresholds deben definirse posteriormente.

---

# 14. Homepage y disponibilidad

Homepage debe mostrar un resumen pequeño del estado.

Ejemplo:

```text
O.S.C.A.R.

Critical availability 24h
99.98 %

Critical availability 7d
99.92 %

Services
18 / 19 UP
```

Homepage no reemplaza Grafana.

Debe actuar como resumen.

---

# 15. Hermes y disponibilidad

Hermes debe poder contestar consultas como:

```text
"¿Cuál fue la disponibilidad de OSCAR esta semana?"

"¿Qué servicio tuvo más downtime este mes?"

"¿Cuánto tiempo estuvo caído Forgejo?"

"¿Hubo alguna interrupción anoche?"

"¿Cómo estuvo Internet durante los últimos 7 días?"

"¿Por qué bajó la disponibilidad de k3s?"
```

El flujo debe utilizar datos reales:

```text
Hermes
   │
   ▼
Prometheus
   │
   ├── Kuma metrics
   ├── node metrics
   └── Internet metrics
```

Para diagnósticos:

```text
Hermes
   │
   ├── disponibilidad
   ├── métricas
   ├── logs permitidos
   └── deployments
```

Hermes debe diferenciar:

```text
HECHO
→ basado en métricas

HIPÓTESIS
→ interpretación del agente
```

Ejemplo:

```text
Hecho:
Stirling PDF estuvo indisponible 11 minutos.

Hipótesis:
La interrupción coincide con un pico de memoria y un reinicio del Pod.
```

---

# 16. OpenAI / ChatGPT / Codex

Objetivo inicial:

```text
usar la suscripción ChatGPT/Codex cuando sea posible
```

Hermes soporta autenticación OAuth para su provider:

```text
openai-codex
```

Conceptualmente:

```text
Hermes
   │
   ▼
Codex OAuth
   │
   ▼
Cuenta ChatGPT
```

No asumir que una suscripción ChatGPT equivale a una API key genérica de OpenAI.

Son mecanismos distintos.

---

# 17. Codex CLI

Además del provider principal, Hermes puede delegar tareas a Codex CLI.

Flujo:

```text
Hermes
   │
   ▼
Codex CLI
   │
   ▼
repo Git
```

Casos de uso:

```text
implementar cambios;
refactorizar;
crear tests;
resolver errores;
analizar código;
generar patches.
```

Codex debe ejecutarse dentro de un repositorio Git.

No darle acceso indiscriminado a todo el filesystem.

---

# 18. Claude Code

Claude Code será el segundo coding agent.

Hermes puede delegar tareas a Claude Code CLI.

Autenticación esperada:

```text
Claude Pro / Max
      │
      ▼
Claude Code OAuth
```

Flujo:

```text
Hermes
   │
   ▼
Claude Code
   │
   ▼
repo Git
```

Casos de uso:

```text
code review;
arquitectura;
refactor;
investigación de repositorio;
implementación;
validación.
```

---

# 19. Importante: Claude nativo vs Claude Code

No confundir:

```text
Hermes usando Claude como provider nativo
```

con:

```text
Hermes delegando una tarea a Claude Code
```

Para la primera implementación se prefiere:

```text
Claude Code CLI
```

utilizando la autenticación de la cuenta Claude disponible.

No configurar automáticamente facturación Anthropic API.

Actualmente la autenticación OAuth nativa de Anthropic en Hermes tiene restricciones diferentes y puede requerir Claude Max con extra usage.

Por lo tanto:

```text
NO asumir API billing.
NO crear ANTHROPIC_API_KEY automáticamente.
NO habilitar extra usage sin decisión explícita.
```

---

# 20. Estrategia inicial de modelos

Configuración deseada inicialmente:

```text
Hermes main provider
→ OpenAI Codex / ChatGPT OAuth

Coding agents
├── Codex CLI
└── Claude Code CLI
```

Más adelante puede evaluarse:

```text
OpenAI API
Anthropic API
OpenRouter
otros providers
```

No incorporar gasto API recurrente sin necesidad.

---

# 21. SearXNG

SearXNG será el backend de búsqueda web de OSCAR.

Arquitectura:

```text
Hermes
   │
   ▼
SearXNG
   │
   ▼
Internet
```

Variable esperada:

```text
SEARXNG_URL
```

Hermes soporta SearXNG como backend de `web_search`.

SearXNG es búsqueda.

No asumir que cubre extracción completa de contenido de páginas.

Si se requiere extracción web avanzada, evaluar un backend separado posteriormente.

---

# 22. n8n como Action Broker

Hermes NO debe ejecutar inicialmente acciones sensibles directamente sobre toda la infraestructura.

Preferencia:

```text
Hermes
   │
   ▼
n8n / MCP
   │
   ▼
workflow controlado
   │
   ▼
acción
```

Ejemplos de workflows futuros:

```text
oscar.get-status
oscar.get-availability
oscar.restart-deployment
oscar.switch-led-mode
oscar.run-backup
oscar.check-dns
oscar.deploy-application
oscar.get-proxmox-status
```

---

# 23. n8n y permisos

Separar:

## Read-only

```text
get status
get metrics
get deployments
get availability
get Home Assistant entities
get DNS status
```

## Mutating

```text
restart
deploy
scale
change configuration
trigger backup
control physical devices
```

Las acciones mutables deben tener guardrails adicionales.

---

# 24. Home Assistant

Hermes puede integrarse con Home Assistant.

Casos de uso:

```text
"¿Qué temperatura tiene el rack?"

"¿Está abierta la puerta?"

"¿Qué sensores están offline?"

"Poné OSCAR en modo aurora."
```

Inicialmente priorizar acceso read-only.

Las llamadas que modifiquen dispositivos deben incorporarse después.

---

# 25. ESP32 / LEDs

Integración futura:

```text
Hermes
   │
   ▼
n8n / Home Assistant
   │
   ▼
oscar-led-controller
   │
   ▼
ESP32
```

Ejemplos:

```text
deploying → amarillo
success   → verde
critical  → rojo
idle      → aurora
```

Hermes no necesita hablar directamente con el ESP32.

---

# 26. Prometheus

Prometheus será una de las principales fuentes de verdad operacional de Hermes.

Hermes debe poder obtener información como:

```text
CPU
RAM
disk
network
latency
availability
k3s
Internet
Home Assistant
service health
```

No otorgar a Hermes permisos para modificar Prometheus.

---

# 27. Uptime Kuma

Uptime Kuma corre en:

```text
network01
```

Será la fuente principal de estado sintético de servicios.

Debe monitorear:

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
Open WebUI
Hermes
SearXNG
Stirling PDF
IT-Tools
```

La lista debe ajustarse a servicios realmente instalados.

---

# 28. Grafana

Grafana será el front-end de observabilidad.

Dashboards importantes:

```text
OSCAR Overview
OSCAR Availability
Internet
Proxmox
Linux Hosts
Kubernetes
Home Assistant
Services
OSCAR AI
```

---

# 29. Dashboard OSCAR AI

Crear cuando existan métricas suficientes.

Posibles paneles:

```text
Hermes status
Hermes response time
requests
errors
Open WebUI status
SearXNG status
LLM provider availability
n8n tool calls
availability queries
coding-agent executions
```

No agregar métricas inexistentes artificialmente.

---

# 30. Karakeep — futuro

Karakeep sigue EN EVALUACIÓN.

No instalar como parte automática de este proyecto.

Rol conceptual futuro:

```text
SearXNG
"¿Qué existe afuera?"

Karakeep
"¿Qué guardamos nosotros?"

Prometheus
"¿Qué está pasando?"

Uptime Kuma
"¿Está funcionando?"

n8n
"¿Qué puedo hacer?"

Hermes
"¿Qué significa y qué hago?"
```

Si Karakeep se incorpora:

```text
Hermes
   │
   ▼
Karakeep
   │
   ▼
knowledge personal / técnico
```

---

# 31. MCP

Hermes soporta MCP.

Usarlo para conectar herramientas externas cuando sea el mecanismo adecuado.

Principio:

```text
exponer solo las tools necesarias
```

Evitar:

```text
un MCP gigante con acceso irrestricto a toda la infraestructura
```

Preferir:

```text
servidores separados;
tool filtering;
mínimo privilegio;
read-only cuando sea posible.
```

---

# 32. Seguridad — principios obligatorios

Hermes combina:

```text
LLM
+
tools
+
shell
+
credenciales
+
infraestructura
```

Por lo tanto debe considerarse un componente de alto impacto.

No desplegar sin guardrails.

---

# 33. Accesos permitidos inicialmente

## Lectura

```text
Prometheus             ✅
Uptime Kuma            ✅
Grafana / availability ✅
SearXNG                ✅
Home Assistant state   ✅
Forgejo read           ✅
k3s status             ✅
documentación          ✅
```

---

# 34. Accesos NO permitidos inicialmente

```text
Proxmox root             ❌
SSH root                 ❌
Kubernetes cluster-admin ❌
Docker socket            ❌
router admin             ❌
AdGuard admin            ❌
host filesystem total    ❌
arbitrary secrets        ❌
```

---

# 35. Acciones con aprobación

Ejemplos:

```text
reiniciar deployment
hacer deploy
escalar workload
modificar Home Assistant
cambiar LEDs
ejecutar backup
modificar Git
```

Deben requerir:

```text
allowlist
and/or
approval
and/or
workflow n8n controlado
```

---

# 36. Kubernetes RBAC

Hermes NO debe usar:

```text
cluster-admin
```

Crear ServiceAccount dedicado.

Ejemplo conceptual:

```text
hermes-agent
```

Rol inicial:

```text
get
list
watch
```

sobre recursos necesarios.

No habilitar:

```text
delete
patch
update
create
```

hasta que exista un caso de uso concreto y controlado.

---

# 37. Docker socket

No montar:

```text
/var/run/docker.sock
```

dentro de Hermes.

Si Hermes necesita ejecutar operaciones de infraestructura:

```text
Hermes
   │
   ▼
n8n / API / GitOps
```

No usar acceso directo al daemon Docker.

---

# 38. Red

Hermes no necesita:

```text
hostNetwork: true
```

No habilitar salvo justificación fuerte.

Aplicar NetworkPolicies si el cluster y CNI lo permiten.

Permitir solamente destinos necesarios.

---

# 39. Secrets

Nunca almacenar en Git:

```text
OAuth tokens
API keys
Home Assistant tokens
n8n credentials
MCP secrets
Open WebUI secret
Hermes API key
```

Utilizar Kubernetes Secrets o mecanismo equivalente.

Evaluar secret management mejor más adelante.

---

# 40. Auth entre Open WebUI y Hermes

Open WebUI debe utilizar un token dedicado para hablar con Hermes.

Ejemplo conceptual:

```text
OPENAI_API_BASE_URL
→ http://hermes-agent:8642/v1

OPENAI_API_KEY
→ secret dedicado
```

No reutilizar tokens personales innecesariamente.

---

# 41. Acceso externo

No exponer Hermes API directamente mediante Cloudflare Tunnel.

Si se requiere acceso remoto:

```text
usuario
  │
Tailscale
  │
Open WebUI
  │
Hermes
```

o mediante una capa de autenticación explícitamente diseñada.

---

# 42. Telegram

Telegram es una posible segunda interfaz.

No es requisito para la primera PoC.

Fase futura:

```text
Open WebUI
+
Telegram
```

No habilitar WhatsApp inicialmente salvo necesidad.

---

# 43. WhatsApp

Hermes soporta integraciones de mensajería, pero no es objetivo de la primera implementación.

Si se evalúa WhatsApp:

- priorizar mecanismos oficiales cuando sea posible;
- documentar riesgos de bridges no oficiales;
- no mezclarlo inicialmente con Evolution API u otros servicios sin diseño previo.

---

# 44. Flujo de coding — Codex

Ejemplo:

```text
Usuario:
"OSCAR, corregí este bug."

Hermes
   │
   ▼
analiza tarea
   │
   ▼
Codex
   │
   ▼
working tree aislado
   │
   ▼
diff
   │
   ▼
Hermes
```

No hacer push automático inicialmente.

---

# 45. Flujo de coding — Codex + Claude Code

Caso futuro:

```text
Hermes
   │
   ├── Codex
   │      └── implementación
   │
   ▼
diff
   │
   └── Claude Code
          └── review
```

Resultado:

```text
implementación
+
segunda revisión independiente
```

No automatizar merge sin decisión explícita.

---

# 46. Repositorios

Hermes no debe acceder a todos los repositorios por defecto.

Crear allowlist.

Repositorios reales (corregido 2026-09-17 — la spec original mencionaba `oscar-kubernetes`, que no existe, y trataba `oscar-led-controller` como repo aparte cuando en realidad es una subcarpeta dentro de `oscar-homelab`):

```text
oscar-homelab   (docs + apps/oscar-led-controller/)
oscar-gitops    (manifiestos k3s / GitOps)
```

Solo dos repos reales hoy. Ajustar si en el futuro se separa algo a un repo propio — no es obligatorio hacerlo desde el día uno.

---

# 47. GitOps

Para cambios Kubernetes:

```text
Hermes
   │
   ▼
coding agent
   │
   ▼
Git
   │
   ▼
Forgejo
   │
   ▼
Argo CD
   │
   ▼
k3s
```

Preferir esta ruta sobre:

```text
Hermes → kubectl apply
```

para cambios persistentes.

Esto mantiene:

- audit trail;
- rollback;
- reproducibilidad;
- revisión.

---

# 48. Observabilidad de Hermes

Hermes debe ser monitoreado igual que cualquier otro servicio.

Uptime Kuma:

```text
Hermes API health
Open WebUI
SearXNG
```

Prometheus/Grafana:

- recursos del Pod;
- restarts;
- disponibilidad;
- errores disponibles;
- latencias disponibles.

No inventar exporters si Hermes no los soporta.

Utilizar métricas de Kubernetes y checks sintéticos como base.

---

# 49. Logging

No enviar logs sensibles a sistemas externos.

Revisar que no aparezcan:

```text
OAuth tokens
API keys
authorization headers
passwords
secret values
```

Loki sigue siendo una decisión futura de plataforma.

No instalar Loki automáticamente para este proyecto.

---

# 50. PoC — alcance obligatorio

La primera PoC debe ser deliberadamente pequeña.

Componentes:

```text
Open WebUI
Hermes
SearXNG
Prometheus/Uptime Kuma read-only
Home Assistant read-only
n8n con 1-2 workflows seguros
```

Coding agents pueden incorporarse durante la misma PoC o inmediatamente después, dependiendo de complejidad de autenticación y ejecución en k3s.

---

# 51. PoC — casos de prueba

## Test 1 — Chat

```text
"Hola OSCAR, describí tu función."
```

Debe responder mediante Hermes desde Open WebUI.

## Test 2 — Search

```text
"Buscá la última versión estable de X."
```

Debe utilizar SearXNG.

Debe ser posible identificar que la búsqueda fue externa.

## Test 3 — Infra status

```text
"¿Cómo está OSCAR?"
```

Debe consultar fuentes reales.

No devolver una respuesta genérica basada solo en el LLM.

## Test 4 — Availability

```text
"¿Cuál fue la disponibilidad de OSCAR en las últimas 24 horas?"
```

Debe utilizar métricas reales de Kuma/Prometheus.

## Test 5 — Availability por servicio

```text
"¿Cuánto uptime tuvo Forgejo esta semana?"
```

Debe responder a partir del historial.

## Test 6 — Incidents

```text
"¿Qué servicios tuvieron caídas en los últimos 7 días?"
```

Debe poder listar incidentes o degradaciones observadas.

## Test 7 — Home Assistant

```text
"¿Qué temperatura tiene el rack?"
```

Si existe el sensor:

```text
read-only query
```

No realizar acciones físicas.

## Test 8 — n8n

Crear una acción de muy bajo riesgo.

Ejemplo:

```text
get-status
```

Hermes debe invocarla correctamente.

## Test 9 — Safety

Pedir:

```text
"Apagá Proxmox."
```

Resultado esperado en PoC:

```text
no puede ejecutarlo directamente
```

Debe explicar que no dispone de esa acción.

---

# 52. PoC de Codex

Después de la base:

```text
"Revisá oscar-led-controller."
```

Validar:

- autenticación OAuth;
- acceso restringido al repo;
- ejecución;
- generación de diff;
- no push automático;
- no acceso a otros repositorios.

---

# 53. PoC de Claude Code

Validar:

- Claude Code instalado;
- OAuth funcionando;
- acceso restringido;
- task delegation desde Hermes;
- respuesta recuperada;
- no modificaciones fuera del workspace permitido.

---

# 54. Disponibilidad del propio OSCAR AI

Agregar a Kuma:

```text
Hermes
Open WebUI
SearXNG
```

De esta manera el medidor de disponibilidad también cubre la capa AI.

Ejemplo:

```text
AI availability 24h
Hermes      100 %
Open WebUI   99.9 %
SearXNG     100 %
```

---

# 55. Medidor general en OSCAR Overview

Grafana `OSCAR Overview` debe incluir:

```text
┌─────────────────────────────┐
│ OSCAR                       │
│                             │
│ Critical availability 24h  │
│ 99.98 %                     │
│                             │
│ Services UP                 │
│ 18 / 19                     │
│                             │
│ Internet            UP      │
│ Proxmox             UP      │
│ Kubernetes          UP      │
│ OSCAR AI            UP      │
└─────────────────────────────┘
```

Esto debe ser un resumen.

El detalle vive en:

```text
OSCAR Availability
```

---

# 56. Posible integración futura con LEDs

El medidor de disponibilidad puede alimentar estados visuales del rack.

Ejemplo futuro:

```text
todo critical UP
→ aurora normal

critical degraded
→ amarillo suave

critical DOWN
→ rojo

deploy success
→ verde temporal
```

No implementar automáticamente.

Evitar que una métrica inestable cause cambios constantes de LEDs.

Aplicar debounce/hysteresis si se implementa.

---

# 57. Fases de implementación

## Fase 0 — Relevamiento

- [ ] Revisar estado de `oscar-ai`.
- [ ] Revisar repositorios actuales.
- [ ] Confirmar k3s resources disponibles.
- [ ] Confirmar storage.
- [ ] Confirmar Prometheus.
- [ ] Confirmar Kuma `/metrics`.
- [ ] Confirmar Open WebUI aún no desplegado o estado actual.
- [ ] Confirmar SearXNG aún no desplegado o estado actual.
- [ ] Revisar auth disponible de ChatGPT/Codex.
- [ ] Revisar auth disponible de Claude Code.
- [ ] Revisar n8n.
- [ ] Revisar HAOS.
- [ ] Revisar política actual de Secrets.

No modificar infraestructura durante esta fase.

## Fase 1 — Base oscar-ai

- [ ] Crear/validar namespace `oscar-ai`.
- [ ] Desplegar SearXNG.
- [ ] Desplegar Hermes.
- [ ] Desplegar Open WebUI.
- [ ] Configurar PVCs.
- [ ] Configurar Secrets.
- [ ] Configurar Services.
- [ ] Configurar health checks.
- [ ] Configurar requests/limits.
- [ ] Integrar Open WebUI → Hermes.
- [ ] Integrar Hermes → SearXNG.

## Fase 2 — OpenAI/Codex

- [ ] Configurar OAuth de Codex/ChatGPT.
- [ ] No crear OpenAI API key salvo necesidad.
- [ ] Validar provider de Hermes.
- [ ] Validar Codex CLI.
- [ ] Validar workspace aislado.
- [ ] Documentar renovación/reautenticación.

## Fase 3 — Claude Code

- [ ] Instalar Claude Code en el entorno apropiado.
- [ ] Configurar login de Claude.
- [ ] No crear Anthropic API key automáticamente.
- [ ] Validar delegación.
- [ ] Restringir workspace.
- [ ] Documentar autenticación.

## Fase 4 — Observabilidad y disponibilidad

- [ ] Agregar Hermes a Kuma.
- [ ] Agregar Open WebUI a Kuma.
- [ ] Agregar SearXNG a Kuma.
- [ ] Configurar scrape `/metrics` de Kuma.
- [ ] Validar `monitor_status`.
- [ ] Crear dashboard `OSCAR Availability`.
- [ ] Crear availability 24h.
- [ ] Crear availability 7d.
- [ ] Crear availability 30d.
- [ ] Crear downtime.
- [ ] Crear incident count si los datos lo permiten.
- [ ] Agregar resumen a OSCAR Overview.
- [ ] Agregar resumen a Homepage.

## Fase 5 — Hermes read-only infra

- [ ] Prometheus read-only.
- [ ] Availability read-only.
- [ ] k3s read-only.
- [ ] Home Assistant read-only.
- [ ] Forgejo read-only.
- [ ] Documentar tools expuestas.
- [ ] Validar mínimo privilegio.

## Fase 6 — n8n Actions

Crear inicialmente solamente:

```text
oscar.get-status
oscar.get-availability
```

Después evaluar:

```text
oscar.switch-led-mode
oscar.restart-deployment
oscar.run-backup
```

No agregar acciones sensibles masivamente.

## Fase 7 — Coding agents

- [ ] Codex.
- [ ] Claude Code.
- [ ] repos allowlist.
- [ ] workspace isolation.
- [ ] diff only inicialmente.
- [ ] no auto-push.
- [ ] no auto-merge.

## Fase 8 — Evaluación

Medir durante uso real:

```text
utilidad
latencia
RAM
CPU
errores
estabilidad
calidad de tools
seguridad
autenticaciones
disponibilidad
```

Después decidir si Hermes pasa de:

```text
PoC
```

a:

```text
componente oficial de OSCAR
```

---

# 58. Criterios de aceptación

## Base

- [ ] Open WebUI habla con Hermes.
- [ ] Hermes utiliza un modelo correctamente.
- [ ] SearXNG funciona como búsqueda.
- [ ] Persistencia sobrevive reinicios.
- [ ] Secrets no están en Git.

## Observabilidad

- [ ] Hermes aparece en Kuma.
- [ ] Open WebUI aparece en Kuma.
- [ ] SearXNG aparece en Kuma.
- [ ] Prometheus scrapea Kuma.
- [ ] Grafana muestra disponibilidad.

## Availability

- [ ] Existe disponibilidad 24h.
- [ ] Existe disponibilidad 7d.
- [ ] Existe disponibilidad 30d.
- [ ] Se puede consultar por servicio.
- [ ] Se puede identificar downtime.
- [ ] Hermes puede responder preguntas de disponibilidad con datos reales.

## Security

- [ ] Hermes no tiene cluster-admin.
- [ ] Hermes no tiene Docker socket.
- [ ] Hermes no tiene root de Proxmox.
- [ ] Hermes no tiene router admin.
- [ ] acciones sensibles no están disponibles directamente.

## Agents

- [ ] Codex funciona con autenticación validada.
- [ ] Claude Code funciona con autenticación validada.
- [ ] ninguno hace push/merge automático inicialmente.

---

# 59. Rollback

Cada fase debe ser reversible.

## Hermes

Rollback:

```text
deshabilitar/eliminar Deployment
```

Open WebUI puede posteriormente apuntarse a otro backend si fuera necesario.

## SearXNG

Puede retirarse sin afectar infraestructura core.

## Availability

No modificar Uptime Kuma destructivamente.

Prometheus solamente consume sus métricas.

## Coding agents

Eliminar credenciales/sesiones y deshabilitar tools.

## n8n

Deshabilitar workflows vinculados a Hermes.

---

# 60. Documentación requerida

Actualizar:

```text
OSCAR_FINAL_INFRASTRUCTURE.md
docs/ia/vision-general.md
catalogo.md
docs/ia/hermes.md
docs/observabilidad/disponibilidad.md
```

Adaptar paths a la estructura real del repo.

---

# 61. `docs/ia/hermes.md`

Debe documentar:

```text
qué es Hermes;
por qué se eligió;
arquitectura;
providers;
Codex;
Claude Code;
Open WebUI;
SearXNG;
MCP;
n8n;
Home Assistant;
seguridad;
troubleshooting;
backup;
upgrade;
rollback.
```

---

# 62. `docs/observabilidad/disponibilidad.md`

Debe documentar:

```text
qué medimos;
fuentes;
Kuma;
Prometheus;
PromQL;
ventanas;
categorías Critical/Core/Applications;
cálculo global;
downtime;
dashboards;
retención;
limitaciones.
```

---

# 63. Prompt para Claude

```text
Actuá como arquitecto DevOps/SRE y responsable técnico de O.S.C.A.R.

Usá este archivo como especificación objetivo para incorporar Hermes Agent como runtime principal de OSCAR AI.

IMPORTANTE:

No implementes todo de golpe.

Primero realizá Fase 0:

1. revisá el repositorio actual;
2. revisá OSCAR_FINAL_INFRASTRUCTURE.md;
3. revisá docs/ia/vision-general.md;
4. revisá catalogo.md;
5. revisá k3s01;
6. revisá Prometheus/Grafana/Uptime Kuma;
7. revisá n8n;
8. revisá Home Assistant;
9. revisá la estrategia actual de Secrets;
10. verificá las versiones actuales de Hermes/Open WebUI/SearXNG y sus requisitos;
11. verificá cómo se autentican actualmente Codex y Claude Code;
12. identificá cualquier contradicción con la arquitectura actual.

Después entregame:

- evaluación;
- cambios propuestos;
- riesgos;
- dependencias;
- recursos requeridos;
- archivos a crear/modificar;
- roadmap;
- rollback.

Decisión actual:

Hermes Agent es el candidato elegido para la PoC de OSCAR AI.

Arquitectura:

Open WebUI
    ↓
Hermes
    ├── ChatGPT/Codex mediante OAuth
    ├── Codex CLI
    ├── Claude Code CLI
    ├── SearXNG
    ├── Prometheus
    ├── Uptime Kuma / disponibilidad
    ├── Home Assistant read-only
    ├── Forgejo/k3s read-only
    └── n8n como Action Broker

REGLAS DE SEGURIDAD:

- no cluster-admin;
- no Docker socket;
- no root Proxmox;
- no router admin;
- no secretos en Git;
- no push/merge automático;
- write access solamente mediante allowlist/approval/workflows controlados;
- aplicar principio de mínimo privilegio.

AUTENTICACIÓN:

Queremos aprovechar inicialmente las suscripciones existentes.

OpenAI:
- preferir ChatGPT/Codex OAuth;
- no asumir que ChatGPT equivale a OpenAI API;
- no crear API billing sin necesidad.

Anthropic:
- preferir Claude Code autenticado con la cuenta Claude;
- no crear ANTHROPIC_API_KEY automáticamente;
- no habilitar Anthropic extra usage automáticamente.

DISPONIBILIDAD:

El medidor de disponibilidad es parte obligatoria de esta iniciativa.

Debe utilizar:

Uptime Kuma
    ↓ /metrics
Prometheus
    ↓
Grafana

Ventanas:

- 24h
- 7d
- 30d

Debe existir:

- disponibilidad por servicio;
- disponibilidad por categoría;
- downtime;
- vista OSCAR Availability;
- resumen en OSCAR Overview/Homepage;
- capacidad de que Hermes responda preguntas históricas de disponibilidad utilizando datos reales.

No asumir que monitor_status tiene una semántica específica sin verificar los datos reales.

No definas SLOs rígidos todavía.

Primero medir.

La primera PoC debe demostrar:

1. Open WebUI → Hermes;
2. Hermes → modelo;
3. Hermes → SearXNG;
4. Hermes → Prometheus/Kuma read-only;
5. consulta real de disponibilidad;
6. Home Assistant read-only;
7. un workflow n8n seguro;
8. rechazo de acciones no autorizadas.

Después incorporar:

9. Codex;
10. Claude Code.

No continúes con una fase si la anterior no está validada.
```

---

# 64. Fuentes oficiales a revisar durante la implementación

Claude debe volver a validar documentación actual antes de implementar.

Hermes:

```text
https://hermes-agent.nousresearch.com/
```

Open WebUI integration:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui
```

SearXNG integration:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
```

Codex integration:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex
```

Claude Code integration:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code
```

MCP:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
```

Uptime Kuma Prometheus integration:

```text
https://github.com/louislam/uptime-kuma/wiki/Prometheus-Integration
```

La documentación oficial debe prevalecer sobre esta especificación si cambió la implementación técnica.

---

# 65. Principio final

OSCAR AI debe evolucionar hacia:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
SUGGEST
   ↓
ASK FOR APPROVAL
   ↓
ACT
```

No:

```text
LLM
 ↓
ROOT ACCESS
```

La autonomía debe crecer solamente a medida que exista observabilidad, control de permisos, auditabilidad y rollback.

El medidor de disponibilidad forma parte de esa base: OSCAR debe poder demostrar con datos históricos cuándo estuvo disponible, cuándo falló y qué componente causó la degradación antes de intentar actuar sobre la infraestructura.
