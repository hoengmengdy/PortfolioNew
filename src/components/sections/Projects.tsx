import { useState } from 'react';
import { projectFilters, projects } from '../../data/projects';
import { useLanguage } from '../../hooks/useLanguage';
import type { ProjectFilter } from '../../types';
import { ProjectCard } from '../projects/ProjectCard';
import { SectionHeading } from '../ui/SectionHeading';

export function Projects() {
  const { t } = useLanguage();
  const copy = t.projects;
  const [filter, setFilter] = useState<ProjectFilter | 'all'>('all');

  const visible = projects.filter(({ filters }) => filter === 'all' || filters.includes(filter));

  return (
    <section id="projects" aria-labelledby="projects-title" className="section">
      <div className="wrap">
        <SectionHeading
          id="projects-title"
          index={3}
          eyebrow={copy.eyebrow}
          title={copy.title}
          lead={copy.lead}
        />

        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div role="group" aria-label={copy.filterLabel} className="flex flex-wrap gap-2">
            <button
              type="button"
              className="filter-btn"
              aria-pressed={filter === 'all'}
              onClick={() => setFilter('all')}
            >
              {copy.all}
            </button>
            {projectFilters.map((id) => (
              <button
                key={id}
                type="button"
                className="filter-btn"
                aria-pressed={filter === id}
                onClick={() => setFilter(id)}
              >
                {copy.filters[id]}
              </button>
            ))}
          </div>
          <p aria-live="polite" className="text-sm text-muted">
            {copy.resultCount(visible.length)}
          </p>
        </div>

        <ul className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {visible.map((project) => (
            <li key={project.slug} className="flex">
              <ProjectCard project={project} number={projects.indexOf(project) + 1} />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
