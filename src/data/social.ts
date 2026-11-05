import type { SocialLink } from '../types';

/** Set these once confirmed. Links left as `null` are simply not shown. */
const facebookUrl: string | null = null;
const email: string | null = null;

const links: Array<SocialLink | null> = [
  { id: 'github', label: 'GitHub', href: 'https://github.com/hoengmengdy' },
  { id: 'telegram', label: 'Telegram', href: 'https://t.me/mengdyy' },
  facebookUrl ? { id: 'facebook', label: 'Facebook', href: facebookUrl } : null,
  email ? { id: 'email', label: email, href: `mailto:${email}` } : null,
];

export const socialLinks = links.filter((link): link is SocialLink => link !== null);
