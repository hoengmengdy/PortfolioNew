import { useLanguage } from '../../hooks/useLanguage';
import { formatIndex } from '../../utils/format';
import { Reveal } from './Reveal';

interface SectionHeadingProps {
  id: string;
  index: number;
  eyebrow: string;
  title: string;
  lead?: string;
}

export function SectionHeading({ id, index, eyebrow, title, lead }: SectionHeadingProps) {
  const { language } = useLanguage();

  return (
    <Reveal className="relative mb-12 md:mb-16">
      <p className="eyebrow flex items-center gap-3">
        <span aria-hidden="true">{formatIndex(index, language)}</span>
        <span aria-hidden="true" className="h-px w-14 bg-gradient-to-r from-gold to-transparent" />
        {eyebrow}
      </p>
      <h2 id={id} className="mt-5 max-w-3xl text-4xl font-medium md:text-6xl">
        {title}
      </h2>
      {lead ? <p className="mt-5 max-w-2xl text-lg text-muted">{lead}</p> : null}
      {/* Khmer numerals are the site's signature, in every language. */}
      <span
        aria-hidden="true"
        lang="km"
        data-numeral={formatIndex(index, 'km')}
        className="pointer-events-none absolute -top-4 right-0 hidden font-display text-[9rem] leading-none font-semibold text-gold/10 select-none before:content-[attr(data-numeral)] lg:block"
      />
    </Reveal>
  );
}
