import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  eyebrow: string;
  description: ReactNode;
  to: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Guía rápida',
    eyebrow: 'START HERE',
    description: <>De cero a Proxmox + Docker + tu primer servicio andando, en un solo recorrido.</>,
    to: '/docs/guia-rapida',
  },
  {
    title: 'Arquitectura',
    eyebrow: 'DESIGN',
    description: <>Red, Proxmox, storage, Docker, Kubernetes, GitOps, seguridad y decisiones técnicas.</>,
    to: '/docs/arquitectura/vision-general',
  },
  {
    title: 'Servicios',
    eyebrow: 'PLATFORM',
    description: <>Qué hace cada servicio, dónde corre, qué depende de él y ejemplos concretos de uso.</>,
    to: '/docs/servicios/catalogo',
  },
  {
    title: 'Runbooks',
    eyebrow: 'OPERATE',
    description: <>Procedimientos repetibles para incidentes, actualizaciones, backup, restore y recuperación.</>,
    to: '/docs/runbooks/indice-runbooks',
  },
  {
    title: 'Laboratorios',
    eyebrow: 'LEARN',
    description: <>Prácticas progresivas para aprender desplegando cosas reales sin comprometer el core.</>,
    to: '/docs/laboratorios/indice',
  },
  {
    title: 'O.S.C.A.R. AI',
    eyebrow: 'AUTOMATE',
    description: <>MCP, agentes, RAG y automatización para que el homelab pueda observarse y operarse con IA.</>,
    to: '/docs/ia/vision-general',
  },
];

function Feature({title, eyebrow, description, to}: FeatureItem) {
  return (
    <div className={clsx('col col--4', styles.featureColumn)}>
      <Link to={to} className={styles.featureLink}>
        <article className={styles.featureCard}>
          <span className={styles.eyebrow}>{eyebrow}</span>
          <Heading as="h3">{title}</Heading>
          <p>{description}</p>
          <span className={styles.learnMore}>Explorar →</span>
        </article>
      </Link>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props) => (
            <Feature key={props.title} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
