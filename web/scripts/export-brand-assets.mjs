import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outputDir = path.join(webRoot, 'public', 'brand');
const tempDir = mkdtempSync(path.join(tmpdir(), 'odoolings-brand-'));
const chromeProfile = path.join(tempDir, 'chrome-profile');
const chrome = process.env.CHROME_BIN || 'google-chrome';

const fontDir = path.join(webRoot, 'node_modules', 'geist', 'dist', 'fonts', 'geist-pixel');
const fonts = {
  square: pathToFileURL(path.join(fontDir, 'GeistPixel-Square.woff2')).href,
  grid: pathToFileURL(path.join(fontDir, 'GeistPixel-Grid.woff2')).href,
  circle: pathToFileURL(path.join(fontDir, 'GeistPixel-Circle.woff2')).href,
  triangle: pathToFileURL(path.join(fontDir, 'GeistPixel-Triangle.woff2')).href,
  line: pathToFileURL(path.join(fontDir, 'GeistPixel-Line.woff2')).href,
};

const letters = [
  ['O', 'PixelSquare', false],
  ['D', 'PixelGrid', false],
  ['O', 'PixelCircle', false],
  ['O', 'PixelTriangle', false],
  ['L', 'PixelLine', true],
  ['I', 'PixelSquare', true],
  ['N', 'PixelGrid', true],
  ['G', 'PixelCircle', true],
  ['S', 'PixelLine', true],
];

const variants = [
  {
    file: 'odoolings-wordmark-on-paper.png',
    width: 2400,
    height: 720,
    mode: 'paper',
    layout: 'wordmark',
  },
  {
    file: 'odoolings-wordmark-on-ink.png',
    width: 2400,
    height: 720,
    mode: 'ink',
    layout: 'wordmark',
  },
  {
    file: 'odoolings-wordmark-ink-transparent.png',
    width: 2400,
    height: 720,
    mode: 'transparent-ink',
    layout: 'wordmark',
    transparent: true,
  },
  {
    file: 'odoolings-wordmark-paper-transparent.png',
    width: 2400,
    height: 720,
    mode: 'transparent-paper',
    layout: 'wordmark',
    transparent: true,
  },
  {
    file: 'odoolings-social-card-paper.png',
    width: 1200,
    height: 630,
    mode: 'paper',
    layout: 'social',
  },
  {
    file: 'odoolings-social-card-ink.png',
    width: 1200,
    height: 630,
    mode: 'ink',
    layout: 'social',
  },
  {
    file: 'odoolings-avatar-paper.png',
    width: 1024,
    height: 1024,
    mode: 'paper',
    layout: 'avatar',
  },
  {
    file: 'odoolings-avatar-ink.png',
    width: 1024,
    height: 1024,
    mode: 'ink',
    layout: 'avatar',
  },
];

function wordmark(className = '') {
  const glyphs = letters
    .map(
      ([character, family, signal]) =>
        '<span class="' +
        (signal ? 'signal' : '') +
        '" style="font-family:' +
        family +
        '">' +
        character +
        '</span>',
    )
    .join('');

  return '<div class="wordmark ' + className + '" aria-label="Odoolings">' + glyphs + '</div>';
}

function contentFor(layout) {
  if (layout === 'social') {
    return [
      '<main class="social">',
      '<p class="eyebrow">Free &amp; open source · Odoo 19 Community</p>',
      wordmark('wordmark-social'),
      '<footer>',
      '<p>A hands-on path from your first module<br>to OCA-quality contributions.</p>',
      '<span>odoolings.ronit.io</span>',
      '</footer>',
      '</main>',
    ].join('');
  }

  if (layout === 'avatar') {
    return [
      '<main class="avatar">',
      '<div class="monogram" aria-label="Odoolings">',
      '<span style="font-family:PixelSquare">O</span>',
      '<span class="signal" style="font-family:PixelCircle">O</span>',
      '</div>',
      '<p>Odoolings</p>',
      '</main>',
    ].join('');
  }

  return '<main class="wordmark-stage">' + wordmark() + '</main>';
}

function htmlFor(variant) {
  return [
    '<!doctype html>',
    '<html><head><meta charset="utf-8"><style>',
    '@font-face{font-family:PixelSquare;src:url("' + fonts.square + '") format("woff2");font-weight:500}',
    '@font-face{font-family:PixelGrid;src:url("' + fonts.grid + '") format("woff2");font-weight:500}',
    '@font-face{font-family:PixelCircle;src:url("' + fonts.circle + '") format("woff2");font-weight:500}',
    '@font-face{font-family:PixelTriangle;src:url("' + fonts.triangle + '") format("woff2");font-weight:500}',
    '@font-face{font-family:PixelLine;src:url("' + fonts.line + '") format("woff2");font-weight:500}',
    '*{box-sizing:border-box}',
    'html,body{margin:0;width:100%;height:100%;overflow:hidden}',
    'body{--paper:hsl(45 22% 95%);--ink:hsl(30 8% 9%);--violet:hsl(255 55% 52%);--violet-dark:hsl(255 85% 76%);font-family:Arial,sans-serif}',
    'body.paper{background:var(--paper);color:var(--ink);--signal:var(--violet)}',
    'body.ink{background:var(--ink);color:var(--paper);--signal:var(--violet-dark)}',
    'body.transparent-ink{background:transparent;color:var(--ink);--signal:var(--violet)}',
    'body.transparent-paper{background:transparent;color:var(--paper);--signal:var(--violet-dark)}',
    '.signal{color:var(--signal)}',
    '.wordmark-stage{width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:72px 120px}',
    '.wordmark{display:flex;align-items:baseline;justify-content:center;white-space:nowrap;font-size:360px;line-height:.72;font-weight:500;letter-spacing:-.09em;text-transform:uppercase}',
    '.wordmark span{display:inline-block}',
    '.social{height:100%;padding:58px 64px 54px;display:grid;grid-template-rows:auto 1fr auto;position:relative;isolation:isolate}',
    '.social:before{content:"";position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 58% 52% at 50% 0,var(--signal),transparent 72%);opacity:.19}',
    '.eyebrow{margin:0;font-size:15px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;opacity:.62}',
    '.wordmark-social{align-self:center;justify-self:start;font-size:176px}',
    'footer{display:flex;align-items:end;justify-content:space-between;gap:48px}',
    'footer p{margin:0;font-size:28px;line-height:1.25;letter-spacing:-.025em}',
    'footer span{font-size:15px;letter-spacing:.02em;opacity:.6}',
    '.avatar{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:38px}',
    '.monogram{display:flex;align-items:baseline;font-size:430px;line-height:.68;font-weight:500;letter-spacing:-.18em;padding-right:.18em}',
    '.avatar p{margin:0;font-size:28px;font-weight:700;letter-spacing:.18em;text-transform:uppercase}',
    '</style></head>',
    '<body class="' + variant.mode + '">',
    contentFor(variant.layout),
    '</body></html>',
  ].join('');
}

mkdirSync(outputDir, { recursive: true });
mkdirSync(chromeProfile, { recursive: true });

try {
  for (const variant of variants) {
    const htmlPath = path.join(tempDir, variant.file + '.html');
    const outputPath = path.join(outputDir, variant.file);
    writeFileSync(htmlPath, htmlFor(variant));

    const args = [
      '--headless=new',
      '--no-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--hide-scrollbars',
      '--allow-file-access-from-files',
      '--force-device-scale-factor=1',
      '--run-all-compositor-stages-before-draw',
      '--virtual-time-budget=1000',
      '--user-data-dir=' + chromeProfile,
      '--window-size=' + variant.width + ',' + variant.height,
      '--screenshot=' + outputPath,
    ];

    if (variant.transparent) args.push('--default-background-color=00000000');
    args.push(pathToFileURL(htmlPath).href);

    const result = spawnSync(chrome, args, { stdio: 'inherit' });
    if (result.status !== 0) {
      throw new Error('Failed to render ' + variant.file + ' with ' + chrome);
    }
  }
} finally {
  rmSync(tempDir, { recursive: true, force: true });
}

console.log('Exported ' + variants.length + ' brand assets to ' + outputDir);
