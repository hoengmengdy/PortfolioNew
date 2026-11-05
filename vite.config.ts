import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
import { seo } from './vite-plugins/seo.ts';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const hostedUrl = env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${env.VERCEL_PROJECT_PRODUCTION_URL}`
    : env.URL;
  const siteUrl = (env.VITE_SITE_URL || hostedUrl || '').replace(/\/+$/, '');

  return {
    plugins: [react(), tailwindcss(), seo(siteUrl)],
    define: { __SITE_URL__: JSON.stringify(siteUrl) },
    build: { target: 'es2022' },
  };
});
