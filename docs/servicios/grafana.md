---
title: Grafana
sidebar_position: 9
---

# Grafana

**Estado:** Objetivo · Observabilidad  
**Dónde corre:** VM observabilidad o Docker Core  
**Sizing inicial:** 1–2 vCPU, 1–2 GB RAM inicial  
**Red/puertos:** 3000 interno detrás de acceso controlado  
**Persistencia:** dashboards, datasources, usuarios; preferir provisioning desde Git

## Rol dentro de O.S.C.A.R.

- dashboard de rack
- CPU/RAM/storage
- Internet y DNS
- CCTV/UPS
- estado de Kubernetes

## Ejemplo concreto

Dashboard O.S.C.A.R.: WAN, Dell, Pi, k3s, backups, UPS, temperatura y disponibilidad en una pantalla 1280×720.

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

Provisionar dashboards críticos desde archivos reduce dependencia de cambios manuales en UI.

API keys y service accounts de Grafana suelen tener permisos amplios sobre datasources; tratarlas como secretos y rotarlas si se filtran.

Como baseline:

- no publicar el panel administrativo directamente a Internet;
- usar usuario no-root dentro del contenedor cuando la imagen lo soporte;
- limitar redes y puertos a lo necesario;
- revisar mounts privilegiados;
- separar secretos de la configuración versionada.

## Backup y restore

El estado vive en `/var/lib/grafana`, por defecto una SQLite (`grafana.db`) con usuarios, API keys y cualquier dashboard/datasource creado a mano desde la UI.

Si dashboards y datasources están provisionados desde Git (ver "Persistencia" arriba), esa parte ya está respaldada por el propio repositorio y no hace falta duplicarla. Lo que sí hay que respaldar es `grafana.db` (usuarios, permisos, estado de alerting) y las API keys/service accounts.

Restore: copiar `grafana.db` a una instancia nueva con el mismo volumen de provisioning montado. Si se perdió el archivo y todo estaba provisionado por código, una instancia nueva se reconstruye sola con `docker compose up`, sin necesitar el backup de la base.

## Observabilidad

- endpoint `/api/health`;
- conectividad con datasources (Prometheus/Loki accesibles desde Grafana);
- errores de render en paneles;
- disponibilidad HTTP y reinicios del contenedor;
- logs de errores.

## Troubleshooting

- **Dashboard muestra "No data"** → datasource inalcanzable o query mal apuntada → verificar conectividad de red hacia Prometheus/Loki, revisar logs del datasource en Grafana (Configuration → Data sources → Test).
- **Cambios en dashboards provisionados desde Git desaparecen al reiniciar** → comportamiento esperado: el provisioning sobrescribe lo editado a mano en la UI → hacer el cambio en el archivo fuente y versionarlo, no en la UI.
- **Grafana no arranca tras un restore de `grafana.db`** → versión de Grafana distinta a la que generó el archivo, o volumen con permisos incorrectos → revisar logs del contenedor y confirmar que la versión de imagen coincide con la del backup. Ver [`docker-servicio-caido.md`](../runbooks/docker-servicio-caido.md).

## Ideas de laboratorio

1. desplegar una instancia de prueba;
2. cargar datos ficticios;
3. provocar una caída controlada;
4. detectar la caída desde Uptime Kuma/Prometheus;
5. restaurar o hacer rollback;
6. registrar el procedimiento en un runbook.

## Documentación oficial

https://grafana.com/docs/grafana/
