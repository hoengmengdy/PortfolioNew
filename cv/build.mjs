// Renders cv/cv.html to public/hoeng-meng-dy-cv.pdf with a local Chrome or Edge.
// Usage: node cv/build.mjs
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = pathToFileURL(join(here, 'cv.html')).href;
const output = resolve(here, '..', 'public', 'hoeng-meng-dy-cv.pdf');

const candidates = [
  process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].filter(Boolean);

const browser = candidates.find((path) => existsSync(path));
if (!browser) throw new Error('No Chrome or Edge found. Set CHROME_PATH to its executable.');

const profile = mkdtempSync(join(tmpdir(), 'cv-chrome-'));
try {
  execFileSync(browser, [
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    '--virtual-time-budget=8000',
    `--user-data-dir=${profile}`,
    `--print-to-pdf=${output}`,
    source,
  ]);
  console.log(`CV written to ${output}`);
} finally {
  rmSync(profile, { recursive: true, force: true });
}
