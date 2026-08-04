// Run with npm run test:progress; the wrapper compiles the client module first.
// Pure-logic checks for lib/progress.ts, including its chapter-id re-export.
// CommonJS output resolves the extensionless "./chapter-id" import the way
// Node's require() does; esnext output does not, and Node's ESM loader then
// fails to find it (Next/Turbopack resolves that same bare specifier fine,
// so the app build isn't affected, only this standalone test compile).
import assert from 'node:assert/strict';

const store = {};
globalThis.localStorage = {
  getItem: (k) => store[k] ?? null,
  setItem: (k, v) => {
    store[k] = v;
  },
};

const { chapterIdFromUrl, mastery, recordQuizAnswer, resetQuiz, today } = await import(
  './.build/progress.js'
);

// --- chapterIdFromUrl -------------------------------------------------------
// a real chapter: parent folder and page both look like NN-slug
assert.equal(chapterIdFromUrl('/docs/02-first-module/09-models-fields'), '09');
assert.equal(chapterIdFromUrl('/docs/02-first-module/09-models-fields/'), '09');
assert.equal(chapterIdFromUrl('/docs/00-orientation/01-what-odoo-is'), '01');

// basePath in front must not matter
assert.equal(
  chapterIdFromUrl('/odoolings/docs/02-first-module/15-recordsets-deep-dive'),
  '15',
);

// the regression this helper exists for: a part's own index page is NOT
// chapter "02" (which belongs to Part 0). Getting this wrong made "mark
// complete" on the Part 2 Review page tick chapter 2 in a different part.
assert.equal(chapterIdFromUrl('/docs/02-first-module'), null);
assert.equal(chapterIdFromUrl('/docs/02-first-module/'), null);

// non-chapter pages inside a part
assert.equal(chapterIdFromUrl('/docs/02-first-module/boss2-garage-inventory'), null);
assert.equal(chapterIdFromUrl('/docs/glossary'), null);
assert.equal(chapterIdFromUrl('/docs'), null);
assert.equal(chapterIdFromUrl('/'), null);

// The wrapper sets Europe/Berlin so this instant is just after local midnight.
assert.equal(today(new Date('2026-08-03T22:30:00.000Z')), '2026-08-04');

// --- quiz persistence -------------------------------------------------------
recordQuizAnswer('15', 0, true);
recordQuizAnswer('15', 2, false); // question 1 skipped -> sparse slot
recordQuizAnswer('15-predict', 0, true);
recordQuizAnswer('p2-review', 0, false);
recordQuizAnswer('p2-review', 0, true); // retake overwrites in place

const saved = JSON.parse(store['z2oe-progress']);
assert.deepEqual(saved.quiz['15'], [1, null, 0]);

// '15' prefix also catches '15-predict'; sparse slots are not counted
assert.deepEqual(mastery(saved.quiz, ['15', 'p2-review']), { right: 3, total: 4 });
assert.deepEqual(mastery(saved.quiz, ['08']), { right: 0, total: 0 });
resetQuiz('p2-review');
const afterReset = JSON.parse(store['z2oe-progress']);
assert.equal(afterReset.quiz['p2-review'], undefined);


console.log('progress.test.mjs: all assertions passed');
