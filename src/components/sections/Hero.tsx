import { m } from 'framer-motion';
import { ArrowRight, Send } from 'lucide-react';
import { profile } from '../../data/profile';
import { useLanguage } from '../../hooks/useLanguage';
import { CvButton } from '../ui/CvButton';
import { Portrait } from '../ui/Portrait';
import { TechIcon } from '../ui/TechIcon';

/** A ring of lotus petals: a quiet nod to Khmer ornament, built from one repeated path. */
const PETALS = Array.from({ length: 36 }, (_, index) => index * 10);

const orbitIcons = [
  { name: 'React', position: 'top-[6%] left-[16%]', delay: '0s' },
  { name: 'TypeScript', position: 'top-[20%] -right-[2%]', delay: '-1.5s' },
  { name: 'Python', position: 'top-[58%] -left-[3%]', delay: '-3s' },
  { name: 'Flask', position: 'bottom-[4%] left-[26%]', delay: '-4.5s' },
  { name: 'PostgreSQL', position: 'right-[4%] bottom-[14%]', delay: '-2s' },
];

// Starting just above zero lets browsers count this text as painted right away, so the
// entrance animation doesn't delay Largest Contentful Paint.
const rise = {
  hidden: { opacity: 0.01, y: 26 },
  shown: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const } },
};

function PortraitOrbit() {
  const { t } = useLanguage();

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[26rem] lg:max-w-[32rem]">
      <div
        aria-hidden="true"
        className="absolute inset-[8%] rounded-full bg-[radial-gradient(circle,color-mix(in_srgb,var(--gold)_26%,transparent),transparent_68%)] blur-2xl"
      />
      <svg
        viewBox="0 0 400 400"
        aria-hidden="true"
        className="animate-orbit absolute inset-0 size-full text-gold opacity-70"
      >
        <g fill="none" stroke="currentColor" strokeWidth="0.8">
          {PETALS.map((angle) => (
            <path
              key={angle}
              d="M200 8c11 14 11 30 0 44c-11-14-11-30 0-44Z"
              transform={`rotate(${angle} 200 200)`}
            />
          ))}
          <circle cx="200" cy="200" r="146" />
        </g>
      </svg>
      <svg
        viewBox="0 0 400 400"
        aria-hidden="true"
        className="animate-orbit-reverse absolute inset-0 size-full text-gold opacity-50"
      >
        <circle
          cx="200"
          cy="200"
          r="136"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          strokeDasharray="2 10"
          strokeLinecap="round"
        />
      </svg>

      <div className="absolute inset-[18%] overflow-hidden rounded-full border border-gold/50">
        <Portrait />
      </div>

      <div aria-hidden="true">
        {orbitIcons.map(({ name, position, delay }) => (
          <span
            key={name}
            title={name}
            style={{ animationDelay: delay }}
            className={`animate-drift absolute grid size-11 place-items-center rounded-full border border-line bg-[var(--glass)] text-gold-text backdrop-blur-sm md:size-14 ${position}`}
          >
            <TechIcon name={name} className="size-5 md:size-6" />
          </span>
        ))}
      </div>
      <span className="sr-only">{t.common.name}</span>
    </div>
  );
}

export function Hero() {
  const { t } = useLanguage();

  return (
    <section
      id="home"
      aria-labelledby="hero-title"
      className="relative isolate flex min-h-svh flex-col overflow-hidden pt-[4.5rem]"
    >
      <div aria-hidden="true" className="hero-grid absolute inset-0 -z-10" />

      <div className="wrap grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1.5fr_1fr] lg:py-16">
        <m.div
          initial="hidden"
          animate="shown"
          transition={{ staggerChildren: 0.1 }}
          variants={{ shown: { transition: { staggerChildren: 0.1 } } }}
        >
          <m.p
            variants={rise}
            className="inline-flex items-center gap-2.5 rounded-full border border-line px-4 py-1.5 text-sm text-muted"
          >
            <span
              aria-hidden="true"
              className={`size-1.5 rounded-full ${profile.availableForOpportunities ? 'bg-emerald-400' : 'bg-gold'}`}
            />
            {profile.availableForOpportunities ? t.hero.available : t.hero.badge}
          </m.p>

          <h1
            id="hero-title"
            className="mt-7 text-[clamp(2.4rem,5vw,4.25rem)] font-medium [&:lang(km)]:text-[clamp(2rem,4.2vw,3.5rem)]"
          >
            <m.span variants={rise} className="block">
              {t.hero.titleLine1}
            </m.span>
            <m.span variants={rise} className="block">
              <span className="gold-text">{t.hero.titleLine2}</span>
            </m.span>
          </h1>

          <m.p variants={rise} className="mt-7 max-w-xl text-lg text-muted">
            {t.hero.description}
          </m.p>

          <m.div variants={rise} className="mt-9 flex flex-wrap gap-3">
            <a href="#projects" className="btn btn-gold">
              {t.hero.explore}
              <ArrowRight aria-hidden="true" className="size-4" />
            </a>
            <CvButton
              downloadLabel={t.hero.downloadCv}
              requestLabel={t.hero.requestCv}
              className="btn btn-line"
            />
            <a href="#contact" className="btn btn-line">
              <Send aria-hidden="true" className="size-4" />
              {t.hero.contact}
            </a>
          </m.div>
        </m.div>

        <m.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
        >
          <PortraitOrbit />
        </m.div>
      </div>

      <div className="border-t border-line">
        <ul className="wrap flex flex-wrap items-center gap-x-8 gap-y-1 py-4 text-sm text-muted">
          {t.hero.roles.map((role) => (
            <li key={role}>{role}</li>
          ))}
          <li className="gold-text font-display font-medium lg:ml-auto">{t.common.brand}</li>
        </ul>
      </div>
    </section>
  );
}
