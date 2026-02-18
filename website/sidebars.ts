import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'start-here',
    {
      type: 'category',
      label: 'Tutorials',
      items: ['tutorials/getting-started-local', 'tutorials/gcp-onboarding'],
    },
    {
      type: 'category',
      label: 'How-to',
      items: [
        'how-to/connector-authoring',
        'how-to/connector-studio',
        'how-to/migrate-custom-connectors',
        'how-to/operate-runs',
        'how-to/troubleshooting',
        'how-to/load-testing',
        {
          type: 'category',
          label: 'Connector Modes',
          items: [
            'how-to/connectors/sql-pull',
            'how-to/connectors/rest-pull',
            'how-to/connectors/rest-push',
            'how-to/connectors/file-pull',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Concepts',
      items: [
        'concepts/architecture',
        'concepts/connector-model',
        'concepts/data-envelope-ndjson',
        'concepts/reconciliation-upserts-deletes',
        'concepts/idempotency-and-deltas',
        'concepts/security-and-governance',
        'concepts/reliability-and-slos',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/api-reference',
        'reference/cli',
        'reference/env-vars',
        'reference/error-codes',
        'reference/connector-fields',
        {
          type: 'category',
          label: 'Providers',
          items: [
            'reference/providers/postgres',
            'reference/providers/mysql',
            'reference/providers/mssql',
            'reference/providers/oracle',
            'reference/providers/http',
            'reference/providers/file',
            'reference/providers/future',
          ],
        },
        'reference/splunk-dashboard-queries',
      ],
    },
    {
      type: 'category',
      label: 'Contributing',
      items: [
        'contributing/contributing',
        'contributing/dev-setup',
        'contributing/testing-ci',
        'contributing/release-process',
      ],
    },
    {
      type: 'category',
      label: 'Project',
      items: ['roadmap', 'changelog'],
    },
  ],
};

export default sidebars;
