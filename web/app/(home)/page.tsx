import Link from 'next/link';
import {
  ArrowRight,
  BookOpenCheck,
  Container,
  Flame,
  GitPullRequest,
  Terminal,
  Wrench,
} from 'lucide-react';
import { Card, CardGrid, type Tone } from '@/components/card';
import { HeroCta } from '@/components/hero-cta';
import { JsonLd } from '@/components/json-ld';
import { OdoolingsWordmark } from '@/components/odoolings-wordmark';
import { chapterIdFromUrl } from '@/lib/chapter-id';
import { authorId, courseId, courseName, isIndexableDocsPage } from '@/lib/seo';
import { appDescription, appName, canonicalUrl } from '@/lib/shared';
import { source } from '@/lib/source';

const TIERS: { icon: typeof Wrench; name: string; parts: string; blurb: string; tone: Tone }[] = [
  {
    icon: Wrench,
    name: 'Foundations',
    parts: 'Parts 0–3 · ch 1–20',
    blurb: 'Environment, ORM, views, security. Build and ship a clean custom module.',
    tone: 'sage',
  },
  {
    icon: BookOpenCheck,
    name: 'Professional',
    parts: 'Parts 4–5 · ch 21–32',
    blurb: 'Extend core apps safely, write tests, build OWL UI, debug anything.',
    tone: 'sky',
  },
  {
    icon: GitPullRequest,
    name: 'Expert / Integrator',
    parts: 'Parts 6–7 · ch 33–40',
    blurb: 'Work the OCA way: contributions, migrations, performance, deployments.',
    tone: 'violet',
  },
];

const FEATURES: { icon: typeof Terminal; title: string; body: string }[] = [
  {
    icon: Terminal,
    title: 'Your code, checked',
    body: 'odoolings, a rustlings-style CLI, inspects your actually running Odoo after every hands-on section and tells you exactly what is missing, with hints.',
  },
  {
    icon: Flame,
    title: 'Practice, not prose',
    body: 'Quizzes with instant feedback, per-chapter completion, streaks. All stored in your browser: no account, no tracking.',
  },
  {
    icon: Container,
    title: 'Real integrator workflow',
    body: 'Docker-first environment, checkpoint diffs after every chapter, and the same conventions used in OCA and professional Odoo teams.',
  },
];

const CHAPTERS = source
  .getPages()
  .filter(isIndexableDocsPage)
  .map((p) => ({ id: chapterIdFromUrl(p.url), url: p.url, title: p.data.title }))
  .filter((c) => c.id !== null)
  .sort((a, b) => a.id!.localeCompare(b.id!)) as { id: string; url: string; title: string }[];

const STRUCTURED_DATA = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Person',
      '@id': authorId,
      name: 'Ronit Jadhav',
      url: 'https://github.com/ronitjadhav',
      sameAs: ['https://github.com/ronitjadhav'],
    },
    {
      '@type': 'WebSite',
      '@id': `${canonicalUrl()}#website`,
      url: canonicalUrl(),
      name: appName,
      alternateName: courseName,
      description: appDescription,
      inLanguage: 'en',
    },
    {
      '@type': 'Course',
      '@id': courseId,
      url: canonicalUrl(),
      name: courseName,
      description: appDescription,
      provider: { '@id': authorId },
      author: { '@id': authorId },
      isAccessibleForFree: true,
      inLanguage: 'en',
      educationalLevel: 'Beginner to advanced',
      learningResourceType: 'Hands-on tutorial',
      audience: {
        '@type': 'EducationalAudience',
        audienceType: 'Python developers learning Odoo development',
      },
      teaches: [
        'Odoo 19 module development',
        'Odoo ORM, models, and fields',
        'Odoo views, security, and business logic',
        'Odoo testing, debugging, and OWL frontend development',
        'OCA conventions and contribution practices',
      ],
      hasPart: CHAPTERS.map(({ id, url, title }) => ({
        '@type': 'LearningResource',
        '@id': `${canonicalUrl(url)}#lesson`,
        url: canonicalUrl(url),
        name: title,
        position: Number(id),
        learningResourceType: 'Lesson',
      })),
    },
  ],
} as const;

export default function HomePage() {
  return (
    <div className="flex flex-1 flex-col gap-3 px-3 pb-3">
      <JsonLd data={STRUCTURED_DATA} />
      {/* hero */}
      <section className="relative isolate overflow-hidden rounded-(--radius-card) bg-(--hero-surface) px-4 py-20 text-center text-(--hero-foreground) md:px-8 md:py-28">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_58%_52%_at_50%_0%,var(--color-fd-primary),transparent_72%)] opacity-35"
        />
        <p className="eyebrow mx-auto w-fit text-(--hero-muted)">
          Free &amp; open source · Odoo 19 Community
        </p>
        <OdoolingsWordmark className="mx-auto mt-16" />
        <p className="mx-auto mt-7 font-mono text-sm tracking-[0.14em] text-(--hero-muted) uppercase">
          Free Odoo 19 development tutorial
        </p>
        <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-(--hero-muted)">
          Learn Odoo development by building LibreFleet, a real Odoo 19 Community app.
          The free, hands-on path takes you from your first Python module to OCA-quality
          contributions, with every step checked against your own running Odoo.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <HeroCta chapters={CHAPTERS} />
          <a
            href="https://github.com/ronitjadhav/odoolings"
            className="rounded-full border border-white/25 px-6 py-3 font-medium transition-colors hover:bg-white/10"
          >
            GitHub
          </a>
        </div>

        {/* odoolings teaser */}
        <div className="mx-auto mt-14 max-w-lg rounded-(--radius-card) border border-white/15 bg-black/30 p-5 text-start font-mono text-sm shadow-(--shadow-card) backdrop-blur-sm">
          <p className="text-(--hero-muted)">$ python odoolings.py check ch09</p>
          <p className="text-green-600 dark:text-green-400">✔ model librefleet.vehicle exists</p>
          <p className="text-green-600 dark:text-green-400">✔ field mileage is Float</p>
          <p className="text-red-600 dark:text-red-400">✘ smart button shows service count</p>
          <p className="pl-4 text-(--hero-muted)">
            hint: a computed Integer + a button of type &quot;object&quot;…
          </p>
        </div>
      </section>

      {/* what makes it different */}
      <section className="rounded-(--radius-card) bg-fd-card px-6 py-16 md:px-12">
        <p className="eyebrow text-fd-muted-foreground">Why this one</p>
        <h2 className="mt-3 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">
          A free Odoo tutorial built for practice, not reading.
        </h2>
        <p className="mt-4 max-w-2xl text-pretty text-fd-muted-foreground">
          Made for Python developers who are new to Odoo, the lessons connect ORM,
          security, views, testing, OWL, and OCA practices through one working project.
        </p>
        <CardGrid cols={3} className="mt-10">
          {FEATURES.map((f) => (
            <Card key={f.title} title={f.title} icon={<f.icon className="size-4" />}>
              {f.body}
            </Card>
          ))}
        </CardGrid>
      </section>

      {/* learning path */}
      <section className="rounded-(--radius-card) bg-fd-card px-6 py-16 md:px-12">
        <p className="eyebrow text-fd-muted-foreground">The path</p>
        <h2 className="mt-3 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">
          One project, three tiers.
        </h2>
        <p className="mt-4 max-w-xl text-fd-muted-foreground">
          40 chapters, one capstone project, and a checkpoint to diff against after every
          single one.
        </p>
        <CardGrid cols={3} className="mt-10">
          {TIERS.map((t, i) => (
            <Card
              key={t.name}
              tone={t.tone}
              eyebrow={`Tier ${i + 1}`}
              title={t.name}
              icon={<t.icon className="size-4" />}
            >
              <span className="mb-2 block text-xs font-medium text-fd-foreground/60">
                {t.parts}
              </span>
              {t.blurb}
            </Card>
          ))}
        </CardGrid>
        <div className="mt-10">
          <Link
            href="/docs/00-orientation/01-what-odoo-is"
            className="group inline-flex items-center gap-2 font-medium text-fd-primary"
          >
            Begin with chapter 1
            <ArrowRight className="size-4 transition-transform duration-300 ease-(--ease-out-soft) group-hover:translate-x-0.5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
