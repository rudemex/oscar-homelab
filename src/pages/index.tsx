import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <div className={styles.kicker}>HOME LAB · INFRASTRUCTURE · AUTOMATION · AI</div>
        <Heading as="h1" className={styles.heroTitle}>
          O.S.C.A.R.
        </Heading>
        <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
        <p className={styles.heroDescription}>
          El manual vivo para construir y operar un homelab real: rack, red, Proxmox, Docker,
          k3s, GitOps, observabilidad, backups, automatización y una capa de IA encima de todo.
        </p>
        <div className={styles.buttons}>
          <Link className="button button--primary button--lg" to="/docs/guia-rapida">
            Empezar a construir
          </Link>
          <Link className="button button--secondary button--lg" to="/docs/arquitectura/vision-general">
            Ver arquitectura
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description="Documentación oficial del homelab O.S.C.A.R.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <section className={styles.manifesto}>
          <div className="container">
            <div className={styles.manifestoGrid}>
              <div>
                <span className={styles.sectionLabel}>PRINCIPIO DE DISEÑO</span>
                <Heading as="h2">Un homelab que se puede entender, romper y reconstruir.</Heading>
              </div>
              <div className={styles.manifestoText}>
                La documentación separa siempre el <strong>estado actual</strong>, la{' '}
                <strong>arquitectura objetivo</strong> y los <strong>laboratorios opcionales</strong>.
                Cada componente debe tener propósito, dependencias, validación, backup y un camino de recuperación.
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
