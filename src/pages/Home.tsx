import { lazy, Suspense, useEffect } from 'react';
import { Navigate, useMatch } from 'react-router';
import { Footer } from '../components/layout/Footer';
import { ScrollProgress } from '../components/layout/ScrollProgress';
import { Navbar } from '../components/navigation/Navbar';
import { About } from '../components/sections/About';
import { Contact } from '../components/sections/Contact';
import { Education } from '../components/sections/Education';
import { Hero } from '../components/sections/Hero';
import { Journey } from '../components/sections/Journey';
import { ManagedPages } from '../components/sections/ManagedPages';
import { Projects } from '../components/sections/Projects';
import { Services } from '../components/sections/Services';
import { Skills } from '../components/sections/Skills';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { projects } from '../data/projects';
import { useLanguage } from '../hooks/useLanguage';
import { useSeo } from '../hooks/useSeo';

const ProjectModal = lazy(() => import('../components/projects/ProjectModal'));

export default function Home() {
  const { t } = useLanguage();
  const slug = useMatch('/projects/:slug')?.params.slug;
  const project = projects.find((item) => item.slug === slug);
  const projectCopy = project ? t.projects.items[project.slug] : null;

  useSeo({
    title: projectCopy ? `${projectCopy.title} | ${t.common.name}` : t.meta.title,
    description: projectCopy ? projectCopy.summary : t.meta.description,
    path: project ? `/projects/${project.slug}` : '/',
  });

  // Sections render after the browser's own hash scroll has already run.
  useEffect(() => {
    const target = window.location.hash.slice(1);
    if (target) document.getElementById(target)?.scrollIntoView();
  }, []);

  if (slug && !project) return <Navigate to="/404" replace />;

  return (
    <>
      <a
        href="#main"
        className="sr-only z-50 rounded-full bg-gold px-4 py-2 font-semibold text-on-gold focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
      >
        {t.common.skipToContent}
      </a>
      <ScrollProgress />
      <Navbar />
      <main id="main" tabIndex={-1} className="outline-none">
        <Hero />
        <About />
        <Skills />
        <Projects />
        <Education />
        <Services />
        <ManagedPages />
        <Journey />
        <Contact />
      </main>
      <Footer />

      {project ? (
        <ErrorBoundary fallback={null}>
          <Suspense fallback={null}>
            <ProjectModal project={project} />
          </Suspense>
        </ErrorBoundary>
      ) : null}
    </>
  );
}
