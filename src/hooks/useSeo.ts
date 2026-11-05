import { useEffect } from 'react';

interface SeoOptions {
  title: string;
  description: string;
  path: string;
  noindex?: boolean;
}

function setMeta(selector: string, content: string) {
  document.head.querySelector(selector)?.setAttribute('content', content);
}

/** Updates the tags already in index.html, so crawlers and browsers never see duplicates. */
export function useSeo({ title, description, path, noindex = false }: SeoOptions): void {
  useEffect(() => {
    document.title = title;
    setMeta('meta[name="description"]', description);
    setMeta('meta[property="og:title"]', title);
    setMeta('meta[name="twitter:title"]', title);
    setMeta('meta[property="og:description"]', description);
    setMeta('meta[name="twitter:description"]', description);

    if (__SITE_URL__) {
      const url = `${__SITE_URL__}${path}`;
      document.head.querySelector('link[rel="canonical"]')?.setAttribute('href', url);
      setMeta('meta[property="og:url"]', url);
    }

    if (!noindex) return;
    const robots = document.createElement('meta');
    robots.name = 'robots';
    robots.content = 'noindex';
    document.head.appendChild(robots);
    return () => robots.remove();
  }, [title, description, path, noindex]);
}
