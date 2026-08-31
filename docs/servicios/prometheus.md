---
title: Prometheus
sidebar_position: 8
---

# Prometheus

**Estado:** Objetivo · Observabilidad  
**Dónde corre:** VM observabilidad o k3s, según fase  
**Sizing inicial:** 2 vCPU, 2–4 GB RAM inicial; storage depende de retención  
**Red/puertos:** 9090 solo LAN/admin  
**Persistencia:** series temporales; definir retención

## Rol dentro de O.S.C.A.R.

- métricas de hosts
- métricas k3s
- temperaturas/exporters
- SLO caseros
- alertas por capacidad

## Ejemplo concreto

Alerta: disco de `pve01` > 85% durante 15 min; dashboard: RAM/CPU/latencia de todos los nodos.

## Checklist de despliegue

- [ ] hostname y ubicación decididos;
- [ ] imagen/versión fijada, evitando tags flotantes en servicios importantes;
- [ ] puertos documentados;
- [ ] volumen/persistencia definida;
- [ ] `.env.example` sin secretos en Git;
- [ ] credenciales reales fuera de Git;
- [ ] backup definido antes de cargar datos importantes;
- [ ] healthcheck o monitor de disponibilidad;
- [ ] métricas/logs incorporados cuando sea razonable;
- [ ] procedimiento de actualización y rollback documentado.

## Seguridad

No guardar métricas indefinidamente. Retención y cardinalidad son decisiones de capacidad.

Si se habilita `--web.enable-admin-api` (necesaria para snapshots), restringirla a acceso LAN/admin: expone endpoints capaces de borrar series o el TSDB completo.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El TSDB en `/prometheus` es una serie temporal recreable: se vuelve a poblar scrapeando desde cero. Según la [estrategia 3-2-1](../backup-dr/estrategia-321.md) se clasifica como **no crítico** — perder el histórico duele pero no es una pérdida de datos irreemplazable.

Lo que sí hay que respaldar (y ya está resuelto, porque vive en Git como IaC) son los archivos de configuración: `prometheus.yml`, reglas de alerting y scrape configs.

Si se necesita conservar histórico más allá de la retención local — por ejemplo antes de migrar de host — usar el endpoint `/api/v1/admin/tsdb/snapshot` (requiere `--web.enable-admin-api`) para generar un snapshot puntual del TSDB.

## Observabilidad

- endpoints `/-/healthy` y `/-/ready`;
- métrica `up == 0` por target: detecta targets caídos;
- uso de disco del TSDB;
- duración de scrape por job;
- reinicios del contenedor.

## Troubleshooting

- **Target down en `/targets`** → servicio caído, exporter no responde, o firewall/VLAN bloqueando el scrape → `curl` al endpoint `/metrics` desde el host de Prometheus, revisar reglas de firewall entre VLANs.
- **Disco del TSDB crece más rápido de lo esperado** → retención muy larga o cardinalidad alta (demasiadas series/labels únicos) → revisar retención configurada y buscar labels de alta cardinalidad en las reglas de scrape.
- **Alertas no llegan aunque la regla dispara en `/alerts`** → Alertmanager mal configurado o ruta de notificación equivocada → revisar la configuración de Alertmanager y el estado de la alerta ahí, no solo en Prometheus.

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://prometheus.io/docs/
