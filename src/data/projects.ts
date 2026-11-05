import type { Project, ProjectFilter } from '../types';

const github = 'https://github.com/hoengmengdy';

/**
 * Every link below was confirmed from the project's git remote or by opening it.
 *
 * - workday: its Vercel deployment returned HTTP 500 when checked, so no demo link.
 * - facebook-analytics: the deployment connects to real Meta accounts, so no demo link
 *   until a public demo mode is confirmed.
 */
export const projects: Project[] = [
  {
    slug: 'workday',
    featured: true,
    filters: ['react', 'flask', 'telegram'],
    stack: [
      'React',
      'TypeScript',
      'Python',
      'Flask',
      'PostgreSQL',
      'REST API',
      'Tailwind CSS',
      'Docker',
      'Telegram Bot API',
    ],
    cover: { kind: 'screenshot', name: 'workday' },
    repoUrl: `${github}/weekly`,
    demoUrl: null,
  },
  {
    slug: 'lsv-industry',
    featured: true,
    filters: ['flask'],
    stack: ['Python', 'Flask', 'PostgreSQL', 'SQLite', 'HTML5', 'CSS3', 'JavaScript'],
    cover: { kind: 'screenshot', name: 'lsv-industry' },
    repoUrl: `${github}/lsvproduct`,
    demoUrl: 'https://www.lsvindustrykh.com',
  },
  {
    slug: 'facebook-analytics',
    featured: true,
    filters: ['react', 'flask'],
    stack: [
      'React',
      'TypeScript',
      'Python',
      'Flask',
      'Meta Graph API',
      'REST API',
      'PostgreSQL',
      'Tailwind CSS',
    ],
    cover: { kind: 'art', art: 'analytics' },
    repoUrl: `${github}/report-page-`,
    demoUrl: null,
  },
  {
    slug: 'empress',
    featured: true,
    filters: ['flask', 'telegram'],
    stack: [
      'Python',
      'Flask',
      'PostgreSQL',
      'SQLite',
      'JavaScript',
      'ABA PayWay',
      'Telegram Bot API',
    ],
    cover: { kind: 'screenshot', name: 'empress' },
    repoUrl: `${github}/empress`,
    demoUrl: 'https://empresscambodia.vercel.app',
  },
  {
    slug: 'bcommunity',
    featured: false,
    filters: ['vue', 'flask'],
    stack: ['Vue.js', 'Python', 'Flask', 'PostgreSQL', 'REST API', 'Vercel'],
    cover: { kind: 'art', art: 'community' },
    repoUrl: `${github}/bcommuniy`,
    demoUrl: 'https://bcommuniy-main.vercel.app',
  },
  {
    slug: 'smm-digital',
    featured: false,
    filters: ['flask'],
    stack: ['Python', 'Flask', 'HTML5', 'CSS3', 'JavaScript', 'Vercel'],
    cover: { kind: 'screenshot', name: 'smm-digital' },
    repoUrl: `${github}/sellpage`,
    demoUrl: 'https://www.smmdigital.shop',
  },
  {
    slug: 'dy-news',
    featured: false,
    filters: ['flask'],
    stack: ['Python', 'Flask', 'PostgreSQL', 'SQLite', 'HTML5', 'CSS3', 'JavaScript'],
    cover: { kind: 'art', art: 'news' },
    repoUrl: `${github}/dynews`,
    demoUrl: 'https://dynews-1.onrender.com',
  },
  {
    slug: 'khmer-calendar',
    featured: false,
    filters: ['node', 'web'],
    stack: ['HTML5', 'CSS3', 'JavaScript', 'Node.js', 'Express', 'Python', 'Google Cloud TTS'],
    cover: { kind: 'screenshot', name: 'khmer-calendar' },
    repoUrl: null,
    demoUrl: null,
  },
  {
    slug: 'qrpage',
    featured: false,
    filters: ['web'],
    stack: ['HTML5', 'CSS3', 'JavaScript'],
    cover: { kind: 'screenshot', name: 'qrpage' },
    repoUrl: `${github}/qrpage-`,
    demoUrl: 'https://qrpage-ten.vercel.app',
  },
];

export const projectFilters: ProjectFilter[] = ['react', 'vue', 'flask', 'node', 'telegram', 'web'];
