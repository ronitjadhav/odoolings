'use client';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/cn';
import { Check, RotateCcw, X } from 'lucide-react';
import { chapterIdFromUrl, recordQuizAnswer, resetQuiz } from '@/lib/progress';

export interface QuizQuestion {
  q: string;
  code?: string; // optional snippet shown above the options (predict the output)
  options: string[];
  answer: number; // index into options
  why?: string;
}

function Question({
  quizId,
  index,
  q,
  code,
  options,
  answer,
  why,
  onAnswered,
}: QuizQuestion & { quizId: string; index: number; onAnswered: () => void }) {
  const [picked, setPicked] = useState<number | null>(null);
  const correct = picked === answer;

  return (
    <div className="not-prose">
      <p className="font-medium mb-3">{q}</p>
      {code && (
        <pre className="mb-3 overflow-x-auto rounded-lg border bg-fd-secondary/50 p-3 text-sm">
          <code>{code}</code>
        </pre>
      )}
      <div className="flex flex-col gap-2">
        {options.map((opt, i) => (
          <button
            key={i}
            type="button"
            disabled={picked !== null}
            onClick={() => {
              setPicked(i);
              recordQuizAnswer(quizId, index, i === answer);
              onAnswered();
            }}
            className={cn(
              'flex items-center gap-2 rounded-lg border px-4 py-2.5 text-start text-sm transition-all',
              picked === null &&
                'cursor-pointer hover:border-fd-primary hover:bg-fd-accent hover:translate-x-0.5',
              picked !== null && i === answer && 'border-green-500 bg-green-500/10',
              picked === i && i !== answer && 'border-red-500 bg-red-500/10',
              picked !== null && picked !== i && i !== answer && 'opacity-50',
            )}
          >
            {picked !== null && i === answer && <Check className="size-4 shrink-0 text-green-500" />}
            {picked === i && i !== answer && <X className="size-4 shrink-0 text-red-500" />}
            {opt}
          </button>
        ))}
      </div>
      {picked !== null && (
        <p
          role="status"
          aria-live="polite"
          className={cn(
            'mt-3 text-sm animate-in fade-in slide-in-from-bottom-1',
            correct ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
          )}
        >
          {correct ? 'Correct!' : 'Not quite.'}{' '}
          <span className="text-fd-muted-foreground">{why}</span>
        </p>
      )}
    </div>
  );
}

export function Quiz({
  questions,
  title = 'Quick check',
  id,
}: {
  questions: QuizQuestion[];
  title?: string;
  id?: string;
}) {
  const pathname = usePathname();
  // results are stored per quiz; default id is the chapter number in the URL
  const quizId = id ?? chapterIdFromUrl(pathname) ?? pathname;
  const [attempt, setAttempt] = useState(0);
  const [answered, setAnswered] = useState(0);

  function retake() {
    resetQuiz(quizId);
    setAnswered(0);
    setAttempt((value) => value + 1);
  }

  return (
    <div className="my-6 flex flex-col gap-6 rounded-xl border bg-fd-card p-5 shadow-sm">
      <p className="not-prose -mb-2 text-xs font-semibold uppercase tracking-wider text-fd-primary">
        {title}
      </p>
      {questions.map((q, i) => (
        <Question
          key={`${attempt}-${i}`}
          quizId={quizId}
          index={i}
          onAnswered={() => setAnswered((value) => value + 1)}
          {...q}
        />
      ))}
      {answered > 0 && (
        <button
          type="button"
          onClick={retake}
          className="not-prose inline-flex w-fit cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors hover:border-fd-primary hover:bg-fd-accent"
        >
          <RotateCcw className="size-4" aria-hidden="true" />
          Retake quiz
        </button>
      )}
    </div>
  );
}
