import { ArrowUpRight, MapPin } from 'lucide-react';
import { socialLinks } from '../../data/social';
import { useLanguage } from '../../hooks/useLanguage';
import { formatIndex } from '../../utils/format';
import { ExternalLink } from '../ui/ExternalLink';
import { Reveal } from '../ui/Reveal';
import { SocialIcon } from '../ui/SocialIcon';

export function Contact() {
  const { t, language } = useLanguage();
  const { contact } = t;

  return (
    <section id="contact" aria-labelledby="contact-title" className="section">
      <div className="wrap grid items-center gap-12 lg:grid-cols-[3fr_2fr] lg:gap-20">
        <Reveal>
          <p className="eyebrow flex items-center gap-3">
            <span aria-hidden="true">{formatIndex(7, language)}</span>
            <span aria-hidden="true" className="h-px w-10 bg-gold" />
            {contact.eyebrow}
          </p>
          <h2 id="contact-title" className="mt-5 text-4xl font-medium md:text-6xl">
            {contact.title}
          </h2>
          <p className="mt-5 max-w-xl text-lg text-muted">{contact.lead}</p>
        </Reveal>

        <Reveal className="panel p-3">
          <ul>
            {socialLinks.map((link) => (
              <li key={link.id}>
                <ExternalLink
                  href={link.href}
                  className="group flex min-h-16 items-center gap-4 rounded-xl px-4 py-3 transition-colors hover:bg-gold/5"
                >
                  <SocialIcon id={link.id} className="size-5 shrink-0 text-gold-text" />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{link.label}</span>
                    <span className="block text-sm [overflow-wrap:anywhere] text-muted">
                      {link.href.replace(/^(https:\/\/|mailto:)/, '')}
                    </span>
                  </span>
                  <ArrowUpRight
                    aria-hidden="true"
                    className="size-4 shrink-0 text-muted transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-gold-text"
                  />
                </ExternalLink>
              </li>
            ))}
            <li className="mt-1 flex min-h-16 items-center gap-4 border-t border-line px-4 py-3 text-muted">
              <MapPin
                aria-hidden="true"
                className="size-5 shrink-0 text-gold-text"
                strokeWidth={1.5}
              />
              {contact.location}
            </li>
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
