import type { SkillCategory } from '../types';

/** No proficiency levels here on purpose: none have been provided, so none are invented. */
export const skillCategories: SkillCategory[] = [
  {
    id: 'frontend',
    skills: ['HTML5', 'CSS3', 'JavaScript', 'React.js', 'TypeScript', 'Tailwind CSS'],
  },
  {
    id: 'backend',
    skills: ['Python', 'Flask', 'PHP', 'Laravel', 'Node.js', 'REST API'],
  },
  {
    id: 'database',
    skills: ['MySQL', 'PostgreSQL', 'Firebase', 'Cloud Firestore'],
  },
  {
    id: 'tools',
    skills: ['Git', 'GitHub', 'VS Code', 'Postman', 'Docker', 'Vercel', 'Render'],
  },
];
