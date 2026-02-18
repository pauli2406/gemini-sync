import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Start Here',
      items: [
        'start-here',
        'getting-started-local',
        'migration-custom-connectors',
        'discovery-engine-cli-playbook',
      ],
    },
    {
      type: 'category',
      label: 'Build Connectors',
      items: [
        'connector-authoring',
        'connector-studio',
        'connector-mode-sql-pull',
        'connector-mode-rest-pull',
        'connector-mode-rest-push',
        'connector-mode-file-pull',
        'connector-field-reference',
        'connector-provider-postgres',
        'connector-provider-mysql',
        'connector-provider-mssql',
        'connector-provider-oracle',
        'connector-provider-http',
        'connector-provider-file',
        'connector-provider-future',
      ],
    },
    {
      type: 'category',
      label: 'Migrate & Operate',
      items: [
        'operations-runbook',
        'architecture',
        'troubleshooting',
        'reliability-phase',
      ],
    },
    {
      type: 'category',
      label: 'API & Governance',
      items: ['api-reference', 'roadmap', 'load-testing', 'splunk-dashboard-queries'],
    },
  ],
};

export default sidebars;
