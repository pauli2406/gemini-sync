import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started-local',
        'migration-custom-connectors',
        'discovery-engine-cli-playbook',
        'connector-studio',
        'troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Connector Authoring',
      items: [
        'connector-authoring',
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
      label: 'Operations',
      items: ['operations-runbook', 'architecture'],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: ['api-reference'],
    },
    {
      type: 'category',
      label: 'Governance & Quality',
      items: ['roadmap', 'reliability-phase', 'load-testing', 'splunk-dashboard-queries'],
    },
  ],
};

export default sidebars;
