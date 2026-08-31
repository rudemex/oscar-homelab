---
title: Modelo de amenazas
sidebar_position: 1
---

# Modelo de amenazas

O.S.C.A.R. es doméstico, pero ejecuta software real y puede almacenar credenciales. Las amenazas más probables no son "hackers de película" sino errores de configuración y automatización con demasiado permiso.

## Actores y superficie por origen

| Origen | Ejemplos de vector | Mitigación principal |
|---|---|---|
| **Atacante remoto (Internet)** | escaneo automatizado de puertos abiertos, credential stuffing contra un panel expuesto, explotación de una imagen/dependencia vulnerable en un servicio público | [exposición mínima](./exposicion-internet.md), Cloudflare Access + MFA, versiones al día, sin puertos administrativos en el router |
| **Dispositivo IoT/invitado comprometido (LAN)** | cámara/foco IoT con firmware inseguro moviéndose lateralmente hacia SERVERS o MGMT | segmentación [VLAN](../red/vlans.md) (IOT→CLIENTS denegado por defecto), sin credenciales compartidas entre VLANs |
| **Credencial filtrada** | contraseña reutilizada de otro servicio, token de API expuesto en un repo o log | identidad única por servicio, [gestión de secretos](./secretos.md), rotación (ver runbook [rotación de secreto](../runbooks/rotacion-secreto.md)) |
| **Error humano propio** | token subido a Git por accidente, backup nunca probado, regla de firewall mal escrita | pre-commit hooks / revisión antes de push, [restore drills](../backup-dr/restore-drill.md) periódicos, cambios de firewall documentados y revisados |
| **Supply chain** | imagen de contenedor comprometida, dependencia npm/pip vulnerable | imágenes oficiales con tag fijo, scan con Trivy (ver [seguridad de contenedores](./contenedores.md)) |

La distinción importa porque la mitigación es distinta: un atacante remoto se detiene en el perímetro (no abrir el panel); un dispositivo IoT comprometido se detiene en la segmentación interna (VLAN), no en el firewall perimetral, que ya lo dejó entrar a la LAN.

## Activos principales

- red doméstica;
- credenciales;
- datos personales;
- repositorios;
- configuración de infraestructura;
- backups;
- CCTV.

## Estrategia

Reducir superficie, segmentar, usar identidad fuerte, mantener versiones, observar anomalías y asumir que cualquier componente puede fallar. Priorizar mitigaciones en este orden: (1) nada administrativo directo a Internet, (2) segmentación VLAN antes de sumar dispositivos IoT/CCTV, (3) secretos fuera de Git y rotables, (4) backups probados, (5) scanning de supply chain una vez que el pipeline es estable.
