import { ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router';
import { useLanguage } from '../../hooks/useLanguage';
import { formatIndex } from '../../utils/format';
import { Reveal } from '../ui/Reveal';

export function Journey() {
  const { t, language } = useLanguage();
  const { journey, projects } = t;

  return (
    <section id="journey" aria-labelledby="journey-title" className="section bg-surface">
      <div className="wrap grid gap-12 lg:grid-cols-[2fr_3fr] lg:gap-20">
        <Reveal className="self-start lg:sticky lg:top-28">
          <p className="eyebrow flex items-center gap-3">
            <span aria-hidden="true">{formatIndex(6, language)}</span>
            <span aria-hidden="true" className="h-px w-10 bg-gold" />
            {journey.eyebrow}
          </p>
          <h2 id="journey-title" className="mt-5 text-4xl font-medium md:text-6xl">
            {journey.title}
          </h2>
          <p className="mt-5 text-lg text-muted">{journey.lead}</p>
        </Reveal>

        <ol>
          {journey.chapters.map((chapter, index) => (
            <li
              key={chapter.title}
              className="border-t border-line py-8 first:border-t-0 first:pt-0"
            >
              <Reveal className="grid gap-x-6 gap-y-2 sm:grid-cols-[3.5rem_1fr]">
                <span aria-hidden="true" className="gold-text font-display text-3xl font-medium">
                  {formatIndex(index + 1, language)}
                </span>
                <div>
                  <h3 className="text-2xl font-medium">{chapter.title}</h3>
                  <p className="mt-3 text-muted">{chapter.body}</p>
                  {chapter.projects.length > 0 ? (
                    <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
                      <span className="text-muted">{journey.seeWork}:</span>
                      {chapter.projects.map((slug) => (
                        <Link
                          key={slug}
                          to={`/projects/${slug}`}
                          className="inline-flex min-h-8 items-center gap-1 text-gold-text hover:underline"
                        >
                          {projects.items[slug].title}
                          <ArrowUpRight aria-hidden="true" className="size-3.5" />
                        </Link>
                      ))}
                    </div>
                  ) : null}
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
