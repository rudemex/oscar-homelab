---
title: Principios de automatización
sidebar_position: 3
---

# Principios

1. **Idempotencia:** repetir no debe destruir ni duplicar.
2. **Timeouts:** ninguna llamada espera indefinidamente.
3. **Retries con backoff:** no reintentar en loop agresivo.
4. **Auditoría:** guardar outcome y contexto útil.
5. **Secretos:** credenciales fuera del workflow exportado.
6. **Dry-run:** para cambios peligrosos, preferir propuesta antes de ejecución.
7. **Rollback:** saber cómo deshacer.
8. **Blast radius:** un workflow de laboratorio no recibe permisos sobre toda la red.
