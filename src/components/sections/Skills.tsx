import { useState } from 'react';
import { skillCategories } from '../../data/skills';
import { useLanguage } from '../../hooks/useLanguage';
import type { SkillCategoryId } from '../../types';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';
import { TechIcon } from '../ui/TechIcon';

type SkillFilter = SkillCategoryId | 'all';

export function Skills() {
  const { t } = useLanguage();
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
              <h3 className="font-display text-2xl font-medium">{skills.categories[id]}</h3>
              <ul className="mt-6 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
                {items.map((skill) => (
                  <li
                    key={skill}
                    className="group flex min-w-0 items-center gap-2.5 rounded-xl border border-line px-3 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-gold hover:bg-gold/5"
                  >
                    <TechIcon
                      name={skill}
                      className="size-4 shrink-0 text-gold-text transition-transform duration-200 group-hover:scale-110"
                    />
                    <span className="min-w-0 text-sm [overflow-wrap:anywhere]">{skill}</span>
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
