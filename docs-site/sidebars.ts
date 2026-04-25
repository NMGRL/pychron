import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',

    {
      type: 'category',
      label: 'Getting Started',
      collapsible: true,
      collapsed: false,
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/experiment-workflow',
      ],
    },

    {
      type: 'category',
      label: 'Hardware',
      collapsible: true,
      collapsed: true,
      items: [
        'hardware/overview',
        'hardware/compatibility-matrix',
      ],
    },

    {
      type: 'category',
      label: 'DVC',
      collapsible: true,
      collapsed: true,
      link: {
        type: 'doc',
        id: 'dvc/setup-guide',
      },
      items: [
        'dvc/setup-guide',
        'dvc/first-run',
        'dvc/configuration',
        'dvc/failure-modes',
        'dvc/offline-mode',
      ],
    },

    {
      type: 'category',
      label: 'Migration',
      collapsible: true,
      collapsed: true,
      items: [
        'migration/massspec-overview',
        'migration/massspec-migration',
      ],
    },

    {
      type: 'category',
      label: 'PyScripts',
      collapsible: true,
      collapsed: true,
      items: [
        'pyscripts/overview',
        'pyscripts/api-reference',
      ],
    },

    {
      type: 'category',
      label: 'Pipeline',
      collapsible: true,
      collapsed: true,
      items: [
        'pipeline/data-reduction',
      ],
    },

    {
      type: 'category',
      label: 'Deployment',
      collapsible: true,
      collapsed: true,
      items: [
        'deployment/multi-node',
      ],
    },

    {
      type: 'category',
      label: 'Dashboard',
      collapsible: true,
      collapsed: true,
      items: [
        'dashboard/configuration',
      ],
    },
  ],
};

export default sidebars;
