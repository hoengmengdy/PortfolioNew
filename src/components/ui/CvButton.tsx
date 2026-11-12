import { Download, FileText } from 'lucide-react';
import { profile } from '../../data/profile';

interface CvButtonProps {
  downloadLabel: string;
  requestLabel: string;
  className?: string;
  onClick?: () => void;
}

/** Downloads the real CV once one is configured. Until then it leads to the contact section. */
export function CvButton({ downloadLabel, requestLabel, className, onClick }: CvButtonProps) {
  if (profile.cvUrl) {
    return (
      <a
        href={profile.cvUrl}
        download="Hoeng-Meng-Dy-CV.pdf"
        className={className}
        onClick={onClick}
      >
        <Download aria-hidden="true" className="size-4" />
        {downloadLabel}
      </a>
    );
  }

  return (
    <a href="#contact" className={className} onClick={onClick}>
      <FileText aria-hidden="true" className="size-4" />
      {requestLabel}
    </a>
  );
}
