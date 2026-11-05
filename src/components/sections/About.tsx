import { GraduationCap, MapPin, Sparkles, Target } from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';
import { Portrait } from '../ui/Portrait';
import { Reveal } from '../ui/Reveal';
import { SectionHeading } from '../ui/SectionHeading';

export function About() {
  const { t } = useLanguage();
  const { about } = t;

  const facts = [
    { icon: GraduationCap, label: about.educationLabel, value: about.educationValue },
    { icon: MapPin, label: about.locationLabel, value: about.locationValue },
    { icon: Target, label: about.goalLabel, value: about.goalValue },
    { icon: Sparkles, label: about.passionLabel, value: about.passionValue },
  ];

  return (
    <section id="about" aria-labelledby="about-title" className="section">
      <div className="wrap">
        <SectionHeading id="about-title" index={1} eyebrow={about.eyebrow} title={about.title} />

        <div className="grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
          <Reveal>
            {/* The arch echoes a temple doorway, framing the portrait like an entrance. */}
            <div className="relative mx-auto aspect-[4/5] max-w-md overflow-hidden rounded-t-full border border-line p-3">
              <div className="size-full overflow-hidden rounded-t-full">
                <Portrait />
              </div>
            </div>
          </Reveal>

          <div>
            <Reveal>
              <p className="text-xl leading-relaxed md:text-2xl md:leading-relaxed [&:lang(km)]:leading-loose">
                {about.bio}
              </p>
            </Reveal>

            <dl className="mt-10 grid gap-4 sm:grid-cols-2">
              {facts.map(({ icon: Icon, label, value }, index) => (
                <Reveal key={label} delay={index * 0.05} className="panel p-6">
                  <Icon aria-hidden="true" className="size-5 text-gold-text" strokeWidth={1.5} />
                  <dt className="eyebrow mt-4">{label}</dt>
                  <dd className="mt-2 text-muted">{value}</dd>
                </Reveal>
              ))}
            </dl>

            <Reveal className="mt-10">
              <h3 className="eyebrow">{about.interestsLabel}</h3>
              <ul className="mt-4 flex flex-wrap gap-2">
                {about.interests.map((interest) => (
                  <li key={interest} className="chip text-sm">
                    {interest}
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
