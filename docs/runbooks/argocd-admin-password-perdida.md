---
title: Argo CD - password de admin inválida/perdida
sidebar_position: 13
---

# Argo CD — password de admin inválida/perdida

## Objetivo

Recuperar acceso al usuario `admin` de Argo CD sin perder ninguna `Application` ni tocar el cluster más allá de lo necesario — el estado deseado sigue viviendo en Git, esto solo afecta el acceso a la UI/API.

## Cuándo usarlo

- `POST /api/v1/session` (o el login de la UI) devuelve `Invalid username or password` con una password que debería ser la vigente.
- Pasó después de un cambio de password vía `PUT /api/v1/account/password` que devolvió éxito (`{}`) pero la password nueva tampoco loguea — visto en la instalación real de `k3s01`: la API respondió éxito y una verificación inmediata funcionó, pero minutos después la misma password dejó de validar (causa no confirmada — no se reprodujo un patrón claro; puede ser un problema de sincronización del hash entre réplicas/cache del `argocd-server`, no confirmado).

## Procedimiento

1. Confirmar que efectivamente no hay ninguna password que funcione (probar la última conocida y, si existía, la inicial autogenerada).
2. Como el login normal está bloqueado, no se puede usar `PUT /api/v1/account/password` (necesita una sesión autenticada). La recuperación oficial es reescribir directamente el hash en el Secret `argocd-secret` (namespace `argocd`), que es donde vive `admin.password`:

   ```bash
   python3 -c "
   import bcrypt
   print(bcrypt.hashpw(b'<password-nueva>', bcrypt.gensalt(10)).decode())
   "
   ```

3. Parchear el Secret con el hash generado y una `passwordMtime` actual:

   ```bash
   kubectl -n argocd patch secret argocd-secret -p '{"stringData": {"admin.password": "<hash-bcrypt>", "admin.passwordMtime": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}}'
   ```

4. **Verificar en caliente antes de dar por resuelto** — no confiar en que el `kubectl patch` haya funcionado solo porque no dio error:

   ```bash
   curl -sk -X POST https://<argocd-server>/api/v1/session \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"<password-nueva>"}'
   ```

   Repetir la verificación una segunda vez con unos segundos de diferencia — el incidente real que motivó este runbook mostró una password que funcionaba en la primera verificación y dejaba de funcionar poco después, así que una sola prueba inmediata no es suficiente evidencia de que quedó realmente resuelto.

## Validación de salida

- Login exitoso repetido (al menos dos verificaciones separadas en el tiempo).
- Password nueva guardada en el gestor de secretos (nunca en Git, nunca en texto plano fuera de ahí).
- Si existía un Secret `argocd-initial-admin-secret` colgado de un bootstrap anterior, confirmar que ya no es necesario y borrarlo.

## Datos a registrar

```text
Inicio:
Detección:
Password(s) que dejaron de funcionar:
Acción tomada:
Verificaciones (cuántas, con qué resultado):
Causa raíz (si se identificó):
```
