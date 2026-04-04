import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Pychron',
  tagline: 'Automated Geoscience Laboratory Operations',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://nmgrl.github.io',
  baseUrl: '/pychron/',

  organizationName: 'NMGRL',
  projectName: 'pychron',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
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
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/NMGRL/pychron/tree/main/docs-site/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/pychron-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Pychron',
      logo: {
        alt: 'Pychron Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/NMGRL/pychron/wiki',
          label: 'Wiki',
          position: 'right',
          target: '_blank',
        },
        {
          href: 'https://github.com/NMGRL/pychron',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/intro',
            },
            {
              label: 'Installation Guide',
              to: '/docs/getting-started/installation',
            },
            {
              label: 'DVC Setup Guide',
              to: '/docs/dvc/setup-guide',
            },
          ],
        },
        {
          title: 'Hardware',
          items: [
            {
              label: 'Hardware Overview',
              to: '/docs/hardware/overview',
            },
            {
              label: 'Compatibility Matrix',
              to: '/docs/hardware/compatibility-matrix',
            },
            {
              label: 'MassSpec Migration',
              to: '/docs/migration/massspec-migration',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/NMGRL/pychron',
            },
            {
              label: 'Issues',
              href: 'https://github.com/NMGRL/pychron/issues',
            },
            {
              label: 'Pychron Labs LLC',
              href: 'https://pychronlabs.org',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Pychron Labs LLC. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'yaml', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
