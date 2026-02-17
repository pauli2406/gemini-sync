import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      items: ['discovery-engine-cli-playbook', 'connector-studio', 'troubleshooting'],
    },
    {
      type: 'category',
      label: 'Connector Authoring',
      items: ['connector-authoring'],
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
