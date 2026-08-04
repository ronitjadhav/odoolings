'use client';
import { useSyncExternalStore } from 'react';
import { chapterIdFromUrl } from './chapter-id';

// All learner state lives in localStorage: no accounts, no backend.
const KEY = 'z2oe-progress';

export interface Progress {
  done: Record<string, string>; // chapter id ("09") -> ISO date completed
  days: string[]; // ISO dates with activity, for the streak
  // quiz id ("15", "15-predict", "p2-review") -> latest outcome per question
  quiz: Record<string, (0 | 1)[]>;
}

const EMPTY: Progress = { done: {}, days: [], quiz: {} };
let cache: Progress | null = null;
const listeners = new Set<() => void>();

export { chapterIdFromUrl };

function load(): Progress {
  if (cache) return cache;
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}') as Partial<Progress>;
    const quiz =
      raw.quiz && typeof raw.quiz === 'object' && !Array.isArray(raw.quiz)
        ? Object.fromEntries(
            Object.entries(raw.quiz).filter((entry) => Array.isArray(entry[1])),
          )
        : {};
    cache = {
      done:
        raw.done && typeof raw.done === 'object' && !Array.isArray(raw.done) ? raw.done : {},
      days: Array.isArray(raw.days)
        ? raw.days.filter((day): day is string => typeof day === 'string')
        : [],
      quiz,
    };
  } catch {
    cache = EMPTY;
  }
  return cache!;
}

function save(next: Progress) {
  cache = next;
  localStorage.setItem(KEY, JSON.stringify(next));
  listeners.forEach((fn) => fn());
}

export function today(now = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function recordVisit() {
  const s = load();
  if (!s.days.includes(today())) {
    save({ ...s, days: [...s.days, today()].slice(-366) });
  }
}

export function toggleDone(chapter: string) {
  const s = load();
  const done = { ...s.done };
  if (done[chapter]) delete done[chapter];
  else done[chapter] = today();
  save({ ...s, done });
}

export function recordQuizAnswer(quizId: string, question: number, correct: boolean) {
  const s = load();
  const answers = [...(s.quiz[quizId] ?? [])];
  answers[question] = correct ? 1 : 0;
  save({ ...s, quiz: { ...s.quiz, [quizId]: answers } });
}

export function resetQuiz(quizId: string) {
  const s = load();
  const quiz = { ...s.quiz };
  delete quiz[quizId];
  save({ ...s, quiz });
}

// mastery over every quiz whose id starts with one of the given prefixes
export function mastery(quiz: Progress['quiz'], prefixes: string[]) {
  let right = 0;
  let total = 0;
  for (const [id, answers] of Object.entries(quiz)) {
    if (!prefixes.some((p) => id.startsWith(p))) continue;
    for (const a of answers) {
      // sparse slots round-trip through JSON as null; count only real answers
      if (a === 0 || a === 1) {
        total++;
        right += a;
      }
    }
  }
  return { right, total };
}

export function streak(days: string[], from = today()): number {
  let n = 0;
  const d = new Date(from + 'T12:00:00Z');
  while (days.includes(d.toISOString().slice(0, 10))) {
    n++;
    d.setUTCDate(d.getUTCDate() - 1);
  }
  return n;
}

export function useProgress(): Progress | null {
  // null on the server / first paint, so SSG markup never mismatches
  return useSyncExternalStore(
    (fn) => {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    () => load(),
    () => null,
  );
}
