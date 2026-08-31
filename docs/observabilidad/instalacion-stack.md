---
title: Instalación del stack
sidebar_position: 6
---

# Prometheus + Grafana + Loki paso a paso

Para la primera etapa se puede ejecutar observabilidad en Docker y migrarla a k3s más adelante solo si existe una ventaja concreta.

## 1. Preparar directorio

```bash
mkdir -p /srv/oscar/apps/observability/{prometheus,loki,grafana/provisioning}
cd /srv/oscar/apps/observability
```

## 2. Versiones

Crear `.env`:

```dotenv
PROMETHEUS_VERSION=CHANGE_ME_STABLE
GRAFANA_VERSION=CHANGE_ME_STABLE
LOKI_VERSION=CHANGE_ME_STABLE
PROMTAIL_VERSION=CHANGE_ME_STABLE
```

Usar versiones estables verificadas al momento de instalar, no `latest`.

## 3. Prometheus

`prometheus/prometheus.yml` mínimo:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['prometheus:9090']
```

Después agregaremos node exporters, k3s y servicios.

## 4. Compose conceptual

```yaml
services:
  prometheus:
    image: prom/prometheus:${PROMETHEUS_VERSION}
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=15d   # ajustar según espacio disponible en el SATA SSD
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:${GRAFANA_VERSION}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

Retención: 15 días es un punto de partida razonable para un solo host — ajustar con `--storage.tsdb.retention.size` también si el disco es la restricción real (ver [storage grande](../proxmox/storage.md#datos-grandes)).

## 4b. Loki + Promtail

Loki solo, sin agente de recolección, no sirve para nada — necesita algo que envíe logs. Para Docker Compose, **Promtail** (o **Grafana Alloy**, su sucesor) lee los logs de los contenedores del propio host y los empuja a Loki:

```yaml
services:
  loki:
    image: grafana/loki:${LOKI_VERSION}
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    restart: unless-stopped

  promtail:
    image: grafana/promtail:${PROMTAIL_VERSION}
    volumes:
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

volumes:
  loki-data:
```

`promtail-config.yml` mínimo usando `docker_sd_configs` para autodescubrir contenedores por label:

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 15s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
```

Retención de Loki (ajustar en `loki-config.yml`, sección `limits_config`/`compactor`) debe ser igual o menor a la de Prometheus para no sorprenderse con crecimiento de disco distinto entre métricas y logs.

## 5. Levantar

```bash
docker compose config
docker compose up -d
docker compose ps
```

## 6. Provisionar datasource

En lugar de configurarlo manualmente para siempre, crear provisioning YAML de Grafana apuntando a `http://prometheus:9090`.

## 7. Node Exporter

Instalar exporter en `core01` y luego en VMs/Pi. Agregar targets a Prometheus en `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['prometheus:9090']
  - job_name: node
    static_configs:
      - targets:
          - 'core01.oscar.home:9100'
          - 'devops01.oscar.home:9100'
          - 'k3s01.oscar.home:9100'
```

`node_exporter` se corre como binario o contenedor con `--network host` en cada VM (no dentro del stack de observabilidad, sino en cada host a monitorear) y expone el puerto `9100` por defecto.

## 8. Primer dashboard

Mostrar:

- CPU;
- RAM;
- disk free;
- network;
- uptime.

## 9. Primera alerta

Elegir **una**: host down o disco >85%. Validar disparándola de forma controlada.

## 10. Backup

Grafana provisioning vive en Git. Datos configurados manualmente y cualquier DB/volume necesaria deben respaldarse según la matriz de backup.
