import type { Plugin } from 'vite';
import { projectSlugs } from '../src/data/slugs.ts';

/**
 * Crawlers need absolute URLs, and the production domain is only known at build
 * time, so URL-bearing tags, sitemap.xml and robots.txt are generated here.
 * Without a site URL they are left out rather than pointing at a guessed domain.
 */
export function seo(siteUrl: string): Plugin {
  return {
    name: 'portfolio-seo',
    transformIndexHtml(html) {
      const tags = siteUrl
        ? [
            `<link rel="canonical" href="${siteUrl}/" />`,
            `<meta property="og:url" content="${siteUrl}/" />`,
            `<meta property="og:image" content="${siteUrl}/images/og.png" />`,
            `<meta name="twitter:image" content="${siteUrl}/images/og.png" />`,
          ].join('\n    ')
        : '';
      return html
        .replace('<!-- seo:url-tags -->', tags)
        .replace('"url": "__SITE_URL__",', siteUrl ? `"url": "${siteUrl}/",` : '');
    },
    generateBundle() {
      if (!siteUrl) {
        this.warn('No site URL set: skipping sitemap.xml and absolute SEO URLs. See .env.example.');
        this.emitFile({
          type: 'asset',
          fileName: 'robots.txt',
          source: 'User-agent: *\nAllow: /\n',
        });
        return;
      }

      const paths = ['/', ...projectSlugs.map((slug) => `/projects/${slug}`)];
      const urls = paths.map((path) => `  <url><loc>${siteUrl}${path}</loc></url>`).join('\n');
      this.emitFile({
        type: 'asset',
        fileName: 'sitemap.xml',
        source: `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
      });
      this.emitFile({
        type: 'asset',
        fileName: 'robots.txt',
        source: `User-agent: *\nAllow: /\n\nSitemap: ${siteUrl}/sitemap.xml\n`,
      });
    },
  };
}
