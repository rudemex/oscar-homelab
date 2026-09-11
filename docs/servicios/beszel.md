---
title: Beszel
sidebar_position: 22
---

# Beszel

**Estado:** Actual, parcial — hub corriendo en `core01`; agente pendiente de conectar (requiere completar el primer acceso por navegador)
**Dónde corre:** Docker Core (`/srv/oscar/apps/beszel/`)
**Sizing inicial:** ~50 MB hub + ~30 MB por agente
**Red/puertos:** `8090` (hub, UI/API), agente en modo `network_mode: host` puerto `45876`
**Persistencia:** SQLite del hub en `./hub-data`

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

```bash
docker compose up -d beszel   # el hub primero, solo
```

## Primer acceso (obligatorio antes de levantar el agente)

1. Entrar a `http://<IP-de-core01>:8090`, crear el usuario admin del hub.
2. En la UI, "Add System" → nombre `core01` → el hub genera una clave pública SSH.
3. Copiar esa clave a `BESZEL_AGENT_KEY` en `.env`.
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

- **El agente no aparece "conectado" en el hub** → `BESZEL_AGENT_KEY` no coincide con la clave que el hub generó para ese sistema, o el agente no arrancó → revisar `docker compose logs beszel-agent` y que la key en `.env` sea exactamente la que dio la UI.
- **No hay datos de red/disco del host real** → el agente no está en `network_mode: host`, quedó en la red por defecto de Compose → confirmar esa línea en `compose.yaml`.
