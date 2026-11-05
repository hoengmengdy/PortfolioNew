/** Production URL resolved at build time, or an empty string when unknown. */
declare const __SITE_URL__: string;

interface ImportMetaEnv {
  readonly VITE_SITE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
