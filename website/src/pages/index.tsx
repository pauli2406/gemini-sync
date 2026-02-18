import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const entryPoints = [
  {
    title: 'Start Here',
    description: 'Pick the right path for operators, connector authors, or contributors.',
    to: '/docs/start-here',
  },
  {
    title: 'Tutorial: Local Setup',
    description: 'From fresh clone to first successful run and UI verification.',
    to: '/docs/tutorials/getting-started-local',
  },
  {
    title: 'Tutorial: GCP Onboarding',
    description: 'Create datastore targets, run ingestion, and validate import results.',
    to: '/docs/tutorials/gcp-onboarding',
  },
  {
    title: 'How-to: Connector Authoring',
    description: 'Create valid connector contracts and keep example policy boundaries.',
    to: '/docs/how-to/connector-authoring',
  },
  {
    title: 'How-to: Operate Runs',
    description: 'Ops endpoints, SLO checks, replay commands, and failure handling.',
    to: '/docs/how-to/operate-runs',
  },
  {
    title: 'API Reference',
    description: 'OpenAPI documentation for push, studio, and ops endpoints.',
    to: '/docs/reference/api-reference',
  },
  {
    title: 'Contributing',
    description: 'Developer setup, CI gates, and release policy expectations.',
    to: '/docs/contributing/contributing',
  },
  {
    title: 'Changelog',
    description: 'Track notable runtime, docs, and governance changes.',
    to: '/docs/changelog',
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
            Diataxis Documentation For Operators And Contributors
          </Heading>
          <p className={styles.subtitle}>
            Learn through tutorials, execute with how-to guides, understand internals in concepts,
            and verify details in reference docs.
          </p>
          <div className={styles.heroActions}>
            <Link className="button button--primary button--lg" to="/docs/start-here">
              Open Start Here
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/reference/api-reference">
              Open Reference
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
