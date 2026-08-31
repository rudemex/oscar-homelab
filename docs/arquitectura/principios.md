---
title: Principios de diseño
sidebar_position: 2
---

# Principios de diseño

## 1. La configuración importante vive en Git

El objetivo es que perder una VM no implique perder el conocimiento para reconstruirla. Deben versionarse:

- `compose.yaml`;
- manifiestos Kubernetes;
- Helm values;
- playbooks y scripts;
- dashboards exportables;
- reglas de alertas;
- documentación;
- inventario no sensible.

Nunca se versionan tokens, contraseñas, claves privadas ni archivos `.env` reales.

## 2. Separar datos de configuración

Una aplicación puede recrearse; sus datos no siempre.

```text
/app
  compose.yaml         <- Git
  .env.example         <- Git
  config/              <- Git si no contiene secretos
  data/                <- backup, NO Git
  secrets/             <- gestor de secretos, NO Git
```

## 3. Todo servicio debe responder seis preguntas

Antes de declararlo operativo:

1. ¿dónde corre?
2. ¿qué puertos usa?
3. ¿qué datos persiste?
4. ¿cómo se respalda?
5. ¿cómo se monitorea?
6. ¿cómo se actualiza y vuelve atrás?

## 4. Evitar dependencias circulares

Ejemplo de mala arquitectura: DNS depende de Kubernetes, Kubernetes depende de un registry cuyo hostname necesita ese DNS, y el DNS solo puede recuperarse cuando Kubernetes arranca.

Los servicios necesarios para recuperar la plataforma deben tener pocas dependencias.

## 5. Defaults seguros

- ningún panel administrativo expuesto directamente a Internet;
- MFA donde sea posible;
- cuentas individuales en vez de credenciales compartidas;
- secretos fuera de Git;
- mínimos privilegios;
- acceso entre VLAN explícito, no implícito;
- backups cifrados fuera del host.

## 6. Automatizar con capacidad de rollback

Una automatización que puede cambiar firewall, DNS o workloads debe registrar:

- qué intentó hacer;
- qué cambió;
- quién/qué la inició;
- resultado;
- procedimiento de reversión.

## 7. La IA no es root

Un agente puede analizar métricas, proponer cambios y ejecutar tareas acotadas. No debería recibir una credencial administrativa universal. Las herramientas disponibles al agente deben ser explícitas y auditables.
