import { Braces, SquareCode } from 'lucide-react';
import {
  siDocker,
  siExpress,
  siFirebase,
  siFlask,
  siGit,
  siGithub,
  siGooglecloud,
  siHtml5,
  siBootstrap,
  siCss,
  siJavascript,
  siLaravel,
  siMeta,
  siMysql,
  siNodedotjs,
  siPhp,
  siPostgresql,
  siPostman,
  siPython,
  siReact,
  siRender,
  siSqlite,
  siTailwindcss,
  siTelegram,
  siTypescript,
  siVercel,
  siVuedotjs,
} from 'simple-icons';

const brandPaths: Record<string, string> = {
  HTML5: siHtml5.path,
  CSS3: siCss.path,
  JavaScript: siJavascript.path,
  Bootstrap: siBootstrap.path,
  React: siReact.path,
  'React.js': siReact.path,
  'Vue.js': siVuedotjs.path,
  TypeScript: siTypescript.path,
  'Tailwind CSS': siTailwindcss.path,
  Python: siPython.path,
  Flask: siFlask.path,
  PHP: siPhp.path,
  Laravel: siLaravel.path,
  'Node.js': siNodedotjs.path,
  Express: siExpress.path,
  MySQL: siMysql.path,
  PostgreSQL: siPostgresql.path,
  SQLite: siSqlite.path,
  Firebase: siFirebase.path,
  'Cloud Firestore': siFirebase.path,
  Git: siGit.path,
  GitHub: siGithub.path,
  Postman: siPostman.path,
  Docker: siDocker.path,
  Vercel: siVercel.path,
  Render: siRender.path,
  'Telegram Bot API': siTelegram.path,
  'Meta Graph API': siMeta.path,
  'Google Cloud TTS': siGooglecloud.path,
};

interface TechIconProps {
  name: string;
  className?: string;
}

/** Decorative: the technology's name is always rendered as text next to it. */
export function TechIcon({ name, className = 'size-5' }: TechIconProps) {
  const path = brandPaths[name];

  if (path) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={className}>
        <path d={path} />
      </svg>
    );
  }

  const Fallback = name === 'VS Code' ? SquareCode : Braces;
  return <Fallback aria-hidden="true" className={className} strokeWidth={1.5} />;
}
