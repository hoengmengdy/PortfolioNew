import { ArrowUpRight, Bell, ChevronDown, Megaphone, MessageCircle, PenSquare } from 'lucide-react';
import { useState } from 'react';
import { managedPages } from '../../data/pages';
import { useLanguage } from '../../hooks/useLanguage';
import { toKhmerDigits } from '../../utils/format';
import { ExternalLink } from '../ui/ExternalLink';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';
import { SocialIcon } from '../ui/SocialIcon';

/** Cards shown before "Show all": three full rows on desktop. */
const INITIAL_COUNT = 15;

const taskIcons = [PenSquare, MessageCircle, Megaphone, Bell];

/** Rotating gold-family gradients so the monograms read as a set without looking identical. */
const tones = [
  'from-[#f5d76e] to-[#b8922a]',
  'from-[#e8c766] to-[#8f6c0c]',
  'from-[#fff0b3] to-[#d4af37]',
  'from-[#d4af37] to-[#5e4606]',
  'from-[#f2d27a] to-[#a67c1a]',
];

/** First letter of each word (up to two), so "CAM - Sport News" becomes "CS". */
function initials(name: string) {
  const words = name.split(/[\s-]+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => Array.from(word)[0])
    .join('')
    .toUpperCase();
}

export function ManagedPages() {
  const { t, language } = useLanguage();
  const { pages } = t;
  const count = String(managedPages.length);
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? managedPages : managedPages.slice(0, INITIAL_COUNT);

  return (
    <section id="pages" aria-labelledby="pages-title" className="section bg-surface">
      <div className="wrap">
        <SectionHeading
          id="pages-title"
          index={6}
          eyebrow={pages.eyebrow}
          title={pages.title}
          lead={pages.lead}
        />

        <Reveal className="mb-10 flex flex-wrap items-center gap-x-8 gap-y-5">
          <p className="flex items-baseline gap-3">
            <span className="gold-text gold-shimmer font-display text-6xl leading-none font-semibold">
              {language === 'km' ? toKhmerDigits(count) : count}
            </span>
            <span className="text-muted">{pages.managedLabel}</span>
          </p>
          <ul className="flex flex-wrap gap-2">
            {pages.tasks.map((task, index) => {
              const Icon = taskIcons[index] ?? PenSquare;
              return (
                <li key={task} className="chip px-3.5 py-1.5 text-sm">
                  <Icon aria-hidden="true" className="size-3.5 text-gold-text" />
                  {task}
                </li>
              );
            })}
          </ul>
        </Reveal>

        <ul className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          {visible.map(({ name, url }, index) => {
            const card = (
              <>
                <span
                  aria-hidden="true"
                  className={`grid size-16 place-items-center rounded-full bg-gradient-to-br ${tones[index % tones.length]} font-display text-xl font-semibold text-on-gold shadow-[var(--shadow-glow)] ring-4 ring-bg transition-transform duration-300 group-hover:scale-105`}
                >
                  {initials(name)}
                </span>
                <span className="mt-4 line-clamp-2 font-display font-medium">{name}</span>
                <span className="mt-2 inline-flex items-center gap-1.5 text-xs text-muted">
                  <SocialIcon id="facebook" className="size-3.5 text-gold-text" />
                  {pages.role}
                </span>
                {url ? (
                  <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-gold-text">
                    {pages.viewPage}
                    <ArrowUpRight aria-hidden="true" className="size-3.5" />
                  </span>
                ) : null}
              </>
            );
            const className =
              'panel group flex h-full flex-col items-center p-5 text-center transition-transform duration-300 hover:-translate-y-1';

            return (
              <li key={`${name}-${index}`}>
                <Reveal delay={(index % 5) * 0.05} className="h-full">
                  {url ? (
                    <ExternalLink href={url} className={className}>
                      {card}
                    </ExternalLink>
                  ) : (
                    <div className={className}>{card}</div>
                  )}
                </Reveal>
              </li>
            );
          })}
        </ul>

        {managedPages.length > INITIAL_COUNT ? (
          <div className="mt-10 flex justify-center">
            <button
              type="button"
              aria-expanded={showAll}
              onClick={() => setShowAll((value) => !value)}
              className="btn btn-line"
            >
              {showAll
                ? pages.showLess
                : `${pages.showAll} (${language === 'km' ? toKhmerDigits(count) : count})`}
              <ChevronDown
                aria-hidden="true"
                className={`size-4 transition-transform duration-300 ${showAll ? 'rotate-180' : ''}`}
              />
            </button>
          </div>
        ) : null}
      </div>
    </section>
  );
}
