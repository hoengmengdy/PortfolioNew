import { ArrowUp } from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';
import { useScrolledPast } from '../../hooks/useScrolledPast';

export function BackToTop() {
  const { t } = useLanguage();
  const visible = useScrolledPast(700);

  return (
    <a
      href="#home"
      aria-label={t.nav.backToTop}
      tabIndex={visible ? undefined : -1}
      aria-hidden={visible ? undefined : true}
      className={`fixed right-5 bottom-5 z-30 grid size-11 place-items-center rounded-full border border-line bg-card text-gold-text shadow-lg transition-all duration-300 hover:-translate-y-1 hover:border-gold ${
        visible ? 'opacity-100' : 'pointer-events-none translate-y-3 opacity-0'
      }`}
    >
      <ArrowUp aria-hidden="true" className="size-5" />
    </a>
  );
}
