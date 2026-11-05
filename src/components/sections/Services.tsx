import {
  Database,
  Globe,
  Layers,
  LayoutDashboard,
  MonitorSmartphone,
  Plug,
  Server,
  Workflow,
} from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';
import { formatIndex } from '../../utils/format';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';

const icons = [Globe, MonitorSmartphone, Server, Layers, Database, Plug, LayoutDashboard, Workflow];

export function Services() {
  const { t, language } = useLanguage();
  const { services } = t;

  return (
    <section id="services" aria-labelledby="services-title" className="section">
      <div className="wrap">
        <SectionHeading
          id="services-title"
          index={5}
          eyebrow={services.eyebrow}
          title={services.title}
          lead={services.lead}
        />

        <Reveal>
          <ul className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
            {services.items.map(({ title, description }, index) => {
              const Icon = icons[index] ?? Globe;
              return (
                <li
                  key={title}
                  className="group bg-bg p-7 transition-colors duration-300 hover:bg-card"
                >
                  <div className="flex items-start justify-between">
                    <Icon
                      aria-hidden="true"
                      strokeWidth={1.25}
                      className="size-8 text-gold-text transition-transform duration-300 group-hover:-translate-y-1"
                    />
                    <span aria-hidden="true" className="font-display text-xs text-muted">
                      {formatIndex(index + 1, language)}
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium">{title}</h3>
                  <p className="mt-3 text-sm text-muted">{description}</p>
                </li>
              );
            })}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
