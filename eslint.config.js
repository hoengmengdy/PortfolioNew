import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'public'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: { globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  {
    // Build scripts run in Node, not the browser.
    files: ['cv/**/*.mjs'],
    languageOptions: { globals: globals.node },
  },
  {
    // Providers live beside their hooks, so these files export both.
    files: ['src/hooks/**/*.tsx'],
    rules: { 'react-refresh/only-export-components': 'off' },
  },
);
