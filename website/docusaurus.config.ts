import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Gemini Sync Bridge Docs',
  tagline: 'Build connectors from on-prem systems to Gemini Enterprise with confidence.',
  favicon: 'img/favicon.ico',
  url: 'https://gemini-sync-bridge-docs.vercel.app',
  baseUrl: '/',
  organizationName: 'pauli2406',
  projectName: 'gemini-sync',

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
            'https://github.com/pauli2406/gemini-sync/edit/main/',
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
      title: 'Gemini Sync Bridge',
      logo: {
        alt: 'Gemini Sync Bridge',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {to: '/docs/api-reference', label: 'API', position: 'left'},
        {to: '/docs/discovery-engine-cli-playbook', label: 'CLI Playbook', position: 'left'},
        {
          href: 'https://github.com/pauli2406/gemini-sync',
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
              label: 'Quickstart',
              to: '/docs/discovery-engine-cli-playbook',
            },
            {label: 'API Reference', to: '/docs/api-reference'},
          ],
        },
        {
          title: 'Operations',
          items: [
            {label: 'Operations Runbook', to: '/docs/operations-runbook'},
            {label: 'Troubleshooting', to: '/docs/troubleshooting'},
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Roadmap',
              to: '/docs/roadmap',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/pauli2406/gemini-sync',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Gemini Sync Bridge contributors.`,
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
