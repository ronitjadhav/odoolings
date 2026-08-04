import fs from 'node:fs';
import path from 'node:path';
import Link from 'next/link';

// Server component: definitions come straight from the glossary page at build
// time, so tooltips can never drift from it.
// ponytail: links point at the glossary page top; per-term anchors would need
// the glossary to use headings. Upgrade if readers ask.

function loadGlossary(): Map<string, string> {
  const src = fs.readFileSync(
    path.join(process.cwd(), 'content/docs/glossary.mdx'),
    'utf8',
  );
  const map = new Map<string, string>();
  for (const block of src.split('\n\n')) {
    const m = block.trim().match(/^\*\*(.+?)\*\*: ([\s\S]+)$/);
    if (!m) continue;
    const definition = m[2]
      .replace(/\s+/g, ' ')
      .replace(/`([^`]*)`/g, '$1')
      .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/\*\*?([^*]*)\*\*?/g, '$1');
    map.set(m[1], definition.length > 240 ? definition.slice(0, 237) + '...' : definition);
  }
  return map;
}

const GLOSSARY = loadGlossary();

export function Term({ k, children }: { k: string; children: React.ReactNode }) {
  const definition = GLOSSARY.get(k);
  // pages are SSG, so a typo'd key fails `npm run build` instead of shipping
  if (!definition) throw new Error(`<Term k="${k}">: no such glossary entry`);
  return (
    <Link href="/docs/glossary" className="odoolings-term" data-tip={definition}>
      {children}
      <span className="sr-only">. Definition: {definition}</span>
    </Link>
  );
}
