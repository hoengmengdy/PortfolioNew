import type { CoverArt, Project } from '../../types';

const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} as const;

/** Abstract drawings with no invented numbers or data, for projects without a usable capture. */
const art: Record<CoverArt, React.JSX.Element> = {
  analytics: (
    <g {...stroke}>
      <path d="M90 300h460M90 240h460M90 180h460M90 120h460" opacity=".2" />
      <path
        d="M90 270c50-10 70-60 120-60s70 40 120 20 70-110 120-120 60 10 100-30"
        strokeWidth="2.5"
      />
      <path
        d="M90 300c60-6 80-30 130-34s80 16 130 0 70-50 120-56 50 0 80-16"
        strokeDasharray="4 8"
        opacity=".6"
      />
      <circle cx="450" cy="110" r="6" fill="currentColor" />
    </g>
  ),
  news: (
    <g {...stroke}>
      <rect x="150" y="70" width="340" height="260" rx="8" />
      <path d="M180 108h280" strokeWidth="5" />
      <path d="M150 130h340" opacity=".4" />
      <rect x="180" y="150" width="130" height="90" rx="4" />
      <path d="M180 262h130M180 282h130M180 302h90" opacity=".6" />
      <path
        d="M335 156h125M335 176h125M335 196h125M335 216h125M335 236h125M335 262h125M335 282h125M335 302h80"
        opacity=".6"
      />
    </g>
  ),
  community: (
    <g {...stroke}>
      <circle cx="320" cy="200" r="42" />
      <circle cx="320" cy="186" r="13" />
      <path d="M296 226c5-14 15-20 24-20s19 6 24 20" />
      <circle cx="170" cy="120" r="26" />
      <circle cx="470" cy="120" r="26" />
      <circle cx="170" cy="280" r="26" />
      <circle cx="470" cy="280" r="26" />
      <path d="M192 134l90 45M448 134l-90 45M192 266l90-45M448 266l-90-45" opacity=".6" />
      <path d="M120 200h26M494 200h26M320 90v30M320 280v30" strokeDasharray="2 8" opacity=".6" />
    </g>
  ),
};

interface ProjectCoverProps {
  project: Project;
  alt: string;
  sizes: string;
  imageClassName?: string;
  eager?: boolean;
}

export function ProjectCover({
  project,
  alt,
  sizes,
  imageClassName = '',
  eager = false,
}: ProjectCoverProps) {
  const { cover } = project;

  if (cover.kind === 'art') {
    return (
      <svg
        viewBox="0 0 640 400"
        role={alt ? 'img' : undefined}
        aria-label={alt || undefined}
        aria-hidden={alt ? undefined : true}
        className={`aspect-[16/10] w-full bg-surface bg-[radial-gradient(circle_at_50%_40%,color-mix(in_srgb,var(--gold)_14%,transparent),transparent_70%)] text-gold-text ${imageClassName}`}
      >
        {art[cover.art]}
      </svg>
    );
  }

  const base = `/images/projects/${cover.name}`;
  return (
    <img
      src={`${base}-1280.webp`}
      srcSet={`${base}-640.webp 640w, ${base}-1280.webp 1280w`}
      sizes={sizes}
      alt={alt}
      width={1280}
      height={800}
      loading={eager ? 'eager' : 'lazy'}
      decoding="async"
      className={`aspect-[16/10] w-full bg-surface object-cover object-top ${imageClassName}`}
    />
  );
}
