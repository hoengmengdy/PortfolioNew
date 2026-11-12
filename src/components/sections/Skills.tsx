import { useState } from 'react';
import { skillCategories } from '../../data/skills';
import { useLanguage } from '../../hooks/useLanguage';
import type { SkillCategoryId } from '../../types';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';
import { toKhmerDigits } from '../../utils/format';
import { TechIcon } from '../ui/TechIcon';

type SkillFilter = SkillCategoryId | 'all';

export function Skills() {
  const { t, language } = useLanguage();
  const { skills } = t;
  const [filter, setFilter] = useState<SkillFilter>('all');

  const visible = skillCategories.filter(({ id }) => filter === 'all' || id === filter);

  return (
    <section id="skills" aria-labelledby="skills-title" className="section bg-surface">
      <div className="wrap">
        <SectionHeading
          id="skills-title"
          index={2}
          eyebrow={skills.eyebrow}
          title={skills.title}
          lead={skills.lead}
        />

        <div role="group" aria-label={skills.filterLabel} className="mb-8 flex flex-wrap gap-2">
          <button
            type="button"
            className="filter-btn"
            aria-pressed={filter === 'all'}
            onClick={() => setFilter('all')}
          >
            {skills.all}
          </button>
          {skillCategories.map(({ id }) => (
            <button
              key={id}
              type="button"
              className="filter-btn"
              aria-pressed={filter === id}
              onClick={() => setFilter(id)}
            >
              {skills.categories[id]}
            </button>
          ))}
        </div>

        <div className={`grid gap-5 ${visible.length > 1 ? 'md:grid-cols-2' : ''}`}>
          {visible.map(({ id, skills: items }, index) => (
            <Reveal key={id} delay={index * 0.05} className="panel p-6 md:p-8">
              <div className="flex items-center justify-between gap-4">
                <h3 className="font-display text-2xl font-medium">{skills.categories[id]}</h3>
                <span
                  aria-hidden="true"
                  className="grid size-9 shrink-0 place-items-center rounded-full border border-line font-display text-sm text-gold-text"
                >
                  {language === 'km' ? toKhmerDigits(String(items.length)) : items.length}
                </span>
              </div>
              <span
                aria-hidden="true"
                className="mt-4 block h-px bg-gradient-to-r from-gold/50 to-transparent"
              />
              {/* Pills wrap to their own width, so short and long lists both fill the card evenly. */}
              <ul className="mt-5 flex flex-wrap gap-2.5">
                {items.map((skill) => (
                  <li
                    key={skill}
                    className="group inline-flex items-center gap-2 rounded-full border border-line bg-bg/40 px-4 py-2 transition-all duration-200 hover:-translate-y-0.5 hover:border-gold hover:bg-gold/10 hover:shadow-[0_8px_24px_-12px_rgba(212,175,55,0.6)]"
                  >
                    <TechIcon
                      name={skill}
                      className="size-4 shrink-0 text-gold-text transition-transform duration-200 group-hover:scale-110"
                    />
                    <span className="text-sm whitespace-nowrap">{skill}</span>
                  </li>
                ))}
              </ul>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
