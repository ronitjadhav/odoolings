// node tests/icon-names.mjs
//
// `<Icon name="...">` only works if the name is a real key in components/icon.tsx's
// ICONS map: it's an allow-list, not a dynamic import, so a typo isn't a blank
// space in production, it's a build failure. This catches the typo before the
// build does, with a message that names the file and line.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = 'content/docs';

function walk(dir) {
  return readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith('.mdx') ? [p] : [];
  });
}

const iconSrc = readFileSync('components/icon.tsx', 'utf8');
const registryBody = iconSrc.match(/export const ICONS = \{([\s\S]*?)\} as const;/)?.[1] ?? '';
const KNOWN = new Set([...registryBody.matchAll(/^\s*([a-zA-Z][\w]*):/gm)].map((m) => m[1]));

if (KNOWN.size === 0) {
  console.error('icon-names: could not parse the ICONS registry out of components/icon.tsx');
  process.exit(1);
}

const USAGE = /<Icon\s+name=(['"])([^'"]+)\1/g;
let total = 0;
const offenders = [];

for (const file of walk(ROOT)) {
  const src = readFileSync(file, 'utf8');
  const lines = src.split('\n');
  for (const m of src.matchAll(USAGE)) {
    total++;
    const name = m[2];
    if (!KNOWN.has(name)) {
      const line = src.slice(0, m.index).split('\n').length;
      offenders.push({ file, line, name });
    }
  }
  void lines;
}

console.log(`icon-names: ${total} <Icon> usages, ${KNOWN.size} names in the registry`);
if (offenders.length) {
  console.error(`\n${offenders.length} usage(s) with a name not in components/icon.tsx:\n`);
  for (const o of offenders) {
    console.error(`  ${o.file}:${o.line}  name="${o.name}"`);
  }
  console.error(`\nKnown names: ${[...KNOWN].sort().join(', ')}`);
  process.exit(1);
}
console.log('all icon names resolve.');
