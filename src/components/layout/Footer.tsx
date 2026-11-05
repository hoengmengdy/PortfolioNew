import { ArrowUp } from 'lucide-react';
import { socialLinks } from '../../data/social';
import { useLanguage } from '../../hooks/useLanguage';
import { BackToTop } from './BackToTop';
import { navItems } from '../navigation/navItems';
import { ExternalLink } from '../ui/ExternalLink';
import { LogoMark } from '../ui/Logo';
import { SocialIcon } from '../ui/SocialIcon';

export function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-line bg-surface">
      <div className="wrap grid gap-12 py-16 md:grid-cols-[2fr_1fr_1fr]">
        <div>
          <LogoMark className="size-12" />
          <p className="mt-6 font-display text-2xl font-medium">{t.common.name}</p>
          <p className="mt-3 max-w-md text-muted">{t.footer.intro}</p>
          <p className="gold-text mt-4 font-display text-sm font-medium">{t.common.brand}</p>
        </div>

        <nav aria-label={t.footer.navigate}>
          <h2 className="eyebrow">{t.footer.navigate}</h2>
          <ul className="mt-5 space-y-2">
            {navItems.map((item) => (
              <li key={item}>
                <a href={`#${item}`} className="text-muted transition-colors hover:text-gold-text">
                  {t.nav[item]}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h2 className="eyebrow">{t.footer.connect}</h2>
          <ul className="mt-5 space-y-3">
            {socialLinks.map((link) => (
              <li key={link.id}>
                <ExternalLink
                  href={link.href}
                  className="inline-flex items-center gap-3 text-muted transition-colors hover:text-gold-text"
                >
                  <SocialIcon id={link.id} className="size-4" />
                  {link.label}
                </ExternalLink>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t border-line">
        <div className="wrap flex flex-col gap-4 py-6 text-sm text-muted md:flex-row md:items-center md:justify-between">
          <p>
            © 2026 {t.footer.rights} {t.footer.builtWith}
          </p>
          <a
            href="#home"
            className="inline-flex items-center gap-2 transition-colors hover:text-gold-text"
          >
            {t.nav.backToTop}
            <ArrowUp aria-hidden="true" className="size-4" />
          </a>
        </div>
      </div>
      <BackToTop />
    </footer>
  );
}
