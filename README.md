# O.S.C.A.R. HomeLab

Documentación viva para construir, operar y evolucionar **O.S.C.A.R.**: rack, red, Proxmox, Docker, Kubernetes, GitOps, observabilidad, backups, automatización y capa de IA.

Esta versión toma como base el template [`rudemex/railway-docusaurus-v3`](https://github.com/rudemex/railway-docusaurus-v3): Docusaurus v3 + TypeScript + estructura clásica + despliegue mediante Docker/Railway.

## Desarrollo local

Requisitos:

- Node.js 20 o superior;
- Yarn.

```bash
yarn
yarn start
```

Docusaurus levanta el sitio localmente y recarga los cambios durante la edición.

## Validación

```bash
yarn typecheck
yarn build
```

O, en un solo paso:

```bash
yarn check
```

## Deploy en Railway

El repositorio incluye `Dockerfile`, siguiendo el enfoque del template base.

1. Crear un proyecto en Railway.
2. Conectar `rudemex/oscar-homelab`.
3. Railway detecta el `Dockerfile` y construye el sitio.
4. Generar un dominio público o configurar uno propio.
5. Definir `SITE_URL=https://tu-dominio` para que Docusaurus genere metadata/canonical URLs correctas.

El contenedor usa automáticamente la variable `PORT` suministrada por Railway.

## Estructura

```text
oscar-homelab/
├── blog/                    bitácora de evolución del homelab
├── docs/                    guía técnica y runbooks
├── examples/                ejemplos Docker/Kubernetes
├── infrastructure/          infraestructura versionable
├── inventory/               inventario de hardware y servicios
├── src/
│   ├── components/          componentes de la portada
│   ├── css/                 tema visual
│   └── pages/               páginas custom de Docusaurus
├── static/                  assets públicos
├── Dockerfile               build/deploy para Railway
├── docusaurus.config.ts     configuración del sitio
├── sidebars.ts              navegación documental
└── package.json
```

## Principio documental

Cada área intenta separar:

- **estado actual**: lo que existe hoy;
- **arquitectura objetivo**: hacia dónde evoluciona O.S.C.A.R.;
- **laboratorio**: pruebas que no son dependencia del entorno estable.

La documentación debe indicar no solo cómo instalar un servicio, sino también para qué sirve, qué depende de él, cómo verificarlo, cómo respaldarlo y cómo recuperarlo.
