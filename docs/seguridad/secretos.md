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

## Secrets en Docker Compose: Infisical (2026-09-19)

Decidido y desplegado — reemplaza al "fase inicial" de arriba (archivos `.env` sueltos con `chmod 600`, sin backup real más allá de copiarlos a mano a Vaultwarden) para las apps que corren como Docker Compose (no k3s, ver sección de abajo para ese caso distinto).

**Evaluadas tres opciones** (Vault/OpenBao, Infisical, SOPS+age) — se descartó SOPS+age (sin servidor, pero el usuario prefirió una herramienta con UI real en vez de un flujo de archivos cifrados) y Vault/OpenBao (más poder — secrets dinámicos, PKI, leasing — que no se aprovecha a esta escala, contra más carga operativa: unseal, políticas, backend de storage). Se eligió **Infisical**: Docker-native, UI real, modelo de "machine identity" pensado para inyectar secrets en contenedores en automático.

Desplegado en `devops01` (`/srv/oscar/apps/infisical/`, backend + Postgres + Redis propios, imagen fijada a `v0.165.13`), publicado en `infisical.oscar.home` vía NPM. `compose.yaml`/`.env.example` versionados en el repo nuevo `oscar-compose` (Forgejo) — el `.env` real con los secrets de arranque de Infisical (paradoja a propósito: la propia base del gestor de secrets también tiene secrets, y esos sí quedan fuera de Git, igual que cualquier otro `.env`) sigue viviendo solo en `devops01`.

**No reemplaza a Vaultwarden** — Vaultwarden es para contraseñas que usa una persona (vos) a mano; Infisical es para secrets que consume una app o un pipeline de CI de forma automática. Dos herramientas, dos consumidores distintos, a propósito.

**Pendiente, no bloqueante:** migrar los `.env` que ya existen (Minecraft, CS2, y el resto de los Compose de OSCAR) a Infisical — hoy siguen siendo archivos sueltos en cada VM, Infisical está desplegado pero todavía no es la fuente real de ningún secreto existente.

## Secrets en GitOps (k3s + Argo CD)

GitOps introduce un problema específico: Argo CD sincroniza manifiestos **desde Git**, pero un `Secret` de Kubernetes en texto plano en un repo (aunque sea privado) es equivalente a subir la contraseña. No alcanza con "no lo subo a un repo público" — el historial de Git, forks internos y backups del repo heredan el secreto para siempre.

**Decidido y resuelto (2026-09-19):** ni SOPS+age ni Sealed Secrets — se extendió la misma decisión que para Docker Compose (arriba): **Infisical Secrets Operator**, instalado en k3s01 vía Argo CD (`apps/infisical-operator/`, chart oficial). Sincroniza `Secret`s nativos de Kubernetes desde Infisical usando el CRD `InfisicalSecret` — el manifest del CRD **sí va a Git** (no tiene el secreto en sí, solo la referencia: proyecto, ambiente, path), pero el `clientId`/`clientSecret` de la identidad que autentica al operador vive en un `Secret` de Kubernetes creado a mano (`kubectl create secret`), **nunca en Git** — mismo criterio que ya se usaba para `nexus-pull` (el `imagePullSecret` de `ci-demo`).

Validado de punta a punta (`apps/infisical-secrets/manifests/example-minecraft-sync.yaml`, namespace `oscar-lab`): un `InfisicalSecret` apuntando al folder `/minecraft` del proyecto "OSCAR Apps" generó un `Secret` nativo real con los 3 valores esperados.

**Gotcha real encontrado en el camino:** `infisical.oscar.home` no resolvía desde *dentro* del cluster (CoreDNS interno de k3s no lo conocía) — mismo problema que ya había pasado con `git.oscar.home` en su momento. Se resolvió agregando una entrada más al `ConfigMap` `coredns-custom` (namespace `kube-system`, ya existente) con el mismo patrón `template IN A` que la entrada de `git.oscar.home`.

**Deuda pendiente, no bloqueante:** un diff cosmético en Argo CD (`OutOfSync` aunque el recurso esté `Healthy` y funcionando bien) — el operador normaliza algunos campos del `InfisicalSecret` después de aplicado, distinto de lo que queda commiteado. No afecta la sincronización real, solo ensucia la UI de Argo CD; sin investigar a fondo todavía.

**Primer caso real migrado (2026-09-19):** el `imagePullSecret` `nexus-pull` de `ci-demo` — antes un `Secret` `kubernetes.io/dockerconfigjson` creado a mano, ahora un `InfisicalSecret` (`apps/ci-demo/templates/secrets.yaml`) que arma el `.dockerconfigjson` con un template de Go (`dict`/`b64enc`, sintaxis Sprig) a partir de `NEXUS_USER`/`NEXUS_PASSWORD` guardados en Infisical (`/ci-demo`). Validado: el contenido del Secret resultante es byte-a-byte igual al que existía a mano, y los pods de `ci-demo` siguen sanos sin ningún cambio en `deployment.yaml` (sigue referenciando `nexus-pull` por nombre, nada más cambió).

**`oscar-led-controller` queda afuera a propósito** — no tiene ningún secret real (imagen local sin registry, `pullPolicy: Never`; WLED no tiene auth) — confirmado leyendo el chart, no se inventó uno para tener "paridad" entre las dos apps.

La misma lógica aplica al propio Argo CD: su kubeconfig/tokens administrativos nunca van a Git, con o sin secret manager (ver [ADR-004 · Argo CD como motor de GitOps](../arquitectura/decisiones-arquitectonicas.md#adr-004--argo-cd-como-motor-de-gitops)).
