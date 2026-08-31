---
title: Gestión de secretos
sidebar_position: 2
---

# Secretos

## Nunca en Git

- passwords;
- API keys;
- tokens;
- claves privadas;
- kubeconfig administrativo;
- encryption keys;
- cookies/sesiones;
- backups sin cifrar con credenciales.

## En el repo sí

```dotenv
# .env.example
POSTGRES_HOST=postgres
POSTGRES_DB=oscar_demo
POSTGRES_USER=CHANGE_ME
POSTGRES_PASSWORD=CHANGE_ME
```

## Evolución

Fase inicial: secret files/variables protegidos con backups seguros, fuera de Git, con permisos de archivo restrictivos (`chmod 600`).
Fase posterior: evaluar Vault/SOPS/age/External Secrets según necesidad real.

El gestor de secretos no sirve si su master key vive al lado del repositorio que intenta proteger.

## Secrets en GitOps (k3s + Argo CD)

GitOps introduce un problema específico: Argo CD sincroniza manifiestos **desde Git**, pero un `Secret` de Kubernetes en texto plano en un repo (aunque sea privado) es equivalente a subir la contraseña. No alcanza con "no lo subo a un repo público" — el historial de Git, forks internos y backups del repo heredan el secreto para siempre.

**Target state:** antes de que Argo CD gestione cualquier aplicación con secretos reales, adoptar uno de estos patrones (no ambos, para no duplicar la superficie de gestión):

- **SOPS + age**: los archivos de secretos se cifran con `sops` usando una clave `age` que **nunca** vive en el repo, y se commitea el YAML cifrado. Un `ConfigManagementPlugin` o `kustomize` con `ksops` los descifra en el momento de sincronizar. Encaja bien con un homelab de un solo operador (una sola clave `age` que respaldar).
- **Sealed Secrets** (Bitnami): un controlador en el cluster expone una clave pública; `kubeseal` cifra el `Secret` localmente y el YAML resultante (`SealedSecret`) sí es seguro de commitear — solo el controlador dentro del cluster puede descifrarlo. Requiere respaldar la clave privada del controlador (si se pierde, todos los `SealedSecret` quedan irrecuperables).

**Decision Pending:** cuál de los dos se adopta. Mientras no se decida, ningún manifiesto GitOps debe llevar un `Secret` de Kubernetes en texto plano — usar variables de entorno inyectadas manualmente (`kubectl create secret` fuera de Git) como puente temporal, documentado como deuda técnica explícita, no como solución final.

La misma lógica aplica al propio Argo CD: su kubeconfig/tokens administrativos nunca van a Git, con o sin secret manager (ver [ADR-004 · Argo CD como motor de GitOps](../arquitectura/decisiones-arquitectonicas.md#adr-004--argo-cd-como-motor-de-gitops)).
