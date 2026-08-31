# Contribuir a O.S.C.A.R.

La documentación se trata como código.

Antes de integrar un cambio:

1. actualizar la documentación afectada;
2. evitar secretos, IP públicas, tokens o credenciales reales;
3. actualizar `inventory/` cuando cambie hardware o servicios;
4. agregar un runbook si el nuevo componente requiere operación recurrente;
5. ejecutar `yarn check`;
6. revisar que los enlaces y diagramas Mermaid rendericen correctamente.

Para cambios grandes, registrar también la decisión en arquitectura o en la bitácora.

## Al documentar un servicio nuevo

`docs/servicios/*.md` sigue una plantilla común (Estado, Rol, Ejemplo concreto, Checklist de despliegue, Seguridad, Backup y restore, Observabilidad, Troubleshooting, Ideas de laboratorio, Documentación oficial). No todas las secciones necesitan el mismo desarrollo: un servicio **Objetivo/Core** (Nexus, Argo CD, Grafana) merece Backup/Observabilidad/Troubleshooting concretos y específicos; un servicio **Laboratorio** puede decir honestamente "no vale la pena respaldar esto" si el dato es recreable, en vez de inflar la sección para completar la plantilla. Preferir una sección corta y honesta a una larga y genérica.
