import { BookOpen, Code2, GraduationCap } from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';

export function Education() {
  const { t } = useLanguage();
  const { education } = t;

  const entries = [
    {
      icon: GraduationCap,
      title: education.degree,
      subtitle: education.university,
      body: education.degreeBody,
    },
    { icon: BookOpen, title: education.interestsTitle, body: education.interestsBody },
    { icon: Code2, title: education.journeyTitle, body: education.journeyBody },
  ];

  return (
    <section id="education" aria-labelledby="education-title" className="section bg-surface">
      <div className="wrap">
        <SectionHeading
          id="education-title"
          index={4}
          eyebrow={education.eyebrow}
          title={education.title}
        />

        <ol className="relative ml-5 max-w-3xl border-l border-line">
          {entries.map(({ icon: Icon, title, subtitle, body }, index) => (
            <li key={title} className="relative pb-12 pl-10 last:pb-0">
              <span className="absolute top-0 -left-5 grid size-10 place-items-center rounded-full border border-gold bg-surface text-gold-text">
                <Icon aria-hidden="true" className="size-4" strokeWidth={1.5} />
              </span>
              <Reveal delay={index * 0.05}>
                <h3 className="pt-1.5 text-2xl font-medium">{title}</h3>
                {subtitle ? <p className="mt-2 font-medium text-gold-text">{subtitle}</p> : null}
                <p className="mt-3 text-muted">{body}</p>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
