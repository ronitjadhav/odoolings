// node tests/cross-refs.mjs
//
// Two things that rot silently and can be checked mechanically.
//
// 1. "chapter 47" must name a chapter that exists. The D13 renumber moved every
//    chapter number at once; the prose references were fixed by hand, which is
//    exactly the kind of pass that misses one. (Part references, "Part 8", are NOT
//    checkable this way: every number 0-9 is a real part, so a wrong one still
//    resolves. That is the reason the authoring skill says to prefer chapter
//    numbers over part numbers in prose.)
// 2. <Mermaid> must carry a `label`. It becomes the diagram's aria-label, and the
//    component defaults it to the useless string "Diagram", so a missing one is
//    invisible in review and only shows up to a screen reader.
// 3. The book has to agree about how long it is. TOTAL_CHAPTERS drives the progress
//    pill, and the widest chapter range in prose ("Parts 8-9 · ch 43-55") describes
//    the same extent. Both went stale in the 2026-09-01 insertion and neither was
//    caught: check 1 passes a range whose upper bound is merely *a* chapter, which
//    "ch 43-50" still was after four chapters moved past it.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, basename } from 'node:path';

const ROOT = 'content/docs';

function walk(dir) {
  return readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith('.mdx') ? [p] : [];
  });
}

const files = walk(ROOT);

// Chapter numbers come from the filenames, which are the source of truth for
// numbering (meta.json lists the same slugs).
const CHAPTERS = new Set(
  files.map((f) => basename(f).match(/^(\d+)-/)?.[1]).filter(Boolean).map(Number),
);

if (CHAPTERS.size === 0) {
  console.error('cross-refs: found no numbered chapter files under ' + ROOT);
  process.exit(1);
}

// Code is full of "check ch09" and version strings; only prose is a cross-reference.
const stripCode = (src) =>
  src.replace(/```[\s\S]*?```/g, (m) => m.replace(/[^\n]/g, ' ')).replace(/`[^`\n]*`/g, ' ');

const REF = /\bchapters?\s+(\d+)(?:\s*[–-]\s*(\d+))?/gi;
// "ch 43-55" and "chapters 43-55": a range claiming to describe the book's extent.
const SPAN = /\bch(?:apters?)?\s*(\d+)\s*[–-]\s*(\d+)/gi;
const LAST = Math.max(...CHAPTERS);
const MERMAID = /<Mermaid\b([\s\S]*?)chart=/g;

// Diagrams that predate the label rule (added with the ch1-10 review, 2026-08-09).
// Chapters 1-10 are clean; these are the chapters not yet walked. Delete a line as
// its chapter gets its walkthrough pass, and never add one: a new unlabelled diagram
// is the failure this test exists to catch.
const UNLABELLED_BASELINE = new Set([
  '06-business-logic/31-the-three-inheritance-types.mdx',
  '06-business-logic/32-extending-core-apps.mdx',
  '06-business-logic/33-mail-chatter.mdx',
  '06-business-logic/34-data-files.mdx',
]);

const badRefs = [];
const badDiagrams = [];
const knownUnlabelled = [];
let refCount = 0;
let diagramCount = 0;

for (const file of files) {
  const src = readFileSync(file, 'utf8');
  const prose = stripCode(src);

  for (const m of prose.matchAll(REF)) {
    for (const n of [m[1], m[2]].filter(Boolean).map(Number)) {
      refCount++;
      if (!CHAPTERS.has(n)) {
        badRefs.push({ file, line: prose.slice(0, m.index).split('\n').length, n, text: m[0] });
      }
    }
  }

  const rel = file.slice(ROOT.length + 1);
  for (const m of src.matchAll(MERMAID)) {
    diagramCount++;
    if (!/\blabel=/.test(m[1])) {
      const where = { file, line: src.slice(0, m.index).split('\n').length };
      (UNLABELLED_BASELINE.has(rel) ? knownUnlabelled : badDiagrams).push(where);
    }
  }
}

console.log(
  `cross-refs: ${refCount} chapter references over ${CHAPTERS.size} chapters, ${diagramCount} diagrams`,
);
if (knownUnlabelled.length) {
  console.log(
    `  (${knownUnlabelled.length} unlabelled diagram(s) in ${UNLABELLED_BASELINE.size} chapters not yet walked, see UNLABELLED_BASELINE)`,
  );
}

// 3. The stated extent, from anywhere the site says it, against the files on disk.
const extentErrors = [];
{
  const shared = readFileSync('lib/shared.ts', 'utf8');
  const total = Number(shared.match(/TOTAL_CHAPTERS\s*=\s*(\d+)/)?.[1]);
  if (total !== CHAPTERS.size || total !== LAST) {
    extentErrors.push(
      `lib/shared.ts TOTAL_CHAPTERS is ${total}, but ${CHAPTERS.size} chapter files exist, numbered up to ${LAST}`,
    );
  }
  // Every range anywhere, including the landing page, which is outside content/docs.
  let widest = 0;
  for (const f of [...files, 'app/(home)/page.tsx']) {
    for (const m of stripCode(readFileSync(f, 'utf8')).matchAll(SPAN)) {
      widest = Math.max(widest, Number(m[2]));
    }
  }
  if (widest !== LAST) {
    extentErrors.push(
      `the widest chapter range stated in prose ends at ${widest}, but the last chapter is ${LAST}`,
    );
  }
}

let failed = false;

if (extentErrors.length) {
  failed = true;
  console.error(`\n${extentErrors.length} place(s) where the book disagrees about its own length:\n`);
  for (const e of extentErrors) console.error(`  ${e}`);
  console.error('\n  A renumber has to update TOTAL_CHAPTERS, the landing page tiers,');
  console.error('  docs/index.mdx and roadmap.mdx, none of which check 1 can see.');
}

if (badRefs.length) {
  failed = true;
  console.error(`\n${badRefs.length} reference(s) to a chapter that does not exist:\n`);
  for (const b of badRefs) console.error(`  ${b.file}:${b.line}  "${b.text}"`);
}

if (badDiagrams.length) {
  failed = true;
  console.error(`\n${badDiagrams.length} <Mermaid> without a label (ships as aria-label="Diagram"):\n`);
  for (const b of badDiagrams) console.error(`  ${b.file}:${b.line}`);
}

if (failed) process.exit(1);
console.log('all chapter references resolve, all diagrams are labelled.');
