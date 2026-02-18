import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const entryPoints = [
  {
    title: 'Start Here',
    description:
      'Choose the fastest path: first local run, staging migration, connector authoring, or operations.',
    to: '/docs/start-here',
  },
  {
    title: 'Local Getting Started',
    description:
      'Run a full local setup with Docker Postgres, seeded source data, and a successful first connector run.',
    to: '/docs/getting-started-local',
  },
  {
    title: 'Migration Checklist',
    description:
      'Move custom connectors out of this runtime repo with a staged, command-driven cutover and rollback plan.',
    to: '/docs/migration-custom-connectors',
  },
  {
    title: 'Quickstart CLI Playbook',
    description: 'Create data stores, wire GCS permissions, run connectors, and verify imports.',
    to: '/docs/discovery-engine-cli-playbook',
  },
  {
    title: 'Connector Studio',
    description: 'Use guided forms to create, validate, preview, and propose connector PRs.',
    to: '/docs/connector-studio',
  },
  {
    title: 'API Reference',
    description: 'Inspect live OpenAPI for `/v1/studio/*`, `/v1/ops/*`, and push ingestion APIs.',
    to: '/docs/api-reference',
  },
  {
    title: 'Connector Authoring',
    description: 'Define SQL/REST connectors with reliable reconciliation and production-safe defaults.',
    to: '/docs/connector-authoring',
  },
  {
    title: 'Operations Runbook',
    description: 'Troubleshoot failures quickly with run state, SLO checks, and recovery commands.',
    to: '/docs/operations-runbook',
  },
];

export default function Home(): ReactNode {
  return (
    <Layout
      title="Documentation"
      description="Gemini Sync Bridge hosted documentation">
      <main className={styles.main}>
        <section className={styles.hero}>
          <p className={styles.kicker}>Gemini Sync Bridge</p>
          <Heading as="h1" className={styles.title}>
            Docs For Building, Migrating, And Operating Connectors
          </Heading>
          <p className={styles.subtitle}>
            Build, operate, and evolve connectors from on-prem systems to Gemini Enterprise with
            one canonical playbook.
          </p>
          <div className={styles.heroActions}>
            <Link className="button button--primary button--lg" to="/docs/start-here">
              Open Start Here
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/migration-custom-connectors">
              Open Migration Guide
            </Link>
          </div>
        </section>

        <section className={styles.grid}>
          {entryPoints.map((item) => (
            <Link key={item.to} className={styles.card} to={item.to}>
              <Heading as="h3">{item.title}</Heading>
              <p>{item.description}</p>
            </Link>
          ))}
        </section>
      </main>
    </Layout>
  );
}
