import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'IngestRelay Docs',
  tagline: 'Build connectors from on-prem systems to Gemini Enterprise with confidence.',
  favicon: 'img/favicon.ico',
  url: 'https://ingest-relay-docs.vercel.app',
  baseUrl: '/',
  organizationName: 'pauli2406',
  projectName: 'ingest-relay',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          routeBasePath: 'docs',
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/pauli2406/ingest-relay/edit/main/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/favicon.ico',
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'IngestRelay',
      logo: {
        alt: 'IngestRelay',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {to: '/docs/reference/api-reference', label: 'Reference', position: 'left'},
        {to: '/docs/contributing/contributing', label: 'Contributing', position: 'left'},
        {to: '/docs/changelog', label: 'Changelog', position: 'left'},
        {
          href: 'https://github.com/pauli2406/ingest-relay',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Start Here',
              to: '/docs/start-here',
            },
            {label: 'Tutorials', to: '/docs/tutorials/getting-started-local'},
          ],
        },
        {
          title: 'Reference',
          items: [
            {label: 'API Reference', to: '/docs/reference/api-reference'},
            {label: 'CLI Reference', to: '/docs/reference/cli'},
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Contributing',
              to: '/docs/contributing/contributing',
            },
            {
              label: 'Changelog',
              to: '/docs/changelog',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/pauli2406/ingest-relay',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} IngestRelay contributors.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
  scripts: [
    {
      src: 'https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js',
      defer: true,
    },
  ],
};

export default config;
