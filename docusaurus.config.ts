import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import {themes as prismThemes} from 'prism-react-renderer';

const config: Config = {
  title: 'O.S.C.A.R. HomeLab',
  tagline: 'Build it. Break it. Learn it. Automate it.',
  favicon: 'img/oscar-mark.svg',

  // Railway serves this project at the service root. Set SITE_URL in Railway
  // when a custom/public domain is available.
  url: process.env.SITE_URL ?? 'http://localhost:3000',
  baseUrl: process.env.BASE_URL ?? '/',

  organizationName: 'rudemex',
  projectName: 'oscar-homelab',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'warn',

  i18n: {
    defaultLocale: 'es',
    locales: ['es'],
  },

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
      onBrokenMarkdownImages: 'throw',
    },
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
          // Requiere que cada archivo tenga al menos un commit; con el repo
          // recién inicializado (sin historia de git) esto rompía `yarn build`
          // con un error fatal de `git log`. Reactivado tras el primer commit.
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
          editUrl: 'https://github.com/rudemex/oscar-homelab/edit/main/',
        },
        blog: {
          showReadingTime: true,
          routeBasePath: 'bitacora',
          blogTitle: 'Bitácora O.S.C.A.R.',
          blogDescription: 'Cambios, decisiones y evolución del homelab O.S.C.A.R.',
          postsPerPage: 10,
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/oscar-social.svg',
    metadata: [
      {
        name: 'keywords',
        content:
          'homelab, proxmox, docker, kubernetes, k3s, argocd, grafana, automation, observability, oscar',
      },
    ],
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    navbar: {
      title: 'O.S.C.A.R.',
      logo: {
        alt: 'O.S.C.A.R. HomeLab',
        src: 'img/oscar-mark.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentación',
        },
        {to: '/docs/roadmap/roadmap-general', label: 'Roadmap', position: 'left'},
        {to: '/docs/runbooks/indice-runbooks', label: 'Runbooks', position: 'left'},
        {to: '/docs/laboratorios/indice', label: 'Labs', position: 'left'},
        {to: '/bitacora', label: 'Bitácora', position: 'left'},
        {
          href: 'https://github.com/rudemex/oscar-homelab',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Construcción',
          items: [
            {label: 'Empezar', to: '/docs/intro'},
            {label: 'Estado actual', to: '/docs/arquitectura/estado-actual'},
            {label: 'Arquitectura', to: '/docs/arquitectura/vision-general'},
            {label: 'Roadmap', to: '/docs/roadmap/roadmap-general'},
          ],
        },
        {
          title: 'Operación',
          items: [
            {label: 'Servicios', to: '/docs/servicios/catalogo'},
            {label: 'Runbooks', to: '/docs/runbooks/indice-runbooks'},
            {label: 'Troubleshooting', to: '/docs/troubleshooting/metodologia'},
          ],
        },
        {
          title: 'Proyecto',
          items: [
            {label: 'Bitácora', to: '/bitacora'},
            {label: 'Repositorio', href: 'https://github.com/rudemex/oscar-homelab'},
          ],
        },
      ],
      copyright: `O.S.C.A.R. HomeLab · ${new Date().getFullYear()}`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'json', 'powershell', 'docker'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
