import { profile } from '../../data/profile';
import { useLanguage } from '../../hooks/useLanguage';

/** Shows the real photo once `profile.photo` is set, and the HM monogram until then. */
export function Portrait({ className = '' }: { className?: string }) {
  const { t } = useLanguage();

  if (profile.photo) {
    return (
      <img
        src={profile.photo}
        alt={t.hero.portraitAlt}
        width={640}
        height={640}
        decoding="async"
        className={`size-full object-cover ${className}`}
      />
    );
  }

  return (
    <div
      role="img"
      aria-label={t.hero.monogramAlt}
      className={`grid size-full place-items-center bg-card bg-[radial-gradient(circle_at_50%_30%,color-mix(in_srgb,var(--gold)_22%,transparent),transparent_65%)] ${className}`}
    >
      <span className="gold-text font-display text-[clamp(4rem,9vw,7rem)] leading-none font-semibold">
        HM
      </span>
    </div>
  );
}
