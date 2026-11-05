import { useLanguage } from '../../hooks/useLanguage';
import type { Language } from '../../types';

const options: Array<{ value: Language; label: string }> = [
  { value: 'km', label: 'KH' },
  { value: 'en', label: 'EN' },
];

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div
      role="group"
      aria-label={t.nav.switchLanguage}
      className="flex items-center rounded-full border border-line p-0.5"
    >
      {options.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          aria-pressed={language === value}
          aria-label={value === 'km' ? 'KH, ភាសាខ្មែរ' : 'EN, English'}
          onClick={() => setLanguage(value)}
          className={`min-h-9 min-w-9 rounded-full px-2 font-display text-xs font-semibold transition-colors ${
            language === value ? 'bg-gold text-on-gold' : 'text-muted hover:text-fg'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
