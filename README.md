# Hoeng Mengdy: Developer Portfolio

A bilingual (English and Khmer) personal portfolio with a black and gold identity, built with React, TypeScript, Tailwind CSS, and Framer Motion.

## Quick start

Requires Node.js 22 or newer.

```bash
npm install
npm run dev
```

| Command             | What it does                        |
| ------------------- | ----------------------------------- |
| `npm run dev`       | Starts the development server       |
| `npm run build`     | Type-checks, then builds to `dist/` |
| `npm run preview`   | Serves the production build locally |
| `npm run typecheck` | Runs the TypeScript check only      |
| `npm run lint`      | Runs ESLint                         |
| `npm run format`    | Formats the code with Prettier      |

On Windows PowerShell, use `npm.cmd` if script execution is restricted.

## Before going live

The site is designed to work with these unset, and it never shows made-up values. Each one you fill in switches on the matching feature.

| What to add           | Where                                    | What changes                                    |
| --------------------- | ---------------------------------------- | ----------------------------------------------- |
| Profile photo         | `profile.photo` in `src/data/profile.ts` | Replaces the HM monogram in the hero and About  |
| CV PDF                | `profile.cvUrl` in `src/data/profile.ts` | "Request CV" becomes a real "Download CV"       |
| Open to opportunities | `profile.availableForOpportunities`      | Shows the "Available for opportunities" badge   |
| Email address         | `email` in `src/data/social.ts`          | Adds email to the contact section and footer    |
| Facebook profile      | `facebookUrl` in `src/data/social.ts`    | Adds Facebook to the contact section and footer |
| Production URL        | `VITE_SITE_URL`                          | Adds canonical URLs and generates `sitemap.xml` |

## Editing content

- **All wording** is in `src/locales/en.ts` and `src/locales/km.ts`. TypeScript reports an error if a key is missing from the Khmer file.
- **Project facts** (stack, links, cover, filters) are in `src/data/projects.ts`. The comment at the top of that file explains why some links are currently left out.
- **Skills** are in `src/data/skills.ts`. Proficiency levels are not shown, because none have been provided.

### Adding a project

1. Add a slug to `src/data/slugs.ts`.
2. Add an entry to `src/data/projects.ts`.
3. Add its copy to both locale files. TypeScript will point out what is missing.
4. Optional: add a real screenshot as `public/images/projects/<name>-640.webp` and `<name>-1280.webp`, at a 16:10 ratio.

The site labels each cover as a screenshot or an illustration, so please keep that honest. Only list features you have confirmed in the source code. Anything built but not yet proven against a live third-party service belongs in `unverified`.

## Deployment

The project is ready for either host. Both configurations include the SPA routing fallback and security headers.

### Vercel

1. Push the project to GitHub and import the repository in Vercel. The settings come from `vercel.json`.
2. Set `VITE_SITE_URL` once you have a custom domain. Until then, the build uses Vercel's production URL automatically.

### Netlify

1. Push the project to GitHub and import the repository in Netlify. The settings come from `netlify.toml`.
2. Set `VITE_SITE_URL` once you have a custom domain. Until then, the build uses Netlify's `URL` variable automatically.

### Custom domain

Add the domain in your host's dashboard, set `VITE_SITE_URL=https://your-domain.com` with no trailing slash, and redeploy. Canonical links, Open Graph URLs, `sitemap.xml`, and `robots.txt` all update from that one value.

## Environment variables

See [.env.example](.env.example). **Every `VITE_` value ends up in the public JavaScript bundle, so never put a secret in one.** The site needs no secrets.

## Project structure

```
src/
  components/
    layout/       Footer, scroll progress, back to top
    navigation/   Navbar, language switcher, theme toggle
    sections/     One component per page section
    projects/     Card, cover, and detail modal
    ui/           Shared building blocks
  data/           Language-neutral facts: projects, skills, social links, profile
  hooks/          Language, theme, active section, SEO
  locales/        en.ts and km.ts: all wording
  pages/          Home and 404
  styles/         Design tokens and base styles
  utils/          Formatting and safe storage
vite-plugins/     Build-time SEO: canonical tags, sitemap.xml, robots.txt
```

## Notes on decisions

- **Khmer text:** letter-spacing and uppercase are turned off for Khmer because they break its letter clusters, and line height is increased so stacked subscripts don't clip. Fonts are self-hosted, and Noto Sans Khmer only downloads when Khmer text is on screen.
- **Project details** are a modal with its own URL (`/projects/<slug>`), so each project can be shared and indexed.
- **Modals and the mobile menu** use the native `<dialog>` element, which provides focus trapping and Escape handling.
- **Accessibility linting:** `eslint-plugin-jsx-a11y` is not installed because it does not yet support ESLint 10. Run an [axe](https://www.deque.com/axe/) check after significant UI changes.
- **TypeScript is pinned to 5.9** because `typescript-eslint` does not yet support newer versions.
