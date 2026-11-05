import { Mail } from 'lucide-react';
import { siFacebook, siGithub, siTelegram } from 'simple-icons';
import type { SocialLink } from '../../types';

const paths = { github: siGithub.path, telegram: siTelegram.path, facebook: siFacebook.path };

export function SocialIcon({
  id,
  className = 'size-5',
}: {
  id: SocialLink['id'];
  className?: string;
}) {
  if (id === 'email') return <Mail aria-hidden="true" className={className} strokeWidth={1.5} />;

  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={className}>
      <path d={paths[id]} />
    </svg>
  );
}
