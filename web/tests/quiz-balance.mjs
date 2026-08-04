// node tests/quiz-balance.mjs [--max-gap N]
//
// Guards against the easiest quiz tell there is: if the correct option is
// visibly the longest, a reader scores well without reading the chapter. An
// audit on 2026-08-03 found the key was the longest option in 87 of 99
// questions, so this exists to stop that creeping back in.
//
// Exits non-zero if any question's key exceeds the longest distractor by more
// than --max-gap characters (default 40, the "blatant" threshold).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const MAX_GAP = Number(process.argv[process.argv.indexOf('--max-gap') + 1]) || 40;
const ROOT = 'content/docs';

function walk(dir) {
  return readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith('.mdx') ? [p] : [];
  });
}

// Matches a { q: ..., options: [...], answer: N } object inside a <Quiz>.
const BLOCK = /\{\s*\n\s*q:\s*(['"])(.*?)\1,\s*\n\s*options:\s*\[(.*?)\],\s*\n\s*answer:\s*(\d+)/gs;
const STRING = /(['"])((?:\\.|(?!\1).)*)\1/g;

let total = 0;
const offenders = [];

for (const file of walk(ROOT)) {
  const src = readFileSync(file, 'utf8');
  for (const m of src.matchAll(BLOCK)) {
    const [, , question, optionsRaw, answerRaw] = m;
    const options = [...optionsRaw.matchAll(STRING)].map((o) => o[2]);
    const answer = Number(answerRaw);
    if (options.length < 2 || answer >= options.length) continue;
    total++;
    const lengths = options.map((o) => o.length);
    const runnerUp = Math.max(...lengths.filter((_, i) => i !== answer));
    const gap = lengths[answer] - runnerUp;
    if (gap > MAX_GAP) offenders.push({ file, question, gap });
  }
}

console.log(`quiz-balance: ${total} questions, max allowed gap ${MAX_GAP} chars`);
if (offenders.length) {
  console.error(`\n${offenders.length} question(s) where the key gives itself away:\n`);
  for (const o of offenders.sort((a, b) => b.gap - a.gap)) {
    console.error(`  +${String(o.gap).padStart(3)} chars  ${o.file}\n              ${o.question.slice(0, 92)}`);
  }
  console.error('\nFix by lengthening a distractor or moving mechanism detail into `why`.');
  process.exit(1);
}
console.log('all questions balanced.');
