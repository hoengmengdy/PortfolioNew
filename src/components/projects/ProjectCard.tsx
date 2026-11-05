import { m } from 'framer-motion';
import { ArrowUpRight, Check, Star } from 'lucide-react';
import { Link } from 'react-router';
import { useLanguage } from '../../hooks/useLanguage';
import type { Project } from '../../types';
import { formatIndex } from '../../utils/format';
import { ExternalLink } from '../ui/ExternalLink';
import { TechIcon } from '../ui/TechIcon';
import { ProjectCover } from './ProjectCover';

const MAX_STACK = 4;
const MAX_FEATURES = 3;

interface ProjectCardProps {
  project: Project;
  number: number;
}

export function ProjectCard({ project, number }: ProjectCardProps) {
  const { t, language } = useLanguage();
  const copy = t.projects.items[project.slug];
  const detailsPath = `/projects/${project.slug}`;
  const extraStack = project.stack.length - MAX_STACK;

  return (
    <m.article
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="panel group flex w-full flex-col overflow-hidden transition-[border-color,box-shadow,translate] duration-300 hover:-translate-y-1 hover:border-gold/60 hover:shadow-[var(--shadow-glow)]"
    >
      <Link
        to={detailsPath}
        tabIndex={-1}
        aria-hidden="true"
        className="relative block overflow-hidden"
      >
        <ProjectCover
          project={project}
          alt=""
          sizes="(min-width: 1024px) 28vw, (min-width: 768px) 46vw, 92vw"
          imageClassName="transition-[transform,filter] duration-500 [filter:var(--cover-filter)] group-hover:scale-[1.03] group-hover:[filter:none]"
        />
        <span className="absolute top-3 left-3 rounded-full bg-black/70 px-2.5 py-0.5 font-display text-xs text-white">
          {formatIndex(number, language)}
        </span>
        {project.featured ? (
          <span className="absolute top-3 right-3 inline-flex items-center gap-1 rounded-full bg-gold px-2.5 py-0.5 text-xs font-semibold text-on-gold">
            <Star aria-hidden="true" className="size-3 fill-current" />
            {t.projects.featured}
          </span>
        ) : null}
      </Link>

      <div className="flex flex-1 flex-col p-6">
        <p className="eyebrow">{copy.category}</p>
        <h3 className="mt-3 font-display text-xl font-medium">{copy.title}</h3>
        <p className="mt-3 text-sm text-muted">{copy.summary}</p>

        {copy.features.length > 0 ? (
          <ul className="mt-4 space-y-1.5 text-sm">
            {copy.features.slice(0, MAX_FEATURES).map((feature) => (
              <li key={feature} className="flex gap-2">
                <Check aria-hidden="true" className="mt-1 size-3.5 shrink-0 text-gold-text" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-sm text-muted italic [&:lang(km)]:not-italic">
            {t.projects.pendingFeatures}
          </p>
        )}

        <ul className="mt-5 flex flex-wrap gap-1.5">
          {project.stack.slice(0, MAX_STACK).map((tech) => (
            <li key={tech} className="chip">
              <TechIcon name={tech} className="size-3 text-gold-text" />
              {tech}
            </li>
          ))}
          {extraStack > 0 ? <li className="chip">+{extraStack}</li> : null}
        </ul>

        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 pt-6">
          <Link
            to={detailsPath}
            aria-label={`${t.projects.viewDetails}: ${copy.title}`}
            className="inline-flex min-h-10 items-center gap-1.5 text-sm font-semibold text-gold-text hover:underline"
          >
            {t.projects.viewDetails}
            <ArrowUpRight aria-hidden="true" className="size-4" />
          </Link>
          <div className="ml-auto flex items-center gap-3 text-sm">
            {project.repoUrl ? (
              <ExternalLink
                href={project.repoUrl}
                aria-label={`${t.projects.sourceCode}: ${copy.title}`}
                className="inline-flex min-h-10 items-center text-muted transition-colors hover:text-fg"
              >
                {t.projects.sourceCode}
              </ExternalLink>
            ) : null}
            {project.demoUrl ? (
              <ExternalLink
                href={project.demoUrl}
                aria-label={`${t.projects.liveDemo}: ${copy.title}`}
                className="inline-flex min-h-10 items-center text-muted transition-colors hover:text-fg"
              >
                {t.projects.liveDemo}
              </ExternalLink>
            ) : null}
          </div>
        </div>
      </div>
    </m.article>
  );
}
