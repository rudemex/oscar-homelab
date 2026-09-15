---
title: Beszel
sidebar_position: 22
---

# Beszel

**Estado:** Actual — hub en `core01`, agentes en **3 hosts** (`core01`, `devops01`, `k3s01`), los tres `up` y reportando CPU/RAM/disco en tiempo real
**Dónde corre:** hub en Docker Core (`/srv/oscar/apps/beszel/`); agentes en `/srv/oscar/apps/beszel-agent/` en cada host adicional
**Sizing inicial:** ~50 MB hub + ~30 MB por agente
**Red/puertos:** `8090` (hub, UI/API), cada agente en modo `network_mode: host` puerto `45876`
**Persistencia:** SQLite del hub en `./hub-data`

## Agentes registrados

| Host | IP | Por qué |
|---|---|---|
| `core01` | `192.168.0.156` | co-instalado con el hub desde el arranque |
| `devops01` | `192.168.0.151` | corre [Forgejo](./forgejo.md) y va a sumar Nexus/CI Runner — sin esto, cero visibilidad de recursos ahí (mismo blind spot que ya pasó con `core01` llegando al 91% de RAM sin que nadie lo viera venir) |
| `k3s01` | `192.168.0.150` | corre Argo CD y `oscar-led-controller`, mismo problema de visibilidad cero |

Cada agente nuevo usa la misma `BESZEL_AGENT_KEY` (clave pública del hub) que ya existía en `core01` — no hace falta generar una por host, es la identidad del hub, no del agente. El registro del "System" en el hub (`host`+`port`+`users`) se hizo vía la API REST de PocketBase (`POST /api/collections/systems/records`), mismo mecanismo que documenta [Homepage](./homepage.md#el-bug-de-beszel-overview-en-vez-de-las-métricas-reales) para sacar el `systemId`.

No se agregó agente en `oscar-core` (el hipervisor, ya cubierto por [ProxMenux Monitor](./proxmenux-monitor.md) + el widget de Proxmox en Homepage) ni en el LXC de AdGuard/VM de Home Assistant (más livianos, Uptime Kuma ya da el chequeo básico de arriba/abajo que alcanza a ese tamaño).

## Rol dentro de O.S.C.A.R.

Monitoreo liviano de CPU/RAM/disco/red por host — mucho menos setup que Prometheus + Grafana + exporters, a costa de menos flexibilidad. Sirve como monitoreo básico mientras no se justifique el stack completo de [observabilidad](../observabilidad/arquitectura.md), o en paralelo si algún día se quiere ambos.

Arquitectura: un **hub** central (UI + API) y uno o más **agentes** (uno por host a monitorear) que el hub consulta por SSH.

## Instalación

```bash
mkdir -p /srv/oscar/apps/beszel/hub-data /srv/oscar/apps/beszel/agent-data
```

`compose.yaml`:

```yaml
services:
  beszel:
    image: henrygd/beszel:${BESZEL_VERSION}
    container_name: beszel
    restart: unless-stopped
    volumes:
      - ./hub-data:/beszel_data
    ports:
      - "8090:8090"

  beszel-agent:
    image: henrygd/beszel-agent:${BESZEL_VERSION}
    container_name: beszel-agent
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./agent-data:/var/lib/beszel-agent
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      LISTEN: 45876
      KEY: ${BESZEL_AGENT_KEY}
```

`.env`: `BESZEL_VERSION=0.19.0` (misma versión en hub y agentes — el protocolo entre ambos no está garantizado estable entre versiones distintas, mantenerlas iguales en los tres hosts). `BESZEL_AGENT_KEY` es la clave pública del hub, generada por el propio hub en su primer arranque (visible en su UI, "Add System") — no se genera a mano, y es la misma para todos los agentes que se sumen (ver "Agentes registrados" abajo).

```bash
docker compose up -d beszel   # el hub primero, solo
```

## Primer acceso (obligatorio antes de levantar el agente)

1. Entrar a `http://<IP-de-core01>:8090`, crear el usuario admin del hub.
2. En la UI, "Add System" → nombre `core01`, **host = IP LAN real de `core01`** (nunca `localhost`: el hub corre en la red bridge por defecto de Docker, no en `network_mode: host`, así que `localhost` apunta al propio contenedor del hub, no al host) → puerto `45876`.
3. El hub tiene su propio keypair SSH en `./hub-data/id_ed25519` (se genera solo al primer arranque); su clave pública es la que hay que copiar a `BESZEL_AGENT_KEY` en `.env` para que el agente confíe en ese hub.
4. Recién ahí: `docker compose up -d beszel-agent`.

El agente usa `network_mode: host` para poder reportar métricas de red/disco del host real, no de la red aislada de Docker — es una excepción deliberada a "no usar host networking", justificada por lo que necesita medir.

## Seguridad

- el agente expone un puerto SSH-like (45876) que solo el hub debería poder alcanzar — en una red plana sin VLAN, cualquier otro host de la LAN también podría intentar conectarse; no es crítico hoy pero es una razón más para la segmentación futura;
- `network_mode: host` le da al contenedor visibilidad total de la red del host — evaluar si eventualmente conviene una regla de firewall específica para el puerto del agente.

## Backup y restore

El hub guarda su estado (usuarios, sistemas registrados, historial de métricas) en `./hub-data`. El historial de métricas es recreable (se vuelve a acumular solo); lo único que vale la pena respaldar es la config de usuarios/sistemas si se quiere evitar re-configurar desde cero.

## Observabilidad

Es la propia herramienta de observabilidad — el "quién vigila al vigilante" aplica igual que con Uptime Kuma: si el hub se cae, nada avisa solo. Un chequeo HTTP desde Uptime Kuma hacia el puerto 8090 cierra ese círculo.

## Troubleshooting

- **El agente no aparece "conectado" en el hub (status `down`)** → causa más común: el campo `host` del sistema en el hub quedó como `localhost` en vez de la IP LAN real de `core01`. El hub vive en la red bridge por defecto de Docker (no `network_mode: host`), así que `localhost` no llega al agente que escucha en la interfaz real del host — hay que usar la IP LAN. El log del agente (`docker compose logs beszel-agent`) muestra `WARN Error creating WebSocket client err="HUB_URL environment variable not set"` en arranque normal — ese warning es inofensivo (es una vía de conexión alternativa que este setup no usa) y no indica el problema real.
- **`BESZEL_AGENT_KEY` no coincide** → si igual falla con el host correcto, confirmar que la key en `.env` es exactamente la pública derivada de `./hub-data/id_ed25519` (`ssh-keygen -y -f id_ed25519`), no una key vieja o de otro sistema.
- **No hay datos de red/disco del host real** → el agente no está en `network_mode: host`, quedó en la red por defecto de Compose → confirmar esa línea en `compose.yaml`.
