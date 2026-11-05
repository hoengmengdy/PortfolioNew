import type { projectSlugs } from '../data/slugs';

export type Language = 'en' | 'km';
export type Theme = 'dark' | 'light';

export type ProjectSlug = (typeof projectSlugs)[number];
export type ProjectFilter = 'react' | 'vue' | 'flask' | 'node' | 'telegram' | 'web';
export type CoverArt = 'analytics' | 'news' | 'community';

export type ProjectCover =
  /** A real capture of the project, served at `/images/projects/<name>-<width>.webp`. */
  | { kind: 'screenshot'; name: string }
  /** A drawn illustration, used and labelled as such when no suitable capture exists. */
  | { kind: 'art'; art: CoverArt };

/** The language-neutral facts about a project. Its wording lives in `src/locales`. */
export interface Project {
  slug: ProjectSlug;
  featured: boolean;
  filters: ProjectFilter[];
  stack: string[];
  cover: ProjectCover;
  /** `null` until a public repository is confirmed. Never guess a URL. */
  repoUrl: string | null;
  /** `null` until a working deployment is confirmed. Never guess a URL. */
  demoUrl: string | null;
}

export interface ProjectCopy {
  title: string;
  category: string;
  summary: string;
  description: string;
  /** Only what was confirmed in the project's source code. */
  features: string[];
  /** Built in code, but not yet proven against the live third-party service. */
  unverified?: string[];
  /** A short caveat a reader should see, such as a data source or a dependency. */
  note?: string;
  coverAlt: string;
}

export type SkillCategoryId = 'frontend' | 'backend' | 'database' | 'tools';

export interface SkillCategory {
  id: SkillCategoryId;
  skills: string[];
}

export interface SocialLink {
  id: 'github' | 'telegram' | 'facebook' | 'email';
  label: string;
  href: string;
}
