'use client';
import { mastery, useProgress } from '@/lib/progress';

// Shows how much of a part's quiz material the reader has answered correctly.
// `keys` are quiz-id prefixes: chapter numbers plus any review quiz ids.
export function Mastery({ label, keys }: { label: string; keys: string[] }) {
  const progress = useProgress();
  if (!progress) return null;

  const { right, total } = mastery(progress.quiz, keys);
  const pct = total ? Math.round((right / total) * 100) : 0;

  return (
    <div className="not-prose my-6 rounded-xl border bg-fd-card p-5">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-fd-primary">
          {label} mastery
        </span>
        <span className="text-sm text-fd-muted-foreground">
          {total === 0 ? 'no quizzes answered yet' : `${right}/${total} correct · ${pct}%`}
        </span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full bg-fd-muted"
        role="progressbar"
        aria-label={`${label} mastery`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-valuetext={total === 0 ? 'No quizzes answered yet' : `${right} of ${total} correct`}
      >
        <div
          className="h-full rounded-full bg-fd-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      {total > 0 && pct < 70 && (
        <p className="mt-2 text-xs text-fd-muted-foreground">
          Under 70%? Revisit the chapters whose questions tripped you up, then retake
          their quizzes: results here always reflect your latest attempt.
        </p>
      )}
    </div>
  );
}
