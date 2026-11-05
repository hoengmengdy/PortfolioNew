import { m } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleAlert,
  ExternalLink as ExternalIcon,
  Info,
  X,
} from 'lucide-react';
import { useEffect, useLayoutEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router';
import { projects } from '../../data/projects';
import { useLanguage } from '../../hooks/useLanguage';
import type { Project } from '../../types';
import { ExternalLink } from '../ui/ExternalLink';
import { TechIcon } from '../ui/TechIcon';
import { ProjectCover } from './ProjectCover';

export default function ProjectModal({ project }: { project: Project }) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const copy = t.projects.items[project.slug];

  const position = projects.indexOf(project);
  const previous = projects[(position - 1 + projects.length) % projects.length];
  const next = projects[(position + 1) % projects.length];

  // A native modal dialog provides the focus trap and inert background. Closing it hands
  // focus back to the card that opened it, which only works while it is still in the
  // document, so this must be a layout effect: its cleanup runs before React removes it.
  useLayoutEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
    return () => dialog?.close();
  }, []);

  // Each project replaces the dialog's content, so start at the top and on the new title.
  useEffect(() => {
    dialogRef.current?.scrollTo({ top: 0 });
    titleRef.current?.focus({ preventScroll: true });
  }, [project.slug]);

  const close = () => navigate('/');

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="project-title"
      className="project-dialog"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) close();
      }}
    >
      <m.div
        key={project.slug}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="sticky top-3 z-10 flex h-0 justify-end pr-3">
          <button
            type="button"
            onClick={close}
            aria-label={t.common.close}
            className="grid size-11 shrink-0 place-items-center rounded-full bg-black/75 text-white transition-colors hover:bg-black"
          >
            <X aria-hidden="true" className="size-5" />
          </button>
        </div>
        <div className="relative">
          <ProjectCover
            project={project}
            alt={copy.coverAlt}
            sizes="(min-width: 1024px) 60rem, 96vw"
            eager
          />
          <span className="absolute bottom-3 left-4 rounded-full bg-black/70 px-2.5 py-0.5 text-xs text-white">
            {project.cover.kind === 'screenshot' ? t.projects.screenshot : t.projects.illustration}
          </span>
        </div>

        <div className="p-6 md:p-10">
          <p className="eyebrow">{copy.category}</p>
          <h2
            ref={titleRef}
            id="project-title"
            tabIndex={-1}
            className="mt-3 text-3xl font-medium outline-none md:text-4xl"
          >
            {copy.title}
          </h2>
          <p className="mt-5 text-lg text-muted">{copy.description}</p>

          {copy.note ? (
            <p className="mt-6 flex gap-3 rounded-xl border border-line bg-gold/5 p-4 text-sm">
              <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-gold-text" />
              <span>{copy.note}</span>
            </p>
          ) : null}

          <div className="mt-10 grid gap-10 md:grid-cols-[3fr_2fr]">
            <div>
              <h3 className="eyebrow">{t.projects.keyFeatures}</h3>
              {copy.features.length > 0 ? (
                <ul className="mt-4 space-y-2.5">
                  {copy.features.map((feature) => (
                    <li key={feature} className="flex gap-3">
                      <Check aria-hidden="true" className="mt-1 size-4 shrink-0 text-gold-text" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-muted">{t.projects.pendingFeatures}</p>
              )}

              {copy.unverified ? (
                <div className="mt-8">
                  <h3 className="eyebrow">{t.projects.unverifiedTitle}</h3>
                  <ul className="mt-4 space-y-2.5">
                    {copy.unverified.map((item) => (
                      <li key={item} className="flex gap-3 text-muted">
                        <CircleAlert aria-hidden="true" className="mt-1 size-4 shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>

            <div className="space-y-8">
              <div>
                <h3 className="eyebrow">{t.projects.technologies}</h3>
                <ul className="mt-4 flex flex-wrap gap-2">
                  {project.stack.map((tech) => (
                    <li key={tech} className="chip">
                      <TechIcon name={tech} className="size-3 text-gold-text" />
                      {tech}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="eyebrow">{t.projects.links}</h3>
                {project.repoUrl || project.demoUrl ? (
                  <div className="mt-4 flex flex-wrap gap-3">
                    {project.demoUrl ? (
                      <ExternalLink href={project.demoUrl} className="btn btn-gold">
                        {t.projects.liveDemo}
                        <ExternalIcon aria-hidden="true" className="size-4" />
                      </ExternalLink>
                    ) : null}
                    {project.repoUrl ? (
                      <ExternalLink href={project.repoUrl} className="btn btn-line">
                        <TechIcon name="GitHub" className="size-4" />
                        {t.projects.sourceCode}
                      </ExternalLink>
                    ) : null}
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-muted">{t.projects.noLinks}</p>
                )}
              </div>
            </div>
          </div>

          {previous && next ? (
            <nav className="mt-10 flex justify-between gap-4 border-t border-line pt-6 text-sm">
              <Link
                replace
                to={`/projects/${previous.slug}`}
                className="inline-flex min-h-10 items-center gap-2 text-muted transition-colors hover:text-gold-text"
              >
                <ArrowLeft aria-hidden="true" className="size-4" />
                {t.projects.previous}
              </Link>
              <Link
                replace
                to={`/projects/${next.slug}`}
                className="inline-flex min-h-10 items-center gap-2 text-muted transition-colors hover:text-gold-text"
              >
                {t.projects.next}
                <ArrowRight aria-hidden="true" className="size-4" />
              </Link>
            </nav>
          ) : null}
        </div>
      </m.div>
    </dialog>
  );
}
