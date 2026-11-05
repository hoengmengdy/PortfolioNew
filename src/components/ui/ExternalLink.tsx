import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { useLanguage } from '../../hooks/useLanguage';

interface ExternalLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  children: ReactNode;
}

export function ExternalLink({ href, children, ...props }: ExternalLinkProps) {
  const { t } = useLanguage();

  return (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
      <span className="sr-only"> ({t.common.externalLink})</span>
    </a>
  );
}
