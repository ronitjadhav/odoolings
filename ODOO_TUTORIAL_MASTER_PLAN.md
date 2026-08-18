# Master Plan: "Odoolings" — A Hands-On Odoo Development Tutorial Site

> **Purpose of this document:** A complete, self-contained execution plan for building an
> Odoo development tutorial website. It is written so that (a) the author (a developer
> joining an Odoo team at Camptocamp, new to Odoo) can follow it as their own learning
> path, and (b) an AI agent (e.g. Claude Sonnet/Opus) can pick it up cold and start
> producing the site and content with no additional context.
>
> **Last researched:** July 2026.

---

## 1. Project Overview

### 1.1 What we are building
A free, open-source, hands-on tutorial website — working title **"Odoolings"** —
published on **GitHub Pages**, teaching Odoo development from absolute basics to
professional/OCA-level expertise. The site is paired with a **companion code repository**
containing every module built in the tutorial, one folder per chapter, so readers can
diff their work against a known-good state at any point.

### 1.2 Why (dual goal)
1. **Primary:** The author learns Odoo development deeply. Writing a tutorial forces
   understanding (the Feynman technique) — you cannot explain `_inherit` vs `_inherits`
   vs `_name` until you truly get it.
2. **Secondary:** The result becomes a public resource others can use, and a visible
   portfolio artifact (useful inside Camptocamp too — the company is one of the largest
   OCA contributors, so OCA-style quality will be noticed).

### 1.3 Target audience of the tutorial
- Developers with intermediate Python, basic SQL/HTML/JS, and Git experience,
  but **zero Odoo knowledge** (i.e., the author on day 1).
- Secondary audience: junior devs onboarding at Odoo integrator companies.

### 1.4 What this tutorial is NOT
- Not a copy/rewrite of the official docs — it **links to** official docs and OCA
  resources and adds the connective tissue: sequencing, explanations of *why*,
  real-world integrator practices, pitfalls, and exercises.
- Not a functional/end-user Odoo course (no "how to configure CRM stages" content
  except where needed to understand the code behind it).
- **Copyright rule for all content authors (human or AI): never copy text, images, or
  code verbatim from the Odoo documentation, Odoo source (LGPL — code snippets you
  write while following patterns are fine, wholesale copying is not), books, or blog
  posts. All prose must be original. Link out generously instead.**

---

## 2. Key Decisions (already made — do not re-litigate, but flag if outdated)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Odoo version to teach | ~~Odoo 18.0~~ → **Odoo 19.0 Community** as the baseline, with "On Odoo 18 this differs" callout boxes (revised 2026-07-10, see changelog) | Author's call after reviewing the 18→19 delta: core framework (modules, ORM, views, security, OWL) unchanged; 19 is supported until Oct 2028 vs Oct 2027 for 18, giving the content a longer shelf life. Teaching 19 idioms (`t-out`, `display_name`, `_read_group`) from day one means readers never learn deprecated forms — and those exact deprecations become ch37's 18→19 migration exercise. Version-bump pass after each October release stays planned. |
| D2 | Edition | **Community (open source)** | Enterprise source is not freely redistributable; Community is what OCA targets; everything learned transfers. Mention Enterprise-only features in info boxes. |
| D3 | Site generator | ~~MkDocs + Material~~ → **Next.js + Fumadocs + Tailwind (shadcn aesthetic)**, static-exported (revised 2026-07-10, see changelog) | The author wants an interactive, product-feel learning platform, not a docs site. Fumadocs provides docs plumbing (search, sidebar, MDX, dark mode) out of the box; custom React components add quizzes, progress/streaks, and the landing page. Static export keeps GitHub Pages hosting free. |
| D4 | Hosting | **GitHub Pages** via GitHub Actions on push to `main` | Free, zero-ops, requested by the author. |
| D5 | Repo layout | **Two repos**: `odoo-tutorial` (site) and `odoo-tutorial-code` (chapter-by-chapter module code) — or one monorepo with `/docs` and `/code`; monorepo preferred for simplicity. *Outdated name: the monorepo migrated to `odoolings` on 2026-08-04, see changelog.* | Keeps site deploys clean while letting readers clone runnable code. Start monorepo; split later only if needed. |
| D6 | Dev environment taught | **Docker Compose first** (Odoo + PostgreSQL), with a "native install" appendix | Reproducible on Linux/macOS/Windows; mirrors how integrators (incl. Camptocamp, which is Docker-heavy in its platform tooling) actually run projects. |
| D7 | Pedagogy | One continuous **capstone project** built across all chapters + small isolated exercises per chapter + a solutions folder | Mirrors the official tutorial's proven approach but with an original project (see §5.2) to avoid duplicating the official "Real Estate" module. |
| D8 | Language | English | Widest reach; author's working language. |
| D9 | License | Content: CC BY-SA 4.0; Code: AGPL-3 (matches OCA convention) | OCA modules are AGPL/LGPL; using AGPL for tutorial modules teaches the norm. |
| D11 | Repo split | **Two repos**: `odoo-tutorial` (site, content, checkpoints, odoolings, plan; main only) and `odoo-tutorial-starter` (a GitHub **template**, 5 files, branch per Odoo version). Supersedes D5's "one monorepo" for the starter only (added 2026-08-03, see §4.5) | Measured the split along the right line at last: the starter surface (`docker-compose.yml` + `odoo.conf`) is 778 bytes that changed **3 times in the project's history**, versus 20 commits touching checkpoints/odoolings. So splitting the *starter* out costs ~zero recurring work, while splitting the *reference* out would have cost 2 coordinated PRs per chapter (which is why D5 was right to keep one repo, and why the earlier rejections were answering the wrong question). Buys four reader-facing wins: setup needs no shell at all (kills the WSL/POSIX prerequisite), `addons/.gitkeep` makes the root-owned-bind-mount bug structurally impossible, readers get a clean repo with their own history from commit one, and the starter can carry `19.0`/`20.0` branches, which is the branch-per-version convention ch7 already teaches. |
| D12 | Functional literacy | **Two new parts teaching Odoo's business apps** (Parts 4 and 5, ch 21-30), inserted at the Foundations/Professional tier boundary, plus targeted enrichment of seven existing chapters (added 2026-08-05, see §5.3 and §5.8) | Odoo is not domain-agnostic the way Django is: its core abstractions *are* business objects, so `account.move`, `stock.move` and `sale.order` are the substance of every real ticket rather than examples layered on a framework. The existing plan already leans on knowledge it never teaches (ch32 says "extend the Sales flow", ch36's report is an invoice, ch37's portal shows invoices and orders, ch48's N+1 examples are over `account.move.line`, and LibreFleet's `part` to `product.product` bridge is abstract without it). So this fills a hole the plan already depends on rather than adding scope. Taught the developer way (run the flow in the UI, then inspect the models, tables, state transitions and core source it drove), which is what neither functional training nor developer tutorials do, and which odoolings can verify over XML-RPC. |
| D13 | Chapter renumbering | **Renumber ch21-40 to ch31-50 once, before writing any new content**, so the new parts sit in their pedagogically correct position with sequential numbering (added 2026-08-05, runbook in §5.8) | The new parts must land after Part 3 (the "read it" half needs the ORM, psql and shell from ch9-15) and before the old ch22 (extending the Sales flow is unlearnable without knowing the Sales flow). Any scheme that avoids renumbering produces a sidebar where numbering runs ch20, ch41, ch21, which reads as permanently bolted on. Measured the cost rather than guessing: 20 file renames of which only 4 are written chapters, 4 part folders, 4 checkpoint dirs, ~21 mechanical forward references in ch1-20, ~46 mixed references inside the four written chapters, plus glossary, odoolings keys and meta.json. **This is the cheapest this migration will ever be** (4 of 20 affected chapters written today, 20 of 20 if deferred). |
| D10 | Reader's workspace | **The reader builds in a repo they own**, bootstrapped in ch5 from two curl'd config files; this repo is read-only reference to them (added 2026-08-03, see §4.5 and the changelog) | The old flow told them to clone this repo and later fork it, which shipped the finished capstone into the exact directory ch8 says to create (silently, since `mkdir -p` and `touch` no-op on existing paths) and guaranteed `git pull upstream main` conflicts on every chapter. Owning their repo removes both failure modes structurally, matches real practice (a custom addon is its own repo, never a fork of a tutorial), and is only possible because `odoolings.py` is stdlib-only with no filesystem access. |

---

## 3. Research Summary — Ecosystem Facts the Executing Agent Must Know

These were verified against live sources in July 2026. Re-verify anything
version-sensitive before writing the corresponding chapter.

### 3.1 Odoo versions & cadence
- Odoo ships **one major version per year, around October**, announced at Odoo
  Experience in Brussels. Current: **Odoo 19 (Oct 2025)**. Expected: **Odoo 20
  (~Oct 2026)**, with an agentic-AI focus per the public roadmap.
- Only the **3 most recent majors are supported** (17/18/19 as of mid-2026; when 20
  ships, 17 drops off). This is why integrators live and breathe **migrations** —
  a whole chapter of the tutorial is dedicated to this.
- Docs live at `https://www.odoo.com/documentation/<version>/` — always link
  version-pinned URLs (19.0, the tutorial baseline), never `/master/`.

### 3.2 Architecture fundamentals (chapter source material)
- Three-tier: presentation (HTML5/JS/CSS + the **OWL** framework), logic (Python),
  data (**PostgreSQL only**).
- Everything is a **module** (a.k.a. addon): a directory with `__manifest__.py` +
  `__init__.py`, found via `--addons-path`. Modules declare `depends`; install/uninstall
  cascades follow the dependency graph.
- Business objects are Python classes mapped to tables by the **ORM**. Views are XML.
  Security = access rights CSV (`ir.model.access.csv`) + record rules + groups.
- The official beginner path is **"Server framework 101"** (builds a Real Estate
  module over ~16 chapters: models, fields, security, views, relations, compute/onchange,
  actions, constraints, inheritance, interacting with other modules, sprinkles/polish).
  Our curriculum tracks the same concept order (it's well-designed) but with an
  **original capstone project** and added integrator-world chapters the official
  tutorial lacks (OCA, Docker, migrations, code review, performance).
- Other official tutorials to link per-chapter: "Discover the web framework" (OWL),
  "Master the web framework", "Define module data", "Restrict access to data",
  "Safeguard your code with unit tests", "Build PDF reports", "Website themes".

### 3.3 OCA (Odoo Community Association) — critical for a Camptocamp dev
- Nonprofit (Swiss association) hosting hundreds of GitHub repos of community
  modules at `github.com/OCA`, organized by domain (server-tools, web, partner-contact,
  account-financial-tools, etc.), each governed by a **PSC** (Project Steering Committee).
- Contribution workflow (must become second nature): sign the **CLA** → fork repo →
  branch off the **version branch** (e.g. `18.0`, never `master`) → commit with
  **`[TAG] module_name: description`** convention (`[FIX]`, `[IMP]`, `[ADD]`, `[MIG]`,
  `[REF]`...) → run **pre-commit** locally (ruff/pylint-odoo/prettier hooks) → open PR
  targeting the version branch → CI (GitHub Actions) + **Runboat** (throwaway live test
  instances per PR, successor to the old runbot) → needs ~2–3 approving reviews incl.
  a PSC member → merged via the **OCA GitHub bot** (`/ocabot merge minor` etc.).
- Module **maturity levels** in `__manifest__.py` `development_status`: Alpha, Beta
  (default), Production/Stable, Mature — each with defined merge requirements.
- README files are generated from `readme/` RST fragments by OCA tooling — don't edit
  README.rst by hand in OCA modules.
- Translations go through **Weblate** — never edit `.po` files in PRs.
- **Module migration** between versions is a first-class OCA activity: each repo has a
  "Migration to version X" tracking issue; git history must be preserved (technique:
  `git format-patch` / the documented migration procedure); **OpenUpgrade** is the
  OCA project for Community-edition database migrations.
- OCA coding guidelines extend Odoo's own; key tools: `pre-commit`, `pylint-odoo`,
  `oca-maintainer-tools`, module template repo. Reviewing others' PRs is expected
  etiquette ("keep a good submitted/reviewed ratio").
- Camptocamp context: long-time major OCA contributor (staff have built core OCA
  infrastructure and tooling). Expect heavy use of OCA modules in client projects,
  Docker-based deployment, and strong code-review culture. The tutorial's "expert"
  tier should explicitly teach *working the OCA way*.

### 3.4 Frontend
- Odoo's JS framework is **OWL** (Odoo Web Library) — a small component framework with
  hooks and a QWeb-based XML template syntax (conceptually React-like but distinct).
- **QWeb** is also the server-side templating engine for reports and website pages.
- Website building blocks ("snippets"), portal pages, and the POS all ride on this stack.

### 3.5 Tooling landscape worth teaching
- `odoo-bin` CLI: `-d`, `-i`, `-u`, `--addons-path`, `--dev=all`, `--test-enable`,
  `--test-tags`, `shell` subcommand, `scaffold` subcommand.
- Debugging: `--dev=all` auto-reload, `pdb`/`debugpy`, browser devtools for OWL,
  developer mode (`?debug=1`) in the UI, `ir.logging`, PostgreSQL query logging.
- Quality: `pre-commit`, `ruff`, `pylint-odoo`, OCA CI.
- Data/ops: `click-odoo`, `odoo-shell` scripting; (mention, without depending on them,
  Camptocamp OSS like `marabunta`/`anthem` for migrations/seeding — verify current
  status when writing that chapter).

---
## 4. Website & Repository Design

### 4.1 Monorepo structure (as built — post-D3 revision)

```
odoolings/                          # public GitHub repo
├── ODOO_TUTORIAL_MASTER_PLAN.md    # this file — single source of truth + changelog
├── web/                            # Next.js 16 + Fumadocs + Tailwind 4, static export
│   ├── content/docs/               # all tutorial content (MDX)
│   │   ├── index.mdx               # docs landing: what/why/how to use
│   │   ├── roadmap.mdx             # milestone status table (keep in sync with §6)
│   │   ├── glossary.mdx            # Odoo jargon: addon, manifest, recordset, sudo, ...
│   │   ├── 00-orientation/         # one folder per part, one NN-slug.mdx per chapter,
│   │   ├── 01-environment/         #   nav order in each folder's meta.json
│   │   └── ...
│   ├── components/                 # quiz.tsx, mermaid.tsx, progress-pill.tsx,
│   │                               #   mark-complete.tsx, search.tsx (see §4.4)
│   └── app/, lib/, ...             # Fumadocs plumbing; root path, custom domain
├── code/
│   ├── addons/                     # SHIPS EMPTY (.gitkeep only). Readers build in
│   │                               #   their own repo (§4.5); librefleet/ here is the
│   │                               #   authoring workspace, git-excluded locally
│   ├── checkpoints/
│   │   └── ch08/ ch09/ ...         # snapshot of the addon after each chapter; also
│   │                               #   the canonical "final state" and diff reference
│   ├── odoolings.py                # XML-RPC work checker (see §4.4), stdlib only
│   ├── docker-compose.yml          # odoo:19 + postgres:16 — the exact dev env taught
│   ├── odoo.conf
│   ├── .pre-commit-config.yaml     # OCA-style hooks, added in Part 6
│   └── requirements-dev.txt        # added when first needed, not before
├── .github/workflows/              # deploy Pages on push; ci.yml for module tests (M3)
├── LICENSE-content (CC BY-SA 4.0), LICENSE-code (AGPL-3)
├── CONTRIBUTING.md
└── README.md
```

### 4.2 Site conventions (Next.js + Fumadocs)
- Navigation: parts as sidebar sections, chapters as pages; prev/next footer nav,
  ZBSearch static search, dark mode — all from Fumadocs.
- Code blocks with copy button and line highlights (Shiki via Fumadocs MDX).
- Callout boxes with consistent semantics used throughout (Fumadocs `<Callout>`):
  - `type="info"  title="Official docs"` → link to the canonical doc page for the topic
  - `type="warn"  title="Gotcha"` → real-world pitfalls
  - `type="info"  title="In the field"` → integrator/OCA/Camptocamp practice notes
  - `type="info"  title="On Odoo 18 this differs"` → version deltas for older projects
- Hands-on sections use `<Steps>`/`<Step>` (house style since the ch1-10 review,
  2026-08-09; ch8 was the trial). The component numbers the steps, so the `###` heading
  inside carries no number of its own and still reaches the table of contents.
- Any chapter that adds a file to LibreFleet shows the whole module tree after the step
  with `<Files className="bg-(--tone-sky)">`, so the reader watches it grow.
- Diagrams: the `<Mermaid>` client component (architecture, request lifecycle, ERDs).
  **`label` is mandatory** (it is the `aria-label`; the default is a useless "Diagram"),
  and `tests/cross-refs.mjs` enforces it. `<br/>` for line breaks in node text, not `\n`.
- Per-chapter footer: *Prerequisites · What you built · Official reading ·
  OCA modules worth studying · Exercise checklist.*

### 4.3 Chapter template (every chapter MUST follow this skeleton)

```markdown
# NN. Chapter Title            <- frontmatter: title + description
**Goal:** one sentence. **Time:** ~X h. **Checkpoint:** code/checkpoints/chNN

## Why this matters            <- motivation, real-world framing
## Concepts                    <- original explanation, diagrams, links to official docs
## Hands-on                    <- numbered steps on the capstone project
## Verify                      <- prove it works: UI steps, odoo-bin shell/psql, and
                                  `python odoolings.py check chNN` where checks exist
## Gotchas                     <- pitfalls collected while writing/testing the chapter
## Quick check                 <- <Quiz> with 3–5 questions, each with a `why`
## Exercises                   <- graded ⭐/⭐⭐/⭐⭐⭐ tasks (see §5.6), no inline solutions
## Further reading             <- official docs + OCA examples + (optional) videos
```

**Authoring rules for the agent:**
1. Every "Hands-on" section must be *executed and verified* in the Docker environment
   before the chapter is marked done. No untested code ships. Screenshots are taken
   from the author's own running instance.
2. Every chapter that changes the capstone module must register odoolings checks for
   its end state, and its Verify section must reference them. Quizzes must test the
   chapter's *ideas* (predict behavior, choose the right approach), not recall of
   syntax that the reader can look up.
3. **Functional chapters (Parts 4 and 5) use the same skeleton, no fork.** Keeping one
   template is what stops them reading as a bolted-on track. What changes is only what
   each section contains, and one rule about Hands-on:
   - **Concepts** covers the business idea *and* the models behind it, so the reader
     always meets `sale.order` next to "quotation".
   - **Hands-on splits into two numbered movements, always in this order:**
     "Run the flow" (do it in the UI, as a user would) then "Read what it did"
     (`psql`, `odoo shell`, `ir.model.fields`, the generated `stock.move` /
     `account.move` records, and the core source method that ran, e.g. reading
     `sale/models/sale_order.py::_action_confirm` after confirming an order).
     The second movement is the whole point. A functional chapter that only narrates
     clicking is a failed chapter, and is exactly the weakness of existing Odoo
     functional training.
   - **Verify** runs odoolings against the reader's *separate demo database*, never
     the `tutorial` DB (see §5.3's note on the functional database).
   - **Exercises** are ticket-shaped wherever possible: "the client says the discount
     on this quote is wrong, here is the pricelist config, find why" beats "explore
     the pricelist screen". This extends the break-it-lab philosophy (§5.6) into
     functional territory, and trains the actual job.

### 4.4 Interactive mechanics — inventory & roadmap

Built (keep polishing, don't rebuild):
- **`<Quiz>`** — per-chapter multiple choice, instant feedback with explanations.
- **`odoolings.py`** — rustlings-style CLI verifying the reader's *running* Odoo over
  XML-RPC, with hints on failure. Chapter checks (`ch05`…) plus, from Part 2 on,
  boss-challenge check sets (`boss2`…, see §5.6).
- **Progress + streaks** — localStorage pill; per-chapter "mark complete". No
  accounts/backend by design; revisit only if a real learner community shows up.
- **`<Mermaid>`** — diagrams as code.

Planned (build at the milestone that needs them, not before):
- **Sidebar completion checkmarks** driven by the same localStorage state (small; do
  during M1 wrap-up so Part 2 readers see their trail).
- **Quiz persistence + per-part mastery** — remember quiz results, show a "Part N
  mastery" bar; feeds the end-of-part review quiz (§5.6). M2.
- **`<Term>` glossary tooltips** — inline hover definitions linking to the glossary,
  so jargon is explained where it occurs. M2, then backfill.
- **Predict-the-output quizzes** — a `code` field on quiz questions rendering a
  snippet above the options ("what does this recordset expression return?"). Extends
  `<Quiz>`, not a new component. M2 (recordsets chapter is the natural debut).
- **ch47 interactive migration checklist** — trackable checkboxes for the OCA
  migration procedure. Build when writing ch47 (was ch37 before the D13 renumber).
- **`odoolings snapshot` / `odoolings diff`** — the one genuinely new tool, and the
  thing that makes Parts 4 and 5 active rather than narrated. `snapshot` records
  per-model record counts and max ids over XML-RPC; `diff` reports what changed since.
  So the reader clicks **Confirm** on a quotation and gets back: `sale.order.state`
  draft to sale, +1 `stock.picking`, +2 `stock.move`, +0 `account.move`. It turns
  "what did that button actually do?" from a paragraph of prose into a repeatable
  forensic method the reader owns, and it exists nowhere else in the Odoo ecosystem.
  Stays inside D10's constraint: pure XML-RPC, no filesystem access, so it works
  against any database the reader points it at. Build it **before ch21**, since every
  functional chapter's "Read what it did" movement uses it. Scope it small: a model
  allowlist (the ~15 models Parts 4-5 touch) rather than introspecting all ~900, and
  JSON state in a gitignored dotfile.

### 4.5 The reader's workspace contract (decided 2026-08-03, see D10 and D11 in §2)

**The reader's LibreFleet lives in a repo they own, created from a template. They never
clone this repo.** Their layout, established in ch4/ch5:

```
librefleet/                 # THEIR repo, from "Use this template", name is their choice
├── docker-compose.yml      # ships in the starter; ch5 explains every line
├── odoo.conf               # ships in the starter
├── .gitignore              # ships in the starter (__pycache__, *.pyc, .checkpoints/)
├── README.md               # ships in the starter
├── odoolings.py            # curl'd in ch5 (stdlib-only, changes every chapter)
├── .checkpoints/chNN/      # fetched on demand in ch8, gitignored
└── addons/
    ├── .gitkeep            # ships in the starter, and MUST: see rule 6
    └── librefleet/         # their module, from ch8
```

**Repo map (D11).** Two repositories, and the boundary is deliberate:

| Repo | Owns | Churn |
|---|---|---|
| `odoolings` | site, chapter MDX, `code/checkpoints/`, `code/odoolings.py`, this plan | every chapter |
| `odoolings-starter` | the 5-file GitHub template readers instantiate | ~annually |

`code/docker-compose.yml` and `code/odoo.conf` here are the **source of truth**; the
starter holds copies and `.github/workflows/deploy-pages.yml` fails the build if they
drift. Mirror changes to the starter; never relax the check.

Rules that follow, and that every chapter must respect:

1. **Never tell the reader to clone this repo, full stop.** Not as a workspace, not as a
   reference. Everything they need arrives as a targeted fetch: `odoolings.py` by `curl`
   (ch5), and a single chapter's checkpoint by tarball extract into `.checkpoints/`
   (ch8's pattern, ~300 KB, always current, nothing to keep in sync):

   ```
   curl -sL https://github.com/ronitjadhav/odoolings/archive/main.tar.gz \
     | tar -xz -C .checkpoints --strip-components=3 'odoolings-main/code/checkpoints/chNN'
   ```
2. **Reader-facing paths are `addons/librefleet/...`**, never `code/addons/...`. The
   `code/` prefix is an artifact of this monorepo and means nothing to them. This also
   matches the `client-project/addons/` layout ch7 already teaches.
3. **`code/checkpoints/chNN` stays the correct reference** in the Checkpoint header
   line and in diff commands: it names a path in *this* repo, which is right.
4. **odoolings is location-independent** (no filesystem access, pure XML-RPC against
   `--url`), which is what makes all of the above possible. Keep it that way: a check
   that reads the reader's files would break this contract.
5. **Fork mechanics** (`git remote rename origin upstream`, etc.) belong in ch45 (pre-D13:
   ch35, corrected 2026-08-11 once ch35 turned out to be cron/server/automated actions
   instead) where they fork an OCA repo to submit a real PR, not in ch7 where they used
   to exist only to work around living in someone else's repo. The starter is a **template**, not a
   fork, precisely so the reader has no upstream and no temptation to PR against us.
6. **`addons/.gitkeep` must stay in the starter.** Git cannot track an empty directory,
   but the directory has to exist before the first `docker compose up`: bind-mount a
   missing path and Docker creates it owned by `root`, which makes ch8's `mkdir` fail with
   `Permission denied` for every Linux reader. Verified the hard way on 2026-08-03.
7. **Setup must need no shell.** ch4/ch5 get the reader running via "Use this template"
   plus `git clone` and `docker compose up`, nothing else. The POSIX-shell requirement
   (ch5's callout) applies to the *rest* of the tutorial, and must not creep back into
   setup: an earlier `curl`-the-config-files design forced exactly that and was reverted.
8. **The starter's default branch tracks D1's baseline** (19.0 today). On a baseline bump,
   branch the outgoing version in the starter *first*, then move its `main`.

---

## 5. Curriculum — The Complete Syllabus

### 5.1 Shape of the journey
Ten parts, 50 chapters, three proficiency tiers (revised 2026-08-05 by D12/D13, which
added Parts 4-5 and pushed the old Parts 4-7 to 6-9):

- **Tier 1 — Foundations (Parts 0–3, ch 1–20):** can build and ship a clean custom
  module.
- **Tier 2 — Professional (Parts 4–7, ch 21–42):** understands the business system
  Odoo actually is, extends core apps safely, writes tests, builds UI, debugs anything.
- **Tier 3 — Expert/Integrator (Parts 8–9, ch 43–50):** works the OCA way, migrates
  modules, tunes performance, reasons about deployments and upgrades.

**The narrative turn, and why Parts 4-5 sit exactly here.** Parts 2-3 build LibreFleet
as an island: `librefleet.part` carries its own `standard_cost` and `list_price`, which
quietly reimplements a slice of `product.product`. That is correct pedagogy (learn the
framework in isolation, without core's surface area in the way) but it is not how a
real integrator would build it. Parts 4-5 are the reveal: here is what Odoo already
ships, and here is the system your module lives inside. Part 6 then becomes the payoff
rather than an abstraction, because "extend the Sales flow" and "bridge `part` to
`product.product`" now describe flows the reader has personally run and inspected.
So the tutorial reads as three acts: **build a module → meet the system → work inside
the system**, which is also the real arc of a developer's first year on Odoo.

### 5.2 The capstone project
An original, non-trivial domain that exercises every framework feature and does not
collide with the official Real Estate tutorial or common demo apps:

> **"LibreFleet" — a vehicle-workshop & service-booking management app.**
> Customers, vehicles, service orders with stages and a kanban, parts consumption,
> technician assignment (many2many), computed totals and margins, statbuttons,
> constraints (no overlapping bookings), an approval wizard, mail/chatter integration,
> a customer portal page to view service history, a QWeb PDF service report, a small
> OWL dashboard widget (jobs per technician), scheduled actions (maintenance
> reminders), and — in the expert tier — a refactor of one feature into an
> OCA-quality standalone module with tests, readme fragments and pre-commit passing.

(The agent may propose a different domain, but it must exercise the same feature
matrix; get the author's sign-off before writing Part 2.)

### 5.3 Chapter list

**Part 0 — Orientation (no code)**
1. What Odoo is: ERP concept, apps vs modules, Community vs Enterprise, editions,
   versioning & the October cadence, odoo.sh vs on-prem vs Odoo Online.
2. The ecosystem map: Odoo SA, integrators/partners, the OCA, where Camptocamp-style
   integrators fit; how the official docs, OCA repos, and YouTube channels relate.
3. Architecture overview: three tiers, request lifecycle, the ORM idea, modules and
   the addons path. (Mermaid diagrams.)
4. Guided tour as a *user*: install a demo DB, click through Sales/CRM/Inventory for
   30 minutes, enable developer mode — you must know the product to develop it.
   **Scope note (D12):** this stays *first contact* only, deliberately shallow. It must
   not try to teach the flows, and it should now close by pointing forward to Parts 4-5
   ("you will come back and take these apart properly once you can read the database").

**Part 1 — Environment**
5. Dev setup with Docker Compose: Odoo 19 + Postgres 16, volumes for addons and
   filestore, config file, first login. Appendix: native install from source.
6. Daily driver workflow: `odoo-bin` flags that matter, `--dev=all`, log reading,
   database create/drop/duplicate, `psql` basics, VS Code setup (Python + XML
   tooling), using `odoo-bin shell`.
7. Git for Odoo work: repo layouts integrators use, addons pinning, branch-per-version
   mindset (mirrors OCA/odoo branches like `18.0`).

**Part 2 — Your first module (ORM core)**
8. Scaffold LibreFleet: manifest anatomy, module install/upgrade cycle, app icon.
9. Models & fields: `models.Model`, field types & attributes, automatic fields,
   what the ORM creates in Postgres (inspect with psql!).
10. Security first: groups, `ir.model.access.csv`, why the module 404s without it.
11. Menus, actions, and your first views: window actions, menu items, list & form.
12. Relations: many2one, one2many, many2many — modeled on customers→vehicles→orders.
13. Computed fields, related fields, onchange; store vs non-store; dependencies.
14. Constraints: SQL vs Python (`@api.constrains`), default values, sequences
    (`ir.sequence`) for order references.
15. Recordsets deep-dive: search/browse/filtered/mapped/sorted, environment (`env`),
    `create`/`write`/`unlink`, `ensure_one`, context, `sudo` (and its dangers).

**Part 3 — Views & UX**
16. View architecture: `ir.ui.view`, inheritance with xpath, view priorities.
17. List & form mastery: widgets, decorations, statusbar, smart buttons, notebooks.
18. Search views, filters, group-by, default filters via context.
19. Kanban views (with the service-order pipeline) + calendar, pivot, graph views.
20. Wizards: `TransientModel`, an "approve & invoice" wizard for service orders.

**Part 4 — How Odoo runs a business** (NEW, D12; the "meet the system" act)

> **All ten chapters in Parts 4-5 run in a separate demo database**, never the reader's
> `tutorial` DB: `odoo -d functional -i <apps> --with-demo --stop-after-init`, verified
> with `odoolings check chNN --db functional`. Three reasons: functional exploration
> needs demo data (chart of accounts, products, partners), installing `sale`/`purchase`/
> `stock`/`mrp`/`account` into `tutorial` would pollute the dev DB and change every
> later checkpoint diff, and `--db` already exists so this needs no new tooling.
> **Verified installable on Odoo 19 Community** (checked in the container 2026-08-05):
> `crm`, `sale`, `sale_management`, `sale_stock`, `purchase`, `purchase_stock`, `stock`,
> `stock_account`, `stock_landed_costs`, `mrp`, `mrp_account`, `account`, `analytic`,
> `payment`, `delivery`, `sale_loyalty`, `point_of_sale`, `website`, `website_sale`.

21. The business spine: partners, products & units. `res.partner` (the
    company/contact hierarchy, customer *and* vendor on one model),
    `product.template` vs `product.product` and how variants generate, product types,
    units of measure (a `relative_uom_id` tree in 19, **not** the pre-19 categories:
    corrected 2026-08-05 after checking the container), product categories.
    Everything in Parts 4-5 sits on this,
    and it is where the reader first meets `odoolings snapshot`/`diff` plus the
    "identify the model behind any screen" developer-mode habit. Connects straight back
    to ch12 (relations) and forward to ch32's `part` to `product.product` bridge.
22. Sales: from lead to confirmed order. The CRM pipeline briefly (lead vs
    opportunity, stages, activities the reader will *build* in ch33), then quotation to
    `sale.order`, order lines, delivery and invoice policies, and the `state` machine
    ch32 will extend. Read-what-it-did payoff: `sale/models/sale_order.py::_action_confirm`.
23. Pricing: pricelists, discounts & promotions. `product.pricelist` rules and their
    resolution order, discounts, `sale_loyalty` promotions and coupons, and how
    `price_unit` on a line is actually arrived at. High-value because price computation
    is one of the most common real ticket sources. Ticket-shaped exercise lives here.
24. Purchase: from RFQ to vendor bill. `purchase.order` lifecycle, vendor pricelists,
    reordering rules, receipts, and the three-way match (order, receipt, bill).
25. Inventory: moves, quants & warehouses. Locations, `stock.move` as double-entry for
    goods (a move always has a source and a destination, which is the same idea
    accounting uses for money), pickings, `stock.quant`, on-hand vs forecast, lead times.
26. Manufacturing: bills of materials & manufacturing orders. `mrp.bom`, components,
    operations and work centers, the `mrp.production` lifecycle, component consumption
    and finished-goods receipt. Kept in Part 4 because it is a transactional flow like
    the others, not a specialism.

**Part 5 — Odoo's accounting core** (NEW, D12) + `boss4`

> Split from Part 4 deliberately: double-entry is a genuinely different mental model
> and deserves its own part rather than being the tail of a six-chapter slog. It also
> gives the reader a part-completion milestone (and a mastery bar, §4.4) halfway
> through the functional act. **Verified in the container:** Community `account` ships
> the full core (`account.move`/`.move.line`, journals, chart of accounts, `account.tax`
> + `fiscal.position` + repartition lines, `account.payment` + payment terms,
> `partial`/`full.reconcile` + `reconcile.model`, bank statements, all six lock dates,
> and the `account.report` *engine*). Enterprise-only and confirmed absent from disk:
> `account_accountant`, `account_reports` (the P&L/Balance-Sheet/Aged *definitions*),
> `sale_commission`. `sale_subscription` has an `ir.module.module` row but no files and
> state `uninstallable`.

27. Accounting foundations: double-entry and the `account.move` duality. Debits and
    credits, chart of accounts, journals, and **the single highest-value fact in these
    two parts: an invoice and a journal entry are the same model.** One `account.move`
    with `account.move.line` children carrying debit/credit, distinguished by
    `move_type`. Draft vs posted, sequences and inalterability. Every developer who has
    not internalised this writes wrong accounting code.
28. Invoicing, payments & reconciliation. Invoice from a sales order, invoicing policy
    (ordered vs delivered), credit notes, vendor bills, `account.payment`, payment
    terms and partial payments, reconciliation via `account.partial.reconcile`,
    `payment_state`, bank statements and `account.reconcile.model`. (Community has the
    reconciliation *engine*; the slick bank-rec widget is the Enterprise part, so this
    chapter reconciles the honest way, which is also the way the ORM sees it.)
29. Taxes & fiscal positions. Tax computation, price-included vs price-excluded,
    tax groups, `account.tax.repartition.line`, fiscal positions mapping taxes by
    country, and why rounding differences appear. Bites developers constantly.
30. Inventory valuation: where stock meets accounting. Costing methods (standard,
    FIFO, AVCO), manual vs automated valuation, stock interim accounts, how a delivery
    posts journal entries, landed costs, COGS. This is the chapter that explains the
    "why is the P&L wrong" class of ticket, and it is the natural join between Part 4
    and Part 5. Closes with lock dates and period close, plus **defining a small custom
    `account.report`**, which is a real Community exercise precisely because the engine
    ships but the statements do not.
- **`boss4` — Run the business end to end.** The cross-app use case (the "branded
  merchandise" shape borrowed from Odoo's own T-shirt training exercise, retold for
  LibreFleet): purchase blank stock, manufacture the branded item, sell it online,
  deliver it, invoice it, collect and reconcile the payment, then prove the inventory
  valuation and the resulting journal entries are what you expect. Spec only, no steps.
  odoolings verifies the whole chain links up (lead → order → picking → invoice →
  payment → reconciliation), which is something no functional training can do.
  **Stretch (and the best developer content in these two parts):** the two things
  Community lacks become *builds*, not omissions. Implement recurring maintenance-plan
  billing (the `sale_subscription` substitute) and a service-advisor commission
  calculation (the `sale_commission` substitute) as LibreFleet features. A developer
  who builds recurring billing has learned more than one who clicked through the
  Enterprise app.

**Part 6 — Business logic like a pro** (was Part 4, ch 21-28; +10 by D13)
31. Model inheritance the three ways: classic `_inherit` extension, prototype
    (`_inherit` + new `_name`), delegation `_inherits` — and when to use each.
32. Extending core apps: add fields to `res.partner`, extend Sales flow; never
    modify core, always extend (the golden rule). **Now assumes ch21-22**, so the
    `part` to `product.product` bridge and the Sales-flow extension describe flows the
    reader has run and inspected rather than abstractions.
33. Mail & chatter: `mail.thread`, activities, followers, email templates,
    automated notifications. (The reader met chatter and activities as a *user* in
    ch22's CRM pipeline; here they build them.)
34. Data files: XML vs CSV, `noupdate`, demo data vs master data, `ref()`/xml-ids
    across modules.
35. Scheduled actions (cron), server actions, automated actions.
36. QWeb reports: PDF service report with header/footer, paper formats. **Now assumes
    ch27-28**, so the canonical invoice-report example is grounded.
37. Controllers & portal: HTTP routes, `type='http'` vs `'json'`, auth levels,
    building the customer portal page; a taste of the website builder. **Now assumes
    ch22/28** (the portal shows real orders and invoices), and this is where
    eCommerce's functional context belongs rather than in Parts 4-5.
38. Testing: `TransactionCase`, `HttpCase`/tours intro, `--test-tags`, demo-data
    pitfalls, writing tests for everything built so far.

**Part 7 — Frontend (OWL) & the web client** (was Part 5, ch 29-32; +10 by D13)
39. OWL fundamentals: components, props, state, hooks, QWeb templates in JS,
    assets bundles (`web.assets_backend`).
40. Extending the web client: a custom field widget, patching existing components.
41. The LibreFleet dashboard: a client action with an OWL component pulling data
    via ORM RPC (`useService("orm")`).
42. (Survey chapter, lighter) Website themes & snippets, POS customization —
    what exists, where the docs are, when you'd go deeper. **This is where POS's
    functional context belongs** (session → orders → payment methods → session close
    and its journal entries), because POS is Odoo's largest OWL application and an
    offline-first one, which makes it the right case study for *this* part rather than
    a chapter in Part 4.

**Part 8 — The OCA way (expert tier begins)** (was Part 6, ch 33-36; +10 by D13)
43. OCA safari: how repos/PSCs are organized, finding modules (odoo-community.org,
    GitHub, Odoo Apps store), judging maturity levels, reading OCA module source
    as study material.
44. OCA tooling on your own module: pre-commit (ruff, pylint-odoo, prettier),
    readme fragments, manifest conventions, module naming rules.
45. Contributing: CLA, fork/branch/commit conventions (`[FIX] module: ...`), PR
    targeting version branches, Runboat, review etiquette, the ocabot; do a real
    first contribution (docs fix or small improvement).
    **Must cover fork mechanics in full** (`fork` → `git remote add upstream` →
    feature branch off the version branch → `git pull upstream 19.0` → PR). This
    moved here from ch7 on 2026-08-03 (D10, §4.5): forking is genuinely required to
    contribute to OCA, whereas in ch7 it only existed to work around the reader
    living inside this repo.
46. Refactor a LibreFleet feature into a standalone OCA-quality module —
    the capstone-of-the-capstone.

**Part 9 — Integrator craft** (was Part 7, ch 37-40; +10 by D13)
47. Migrations: why yearly releases force them, migrating a module 18→19 (manifest,
    views, API changes — the deprecation list from the D1 revision is the exercise
    material), OCA migration process & preserving git history, OpenUpgrade
    for database migrations, Enterprise upgrade service (concept level).
48. Performance: read the ORM's SQL, N+1 patterns, `read_group`, batch `create`,
    indexes, `prefetch`, profiling; when to drop to SQL (and the rules for doing so).
49. Deployments & ops (concept level): workers, longpolling/gevent, nginx, filestore,
    backups, staging/prod flows, odoo.sh vs Docker platforms; multi-company and
    localization awareness.
50. Career map: reading core source effectively, Odoo certification, OCA Days /
    Odoo Experience, keeping up with version releases; what changes in Odoo 19/20
    and how to re-learn efficiently each October.

### 5.4 Concept coverage checklist (verified for real 2026-08-12, at ch50, see §10)
ORM CRUD ✅ recordsets ✅ env/context ✅ compute/related/onchange ✅ constraints ✅
sequences ✅ all 3 inheritance types ✅ view inheritance/xpath ✅ all view types ✅
wizards ✅ security (groups/ACL/record rules/sudo) ✅ mail.thread ✅ cron ✅
server actions ✅ QWeb reports ✅ controllers ✅ portal ✅ OWL component ✅ widget ✅
assets ✅ tests (unit + tour) ✅ data files/noupdate ✅ i18n basics ✅ (ch34) pre-commit/OCA
conventions ✅ migration exercise ✅ (ch47) performance patterns ✅ (ch48) deployment concepts ✅ (ch49)

Functional coverage (added 2026-08-05, D12; Parts 4-5):
partner/company model ✅ product.template vs product.product + variants ✅ UoM ✅
sale.order lifecycle ✅ CRM pipeline ✅ pricelist resolution ✅ discounts/promotions ✅
purchase.order + three-way match ✅ stock.move/quant/picking ✅ warehouses & locations ✅
mrp.bom + mrp.production ✅ double-entry ✅ account.move duality (invoice = journal
entry) ✅ journals & chart of accounts ✅ payment + reconciliation ✅ payment terms ✅
taxes (incl./excl.) + fiscal positions ✅ inventory valuation (std/FIFO/AVCO) + COGS ✅
lock dates/period close ✅ (ch27, added 2026-08-12) account.report engine ✅ POS session → journal entry ✅
eCommerce order → sale.order ✅ (ch42, added 2026-08-12)

### 5.5 LibreFleet blueprint (data model & feature map — added 2026-07-13)

The schema below is fixed *before* M2 so chapters build one coherent module instead of
inventing fields as they go. Module name **`librefleet`** — deliberately not `fleet`,
because core Odoo ships a `fleet` module (that collision is itself a ch8 teaching
point). Models use the `librefleet.` prefix. **Author sign-off on this blueprint is
the gate for starting M2** (like the capstone-domain sign-off was for Part 2 planning).

Models, with the chapter that introduces each piece:

- **`librefleet.vehicle`** (ch9) — the reader's first model. `license_plate` (Char,
  required), `vin` (Char), `model_name` (Char), `year` (Integer), `mileage_km`
  (Float), `notes` (Text), `active` (Boolean — archiving). ch12 adds `owner_id`
  (many2one → `res.partner`) and `service_order_ids` (one2many). ch13 adds
  `service_count` (computed, statbutton). ch14 adds a SQL unique constraint on
  `license_plate` and a Python constraint on `year`.
- **`librefleet.service.type`** (ch11) — deliberately tiny config model (`name`,
  `flat_fee`, `default_duration_h`) so the first menus/actions/views chapter works on
  something with no relations yet.
- **`librefleet.service.order`** (ch12) — the centerpiece. `reference` (Char, from
  `ir.sequence`, ch14), `vehicle_id` (many2one), `customer_id` (related to
  `vehicle_id.owner_id`, stored — ch13), `service_type_id` (many2one),
  `technician_ids` (many2many → `res.users`), `line_ids` (one2many), `stage`
  (Selection: draft → confirmed → in_progress → done/cancelled; statusbar ch17,
  kanban pipeline ch19), `scheduled_start`/`scheduled_end` (Datetime; the
  no-overlapping-bookings-per-vehicle constraint, ch14), `parts_total` / `labor_total`
  / `margin` (computed with `@api.depends`, ch13). Later: chatter (ch23), approve &
  invoice wizard (ch20), QWeb PDF report (ch36), portal view (ch37), maintenance-
  reminder cron (ch35), OWL jobs-per-technician dashboard (ch41). [Pre-D13 numbers
  corrected 2026-08-11 when ch35 was written; see the changelog entry above.]
- **`librefleet.part`** (ch12) — `name`, `code`, `standard_cost`, `list_price`.
  Self-contained on purpose: no dependency on `product`/`sale` in Tier 1. Bridging to
  real product/invoice flows is exactly what ch22 (extending core apps) then teaches.
- **`librefleet.service.order.line`** (ch12/13) — `order_id`, `part_id`, `qty`,
  `price_unit` (default from part), `subtotal` (computed).

Security (ch10): two groups — *Workshop / User* (technicians: read all, write orders
assigned to them via record rule) and *Workshop / Manager* (full CRUD + config
models). The record rule lands in ch10 and is *felt* throughout Part 2–3.

Part 8 extraction candidate (ch46): the maintenance-reminder feature becomes a
standalone OCA-quality `librefleet_maintenance_reminder` module.

**How LibreFleet relates to Parts 4-5 (D12).** The blueprint above is deliberately an
*island*: `librefleet.part` carries its own `standard_cost`/`list_price`, and service
orders have their own totals, none of it touching `product`, `sale` or `account`. That
is the right call for Parts 2-3 (learn the ORM without core's surface area in the way),
and Parts 4-5 are where the reader finds out what it cost: Odoo already ships all of
it. Nothing in the blueprint changes; what changes is that ch32's bridge to
`product.product`, ch36's invoice report and ch37's portal stop being abstractions.
The two Community gaps (`sale_subscription`, `sale_commission`) become LibreFleet
features in `boss4`'s stretch: a recurring maintenance plan (which §5.5 already hints
at) and a service-advisor commission.

### 5.6 Challenge design (added 2026-07-13 — makes the tutorial *hard* in the right places)

Three exercise grades, used in every chapter's Exercises section:
- **⭐ Apply** — same pattern, new target ("add a `color` field to vehicles and show
  it in the list"). Confidence reps.
- **⭐⭐ Transfer** — combine this chapter with earlier ones, no steps given ("managers
  see cancelled orders, technicians don't — no view duplication allowed").
- **⭐⭐⭐ Stretch** — requires reading official docs/OCA source beyond the chapter;
  flagged as optional so beginners don't stall.

**Boss challenges** close each part from Part 2 on — a one-page *spec* (no steps) for
a small feature or mini-module built from memory, verified by an odoolings check set:
- **Part 2 boss (`boss2`):** build a tiny "garage inventory" module (one model,
  security, menu, list+form, one computed field, one constraint) from a spec, without
  looking back at chapters. This replaces the vague "rebuild from memory" self-test
  with something *checkable*.
- **Part 3 boss (`boss3`):** full view suite (search defaults, kanban with grouping,
  a wizard) for a provided model spec.
- **Parts 4-5 boss (`boss4`):** run the business end to end across every app touched
  in the functional act (see §5.3). The only boss verified mostly by *state* rather
  than by code: odoolings walks the chain lead → order → picking → invoice → payment →
  reconciliation and checks it links up.
- **Part 6 boss (`boss5`, was `boss4`):** extend a core app per spec (field on
  `res.partner` + automated activity + a test that proves it).
- **Part 7 boss (`boss6`, was `boss5`):** a small OWL component against a documented
  RPC shape.
Boss specs live on the site; solutions live in `code/checkpoints/bossN/`.
**Boss renumbering (D13):** only `boss2` is written, so renaming the planned ones is
free. Do it as part of the §5.8 migration, not later.

**Ticket-shaped exercises (added 2026-08-05, D12)** — in Parts 4-5 especially, frame
exercises as the ticket an integrator actually receives rather than as a tour: "the
client says the discount on this quote is wrong, here is the pricelist config, find
why" instead of "explore the pricelist screen". Same spirit as the break-it labs below,
applied to configuration rather than code, and it trains the real job.

**Break-it labs** — one per chapter where instructive: deliberately cause the failure
the chapter protects against (delete the ACL line and upgrade; make two fields depend
on each other; drop a required field from a form view), read the actual
traceback/log, then fix it. Debugging literacy is the #1 skill gap of new Odoo devs
and no existing tutorial teaches it systematically — this is our differentiator.

**End-of-part review quizzes** — a cumulative `<Quiz>` on each part's index page
mixing questions from all its chapters (spaced repetition; pairs with the per-part
mastery bar from §4.4).

### 5.7 Functional-track scope: what is taught where (added 2026-08-05, D12)

The source for Parts 4-5 is Camptocamp's own functional onboarding curriculum. Mapping
it, with the Community feasibility verified in the container on 2026-08-05:

| Training topic | Lands in | Community? |
|---|---|---|
| Getting started, navigation | ch21 (+ ch4 first contact) | yes |
| CRM | ch22 (pipeline, briefly) | yes (`crm`) |
| Sales | ch22 | yes (`sale`, `sale_management`) |
| Pricelists, Promotions | ch23 | yes (`sale_loyalty` for promos/coupons) |
| Sales Tax | ch29 | yes |
| Delivery | ch25 | yes (`delivery`, `stock`) |
| Commissions | `boss4` stretch, as a **build** | **no** (`sale_commission` is Enterprise) |
| Purchase | ch24 | yes |
| MRP: overview, basics, manufacturing, orders | ch26 | yes (`mrp`, `mrp_account`) |
| Accounting basics | ch27 | yes |
| Invoicing, Payments | ch28 | yes |
| Banks and Cash | ch28 | engine yes; the bank-rec *widget* is Enterprise |
| Taxes | ch29 | yes |
| Inventory valuation | ch30 | yes (`stock_account`, `stock_landed_costs`) |
| Accounting management, End of period | ch30 | yes (all six lock dates present) |
| Reporting | ch30 | `account.report` **engine** yes, statements Enterprise |
| Point of Sale | ch42 (with the OWL part) | yes (`point_of_sale`) |
| Website, Ecommerce | ch37 + ch42 | yes (`website`, `website_sale`) |
| Subscriptions | `boss4` stretch, as a **build** | **no** (`sale_subscription` unusable) |
| Use Case: Branded T-shirt | `boss4` | yes |

**Deliberately not attempted:** turning the reader into a functional consultant.
Chart-of-accounts design, jurisdiction tax compliance and requirements gathering are
career skills, not chapters. The goal is the literacy a *developer* needs to not write
wrong code, plus enough breadth to follow a client conversation.

### 5.8 Migration runbook for D13's renumber (execute before writing any new chapter)

Ordered, and **must be one PR, fully verified, before ch21 is written**, or new content
collides with old numbering. Measured surface as of 2026-08-05:

1. **Rename part folders** (git mv), then fix the root `web/content/docs/meta.json`
   `pages` array to the new order, inserting the two new part folders:
   `04-business-logic` → `06-business-logic`, `05-frontend-owl` → `07-frontend-owl`,
   `06-oca-way` → `08-oca-way`, `07-integrator-craft` → `09-integrator-craft`.
   New: `04-odoo-business`, `05-accounting-core`.
2. **Rename 20 chapter files**, `NN` → `NN+10`, highest first to avoid collisions
   (40→50, 39→49, … 21→31). Update each file's own `title:` frontmatter and its
   `**Checkpoint:** code/checkpoints/chNN` line. Also update each part folder's
   `meta.json` `pages` array.
3. **Rename 4 checkpoint dirs**: `code/checkpoints/ch21..ch24` → `ch31..ch34`.
4. **Rename odoolings keys**: `CHAPTERS["ch21".."ch24"]` → `"ch31".."ch34"`, plus
   `"ch24-demo"` → `"ch34-demo"`, plus the section comments naming those chapters.
   Then rename planned bosses: `boss4` → `boss5`, `boss5` → `boss6` (only `boss2`
   exists, so this is documentation-only today).
5. **Fix cross-references. This is the only step with a real trap.** References to
   ch1-20 must NOT move; references to ch21-40 must gain 10; and both kinds appear
   *mixed inside the same paragraph* in the four written chapters, so a blind
   `sed s/chapter 2/chapter 3/` corrupts the content. Use a script that matches
   `(chapter|ch)\s*(\d\d?)` , parses the number, and rewrites only when `21 <= n <= 40`.
   Known counts to reconcile against afterwards: ~21 forward refs in ch1-20
   (ch4, ch6, ch7, ch8, ch12, ch13, ch14, ch15, ch16, ch17, ch19, ch20, boss2),
   ~46 mixed refs inside ch21-24, 9 in `glossary.mdx`, 11 in `odoolings.py`.
6. **The master plan is the exception:** its §10 changelog entries are a historical
   record and must keep their original numbers. Only §4-§6 current-state text gets
   renumbered. Do this by hand, not by script.
7. **Update the site's chapter arithmetic:** `web/lib/shared.ts` `TOTAL_CHAPTERS`
   40 → 50, and the homepage `TIERS` array's `parts` strings to
   `Parts 0–3 · ch 1–20` / `Parts 4–7 · ch 21–42` / `Parts 8–9 · ch 43–50`.
8. **Update `roadmap.mdx`** to the §6 milestone remap below.
9. **Verify:** `npm run build`, `npm test`, `grep -rn '—' web/content/docs/` empty,
   full odoolings suite green ch05-ch34 (the renamed keys), and a link check that no
   MDX references a chapter number that no longer exists. Spot-check the four written
   chapters by reading them end to end: the mixed-reference step is where a silent
   error would hide, and this repo's own audit history says cross-references are the
   most common defect class.

Work in milestones; each ends in a deployable state. The author reviews each milestone
before the next starts. **Cadence assumption:** the author studies/writes ~1–2 h on
weekdays; agent prepares scaffolding, drafts, and verification scripts; the author
executes every hands-on section personally (that's the learning).

### M0 — Bootstrap (½ day) — ✅ done 2026-07-10 (then rebuilt on the D3 stack, see changelog)
- [x] Create GitHub repo `odoo-tutorial` with structure from §4.1.
- [x] Site configured (Next.js + Fumadocs after the D3 pivot): nav skeleton (all 40
      chapters as stubs), callouts, mermaid, quizzes, progress, odoolings.
- [x] GitHub Actions: deploy to Pages on push. Verify live URL.
- [x] `code/docker-compose.yml` for Odoo 19 + Postgres 16, tested end-to-end
      (fresh clone → `docker compose up` → login → install an app).
- **Acceptance:** live site with skeleton; `docker compose up` works on a clean machine.

### M1 — Part 0 + Part 1 (week 1) — ✅ done 2026-07-13
- [x] Chapters 1–4 following the §4.3 template (quizzes included; ch4 hands-on
      executed for real on odoo:19).
- [x] Chapters 5–7 written 2026-07-13, hands-on executed for real (ch05/ch06
      odoolings checks green; OCA clone measurements in ch7 are live data).
- [x] Original diagrams (mermaid) for architecture & request lifecycle.
- [x] Glossary started (every jargon term used gets an entry the day it appears).
- [x] Sidebar completion checkmarks (§4.4) as M1 wrap-up (done 2026-07-13:
      `ChapterItem` sidebar override reading the existing localStorage progress).
- **Acceptance:** a Python dev with no Odoo background gets a running dev env and
  understands the ecosystem map, verified by the author actually doing it.

### M2 — Part 2 (weeks 2–3) — the heart of the tutorial
- [x] **Gate: author signs off on the §5.5 LibreFleet blueprint** (2026-07-13).
- [x] Chapters 8–15 with checkpoints `ch08`–`ch15` committed and installable, each
      registering odoolings checks; exercises graded per §5.6; break-it labs where
      instructive (ch15 done 2026-08-02).
- [x] Every chapter's Verify section includes at least one `odoo-bin shell` or psql
      inspection so readers see what the ORM does under the hood.
- [x] Quiz persistence + per-part mastery, `<Term>` tooltips, predict-the-output
      quiz variant (§4.4); Part 2 review quiz (done 2026-08-02).
- [x] `boss2` challenge: spec page + odoolings check set + solution checkpoint (done 2026-08-02).
- **Acceptance:** LibreFleet core installs from any checkpoint; author completes
  `boss2` from the spec alone with odoolings green.

### M3 — Part 3 (week 4) — ✅ chapters done 2026-08-02
Rescoped 2026-08-05 by D12/D13: M3 was "Parts 3 & 4 (ch 16-28)", but the old Part 4 is
now Part 6 and moved to M5, so M3 is just Part 3.
- [x] Chapters 16–20 + checkpoints, each registering odoolings checks.
- [ ] `boss3` challenge; Part 3 review quiz.
- **Acceptance:** author clears `boss3`; the view suite works on the service-order
  pipeline.

### M3.5 — The D13 renumber (½ day, blocking) — NEW
- [ ] Execute §5.8's runbook end to end, as one verified PR.
- **Acceptance:** full odoolings suite green on the renamed keys (ch05-ch34), site
  builds, `npm test` passes, and no MDX references a chapter number that no longer
  exists. **Nothing in M4 may start until this lands.**

### M4 — Parts 4 & 5, the functional act (weeks 5–7) — NEW (D12)
- [ ] `odoolings snapshot` / `odoolings diff` (§4.4) built and used from ch21 on. This
      comes first: every functional chapter's "Read what it did" movement depends on it.
- [ ] The shared `functional` demo database recipe, documented once in ch21 and reused:
      `-d functional -i <apps> --with-demo`.
- [ ] Chapters 21–30 per §5.3, each with odoolings checks that verify *business state*
      (confirmed order, quant at a location, `payment_state == 'paid'` with reconciled
      lines, `mrp.production` done) rather than module structure.
- [ ] `boss4` (end-to-end business run) + its two stretch builds (recurring maintenance
      billing, commission calc) + Parts 4/5 review quizzes.
- [ ] Glossary: the functional vocabulary block (journal entry, reconciliation, quant,
      BoM, fiscal position, payment term, COGS, AVCO/FIFO, MO, RFQ, UoM, pricelist).
- **Write order if the whole part cannot be done at once** (highest unblocking value
  first, because Part 6 depends on them): ch21, ch22, ch27, ch28, then ch23-26, ch29-30.
- **Acceptance:** the author can run the full order-to-cash and procure-to-pay flows
  from memory in a fresh demo DB, explain what each posted to `account.move` and
  `stock.move`, and clears `boss4`.

### M5 — Part 6, business logic (weeks 8–10)
- [ ] Chapters 31–38 (ch31-34 already written as the old ch21-24) + checkpoints; test
      suite grows with ch38 and CI (`ci.yml`) starts running module tests on every push.
- [ ] `boss5` (was `boss4`); Part 6 review quiz.
- [ ] Revisit ch32/ch36/ch37 once Parts 4-5 exist: each gains a short prerequisite
      pointer and can drop any hand-waving it currently does about Sales/invoices.
- **Acceptance:** CI green; PDF report renders; portal page works logged-in and
  logged-out; ≥ 15 meaningful tests; author clears the boss.

### M6 — Part 7, frontend (weeks 11–12)
- [ ] Chapters 39–42; OWL dashboard functional; `boss6` (was `boss5`); Part 7 review quiz.
- [ ] ch42 absorbs the POS functional context (§5.3), so POS arrives as an OWL case
      study rather than a Part 4 chapter.
- **Acceptance:** custom widget + client action work with `--dev=all` hot reload.

### M7 — Parts 8 & 9, the expert tier (weeks 13–15)
- [ ] Chapters 43–50; pre-commit adopted repo-wide; the extracted OCA-style module
      passes `pre-commit run -a` and has readme fragments.
- [ ] Author makes one real (small) OCA contribution as the ch45 exercise.
- [ ] ch47 interactive migration checklist (§4.4).
- **Acceptance:** the extracted module would plausibly survive an OCA review;
  migration exercise completed against a real 18.0 module (18→19).

### M8 — Polish & launch (week 16)

> **Live status of the two running sweeps (updated 2026-08-17).** Both are partly done;
> pick either up cold from here.
>
> | Sweep | Done | Left |
> |---|---|---|
> | Screenshot backfill | ch4, ch21-28 | **ch29** (1 image, vs 3-4 in its neighbours) |
> | Reader-clarity pass | ch12-24 | **ch25-30**, then a decision on ch31-50 |
>
> The clarity pass is the newer of the two and is described in its own M8 item below.
> ch30 was written after the screenshot policy changed and carries its own images by
> §6 rule 4b, so it is not part of the backfill; it *is* in scope for the clarity pass.

- [ ] **Backfill screenshots for the chapters written before the policy changed**: ch4 and
      ch21-29, which shipped with no images because the pipeline was broken until
      2026-08-05 (see the changelog). Chapters from ch30 on carry their own, per §6 rule
      4b, so this is a one-off catch-up rather than a standing task. Treat it as a
      correction exercise whose by-product is images: the browser found five wrong UI
      claims the first time it was pointed at a written chapter.
      Decide once, before capturing: viewport size, light or dark, and how to caption
      screens whose sequence numbers and dates a reader cannot reproduce. **The real
      payload is not the pictures, it is catching wrong UI claims:** ch27 shipped
      `Accounting → Configuration → Chart of Accounts` for two chapters before ch29 found
      that Community's app is called *Invoicing* and puts those menus a level deeper.
      Everything verified through the database was right; the thing inferred about the
      interface was not. Assume more of those exist.
      **The image pipeline is already proven end to end (2026-08-05), so do not
      rediscover it:** images live in `web/public/screens/…` and are referenced from MDX as
      `/screens/…`; markdown `![]()` works and Fumadocs styles it (`rounded-lg`,
      responsive `sizes`). The trap that had to be fixed first is in the changelog: the
      export needed `images: { unoptimized: true }`, and `tests/export-preview` now guards
      it. Screenshots arrive as **jpeg at 1568px wide** from the browser tool, so check
      whether small UI text survives the compression before committing to a whole pass;
      re-crop with the `zoom` action for anything fiddly like a distribution table.
- [ ] **Reader-clarity pass, chapter by chapter** (started 2026-08-16 after the author
      read the tutorial as a learner and kept getting stuck). **Done: ch12-24. Left:
      ch25-30, then decide whether ch31-50 needs it.**
      This is not a proofread. It hunts seven specific defects, and the two that matter
      most are the ones a normal review misses:
      **steps that cannot be followed at all** (ch22's hands-on told the reader to press
      Confirm before the diff that had to precede it; ch23 sent them to search Apps for
      `sale_loyalty`, which is `auto_install` with no `application` key so the search
      returns nothing; ch14 said "with `ValidationError` imported" when the ch13
      checkpoint has no such import), and **claims the chapter contradicts elsewhere**
      (ch19's Gotcha demanded root declarations that its own Concepts section, code and
      screenshot all show are unnecessary).
      The others: unexplained jargon at first use, one sentence cramming several edits,
      assumed knowledge, a command named but not shown, and content deferred to the
      checkpoint that the reader needs right now.
      **Method that worked, reuse it.** One agent per chapter reading the chapter, the
      previous chapter (so it does not flag what was already taught) and the checkpoint,
      each finding carrying exact verbatim `old_string`/`new_string`; then a skeptic pass
      over every finding before applying. Do not skip the skeptic: it caught an agent
      repeating a chapter's own wrong module count, and another asserting a view-typing
      rule that ch16's extension view disproves. Verify every claim against the running
      container, and treat "never ship unexecuted code" as binding on the fix text too,
      no invented output.
      **Beware shared-database drift**, the same trap that produced the stale "157
      accounts" and "seven journals" figures: the `functional` database on a working
      machine is *ahead* of what an in-order reader has, because later chapters install
      more apps into it. ch22 needed a pristine chapter-21-state database built from
      scratch to get the right answer (three bridge modules, not the four a
      fully-worked-through database reports).
- [ ] Full read-through edit; consistency pass on admonitions and footers.
- [ ] Landing page with learning-path graphic; "how to use this tutorial" guide.
- [ ] README, CONTRIBUTING, licenses; announce (LinkedIn, r/Odoo, OCA Discord —
      author's call).
- [ ] Post-launch backlog issue: "Odoo 19/20 delta pass" (schedule after Odoo 20
      ships ~Oct 2026).

### Standing rules for the agent
1. **Never ship unexecuted code.** Run every snippet in the Docker env; paste real
   output, not imagined output.
2. **Verify version-sensitive facts** against the 19.0 docs before writing; add an
   "On Odoo 18 this differs" box when the 18.0 docs differ (readers may be on older
   client projects).
3. **Original prose and images only** (see §1.4). Link, don't copy.
3b. **Style: natural, conversational prose; no em dashes** (author preference,
    2026-07-13). Use commas, colons, parentheses or a new sentence instead. En
    dashes in numeric ranges (`1–7`) are fine.
4. Small PRs per chapter; the author reviews and *manually re-executes* each Hands-on
   before merge — this is the learning loop, do not optimize it away.
4b. **Screenshots are part of chapter work** (author's decision, 2026-08-05; an earlier
    version of this rule deferred them all to M8, which was the agent over-reading
    "add them at the end" and is now corrected). Capture them from the real instance
    with the Chrome tools while writing the chapter. Five things must be right, all
    learned the hard way on 2026-08-05, see the changelog:
    - The agent **cannot log in**; the author signs in to `localhost:8069` once and the
      Chrome profile keeps the session.
    - **Pin the viewport** (`resize_window`) before capturing. The tool returned
      1568x739 and 1447x850 in the same session, and unpinned screenshots will not
      match each other.
    - `images: { unoptimized: true }` must stay in `next.config.mjs`, or every image
      404s in production while the build stays green. `tests/export-preview` guards it.
    - Files go in `web/public/screens/…`, referenced from MDX as `/screens/…`. Plain
      markdown `![]()` works and Fumadocs styles it. **MDX has no `<http://…>`
      autolinks**, it parses them as JSX; use `[text](url)` or a code span.
    - **Check every UI claim against the screen, not against `ir.ui.menu`.** Walking the
      menu tree shows what exists, not what a user sees; the client filters by
      `group_ids`, and `with_user()` does not. Expect a handful of wrong claims per
      chapter: one screen produced four on 2026-08-05.
5. Maintain `docs/glossary.md` and the §5.4 checklist continuously.
6. If the author's team reveals internal conventions (their Docker platform, CI,
   project template), prefer those in "In the field" boxes — ask, don't guess.

---

## 7. The Author's Parallel Learning Plan (how to use this while onboarding)

- **Before onboarding starts:** M0 + M1. Also watch, at 1.5×: the official Odoo
  YouTube "developer" playlists and 2–3 OCA Days technical talks (e.g. contribution
  workflow talks) — note anything worth linking from chapters.
- **Weeks 1–3 of the job:** M2. This aligns with typical integrator onboarding
  (first bugfixes on models/views). Bring questions from real tickets back into
  "Gotchas" sections — that is what will make this tutorial better than the docs.
- **Weeks 4–8:** M3–M4 while taking on real tasks.
- **Month 3:** M5 — and ask the team for a real OCA PR to make; Camptocamp
  colleagues review OCA PRs constantly and will gladly point you to a good first one.
- **Retention tactics:** end-of-part self-tests (rebuild from memory), teach-back
  (explain one concept per week to a colleague or in a blog-style chapter intro),
  spaced review of the glossary.

### 7.1 The side-by-side walkthrough (author's decision, 2026-08-05)

From ch1 onward the author and the agent go through every written chapter **together**, in
one session per batch: the author learns the material and does the hands-on himself, the
agent drives Chrome alongside him, verifies every claim on screen, captures the
screenshots, and fixes the chapter as they go. This replaces the separate "author
re-executes later" pass (§6 rule 4) rather than adding to it, and it is the same principle
§7 already states about bringing real-ticket questions into Gotchas: **the author's
confusion is the single most valuable input this tutorial can get, and it is the one thing
the agent cannot generate for itself.**

The loop per chapter:

1. Author reads the chapter and says where it stops making sense. That is a defect, logged
   even when the instructions are technically correct.
2. Author runs the hands-on himself. The agent watches the database over `odoo shell` /
   `odoolings diff` and confirms the state matches what the chapter claims.
3. Agent verifies every UI claim **on screen**, not against `ir.ui.menu`, and captures the
   screenshots that earn their place.
4. Both note improvements: wrong claims, thin explanations, weak quiz questions, missing
   diagrams, places an interactive component would beat prose.
5. One PR per chapter. Findings go in the §10 changelog the same session, because a long
   walkthrough will outlive the agent's context window and anything not written down is
   lost.

**Environment: fresh as we go** (author's decision, 2026-08-05). Each chapter is walked
against the state *its own reader* would have, not our accumulated authoring state, because
a screenshot of the wrong state teaches the wrong thing. Staged so the regression net
survives:

| When | Do | Recoverable because |
|---|---|---|
| ch1-3 | nothing, no database is needed | |
| ch4 | `dropdb tour`, author creates it from the database manager as the chapter instructs | it is only `crm` + `sale_management` + demo |
| ch8 | move `code/addons/librefleet` aside, `dropdb tutorial`, rebuild the module chapter by chapter | `code/checkpoints/ch34/librefleet` is **byte-identical** to the workspace (verified) |
| ch21 | `dropdb functional`, rebuild by walking ch21-29 | the chapters themselves rebuild it |

Deliberately **not** a `docker compose down -v` up front: that would take `functional` with
it, and the ch21-29 checks are the only regression net we have while editing the front of
the book. Drop individual databases instead, and keep the volumes. Take `pg_dump -Fc`
backups of all three before the first drop; they are insurance, not the plan, since
everything above is reproducible from the repo.

One consequence worth accepting rather than fixing: with other databases still present, the
database-manager screen a ch4 reader sees will list them. Cosmetic, and not worth
engineering around.

Rules that keep it working:

- **One driver at a time.** The agent and the author sharing a browser will diverge; say
  who has the wheel. If the author wants to click, the agent pauses.
- **No modal dialogs.** A JavaScript `alert`/`confirm` blocks the Chrome extension
  completely and the agent goes deaf until it is dismissed by hand.
- **Do not resize the window mid-chapter**, or the screenshots will not match each other.
- The agent still **cannot log in**. Author signs in once per session.
- **Model:** Sonnet is enough for the walk-and-capture; escalate to Opus for a chapter
  where being confidently wrong is expensive (taxes, valuation, security, performance).

On "more interactive": the site already has `Quiz`, `Mermaid`, `Term` (glossary tooltips),
`Mastery`, `Card`/`CardGrid`, `Icon` (added 2026-08-09, see §10), the progress pill and
mark-complete. Prefer using those harder before building anything new. If the walkthrough
shows a real gap, the two ideas already parked in §10 are the predict-the-output quiz
variant and quiz persistence; treat any *new* component as its own scoped piece of work,
not something to slip into a chapter PR. `Icon` is itself the example of that rule
working: flagged mid-walkthrough rather than added unilaterally, scoped and built as its
own piece before chapter work resumed.

**Where `Icon` earns its place, going forward:** "Further reading" bullets and any
source-type table ("Where the knowledge lives" in ch2 is the model) get a leading icon
picking the *kind* of thing being linked (docs, source, video, forum, store...), applied
chapter by chapter as each is walked rather than retrofitted en masse across the 26
chapters not yet touched. Beyond that, use it sparingly: a `Card` eyebrow, a status marker
next to Gotchas. It is not a replacement for the ⭐-grading convention on Exercises, and it
is not a reason to add a glyph to every bullet point in the tutorial.

## 8. Canonical Link Index (seed list for chapter "Further reading" sections)

- Official docs (19.0): developer home, Server framework 101, ORM reference, view
  reference, OWL tutorials, testing, QWeb reports, controllers —
  `https://www.odoo.com/documentation/19.0/developer.html`
- Official docs (18.0) for "On Odoo 18 this differs" boxes:
  `https://www.odoo.com/documentation/18.0/`
- Odoo source: `https://github.com/odoo/odoo` (branch `19.0`)
- OCA: `https://github.com/OCA` · contribute guide:
  `https://www.odoo-community.org/get-involved/contribute` · guidelines repo:
  `OCA/odoo-community.org` · `OCA/maintainer-tools` · `OCA/OpenUpgrade` ·
  Runboat: `https://runboat.odoo-community.org`
- OWL: `https://github.com/odoo/owl`
- YouTube: @Odoo (official) and @OdooCommunity (OCA Days talks)
- pre-commit / pylint-odoo: `OCA/pylint-odoo`, OCA addons repo template

## 9. Open Questions for the Author (answer before M1)
1. ~~Monorepo OK, and repo name?~~ **Answered 2026-07-10: monorepo, `odoo-tutorial`.**
2. ~~Capstone domain sign-off~~ **Answered 2026-07-10: LibreFleet confirmed.**
3. Will your team confirm the Odoo version your projects run? If most client work is
   on 16/17, add a short "working on older versions" appendix.
4. ~~Public from day 1?~~ **Answered 2026-07-10: public from day 1.**
5. ~~Sign off on the §5.5 LibreFleet blueprint (models/fields/security)?~~
   **Answered 2026-07-13: approved as written. M2 unblocked.**
6. ~~Add component architecture and the OCA connector vocabulary? (raised 2026-08-17)~~
   **Answered 2026-08-18: yes, built as a root-level appendix, `appendix-components.mdx`,
   no chapter renumbered. The reasoning below stands as the record of why.**
   The author's Odoo manager asked whether he knew "adapters / component architecture",
   both generally and as the named framework. The tutorial currently answers neither: the
   only occurrence of "component framework" in 50 chapters is OWL, and `connector`,
   `component`, `Backend Adapter`, `Mapper` and `Binding` appear nowhere.
   **Recommendation: yes, as ONE appendix, and deliberately not as an inserted chapter.**
   Reasoning and the proposed spine are in the §10 entry for 2026-08-17. The decision the
   author actually has to make is placement, because inserting into Part 8 renumbers ch44
   to ch50, and §10's own D13 record shows what that costs: it silently falsified twelve
   references and broke `main`. An appendix costs nothing to add and nothing to undo.
   Blocking question for the author: is this expected knowledge for the team's client
   work (Camptocamp maintains `component` and `connector`), or is it specialist knowledge
   that belongs in a follow-up rather than in the tutorial's spine?

---

## 10. Changelog (running log — update whenever a decision or milestone changes)

### 2026-08-18 (later) — ch21-26 retrofitted onto the `<Steps>`/`<Step>` house style

Reader-reported gap: chapters 21-26 (all written 2026-08-05, before the 2026-08-09 ch1-10
review made `<Steps>`/`<Step>` house style) still numbered their Hands-on with plain
`#### N. Title` headings under `### Movement 1/2` sub-headers. The ch1-10 retrofit never
swept forward into Part 4, so the gap sat there until a reader jumped straight to ch21 and
noticed the UI was inconsistent with every chapter before and after it.

Fixed by wrapping each chapter's Hands-on in `<Steps>`, one `<Step>` per former `#### N.`
item, dropping the number from the heading text (the component supplies it) exactly as
ch42 first proved works for a Movement-style Hands-on. The `### Movement N: ...`
sub-headers are gone; where they carried chapter-specific framing rather than the generic
"run the flow, then read what it did" (ch25's movements run in reverse, ch26's first
movement builds the recipe as well as running it), that framing moved into the paragraph
immediately above `<Steps>` instead of a header. ch27-30 still have the same gap and are
unfixed for now, scope was deliberately capped at Part 4.

Verified: `npm run test:ci` green, and ch21/ch25 eyeballed in the browser (localhost:3000)
to confirm the numbered-circle rendering matches ch20's.

Remaining, tracked here rather than fixed silently: **ch27-30 (Part 5) have the identical
gap** and should get the same treatment in a follow-up pass.

### 2026-08-18 — the component appendix, built (§9 q6 answered yes)

Written as `web/content/docs/appendix-components.mdx`, a root-level page slotted into
`meta.json` between Part 9 and the glossary. **No chapter renumbered, no checkpoint
invented, no odoolings check added.** Four glossary entries added (component (OCA),
collection, backend adapter, WorkContext).

**The hands-on is real and was run here before it was written.** That mattered, because it
turned up two things the proposal had guessed at:

- **`component` installs on Odoo 19 with no connector at all.** `depends: ["base"]`,
  version 19.0.1.0.1, loaded on a scratch database in 0.05s. The proposal's claim that
  components can be taught standalone holds up, which is what keeps this to one appendix.
- **It needs `cachetools`, and the `odoo:19` image does not ship it.** A hand-run
  `pip install --break-system-packages` inside the container works but dies with the
  container, so that is now a Callout rather than a footnote. Any OCA module with
  `external_dependencies` has the same tax, and it is the first real friction on leaving
  core-only Odoo.

The demo is two backends, two adapters, one call site, forty lines:

```text
acme.backend     -> acme.parts.adapter     ACME REST /parts/OF-102
zenith.backend   -> zenith.parts.adapter   Zenith SOAP getPrice(OF-102)
```

Identical `work.component(usage="backend.adapter")` both times. That single output is the
argument the whole appendix exists to make, and there is no way to write it with
`_inherit`.

A happy accident worth keeping: installing the demo emits Odoo's own
"models have no access rules" warning for the two collection models, which lands chapter
10's lesson exactly where the appendix needs to explain that collections *are* models and
components are not. Real output, better than any prose about the distinction.

Structure follows §4.3 with two deliberate omissions, both because this is an appendix
rather than a chapter: no checkpoint (all forty lines are inline) and no `odoolings check`
(the tutorial's checker keys on `chNN` and inventing an appendix key would be worse than
leaving the Verify section to prove itself from the shell).

### 2026-08-17 (later) — proposal: an appendix on component architecture (now built, see above)

Raised by the author, whose Odoo manager asked whether he knew "adapters / component
architecture", both as a general design idea and as the specific thing. Recorded as an
open question rather than acted on, because it changes the syllabus and the syllabus is a
signed-off decision.

**The gap is real and total.** Grepped all 50 chapters plus the glossary: the only match
for "component framework" is OWL, and `connector`, `component`, `Backend Adapter`,
`Mapper`, `Binding` and `WorkContext` appear nowhere at all.

**Two different questions hide inside the manager's one.** Worth separating, because the
tutorial should answer both and they have different answers:

1. *Component architecture as a general idea*: build a system from pluggable units that
   are looked up at runtime by contract, rather than wired in by inheritance. **Odoo's
   server side does not work this way.** Its extension model is a module dependency graph
   plus ORM inheritance merged into one per-database registry, which is class *merging*,
   not lookup. That is a genuinely interesting answer to give in an interview, and the
   tutorial has taught every piece of it (ch31's three inheritance types, ch3's registry)
   without ever naming the contrast.
2. *The named framework*: OCA's `component` module, written by Camptocamp, alive on the
   19.0 branch of `OCA/connector`. Components are resolved at runtime by `_usage`,
   `_collection` and `_apply_on`, which is what lets several backends carry their own
   implementation of the same operation side by side. An adapter, per the connector docs,
   is the component with "a common interface to speak with the backend", translating
   search/read/write into the backend's protocol.

**Where inheritance runs out, with core's own workaround as the hook.** The honest reason
components exist is that `_inherit` is global and singular: you cannot have a Magento
export and a Prestashop export of `res.partner` coexist and be chosen per record. Core
hits this too and solves it by building a method name out of a string, verified in
`delivery/models/delivery_carrier.py`:

```python
if hasattr(self, '%s_rate_shipment' % self.delivery_type):
    res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
```

The class docstring even documents that as the extension protocol ("extend the selection
of the field `delivery_type` with a pair `<my_provider>_rate_shipment`"). That is a
registry with no registry, and it is the perfect way in: the reader sees the problem in
core before meeting the framework that solves it properly.

**The reader has already built one and does not know it.** ch40 and ch41 register into
`registry.category("fields")` and `registry.category("actions")`, look-up-by-string with
late binding, which is a component architecture in everything but name. Naming it
retroactively costs one paragraph and makes the whole idea land.

**Why one appendix and not four chapters.** The `component` README states it "can be used
without using the full Connector", which is the unlock: components can be taught with a
small standalone example, no Magento instance, no `queue_job`, no binding tables, no new
environment axis. Teaching the full connector would need several chapters and a second
addons stack, which is a different-sized commitment.

**Why an appendix and not an inserted chapter.** Inserting into Part 8 renumbers ch44-50,
and this plan already records what that costs: the D13 renumber silently falsified twelve
"Part N" references and the ch45→ch46 stub bump broke `main`. Numbering also reaches
`code/checkpoints/chNN`, `odoolings.py`'s `CHAPTERS` keys and `web/public/screens/chNN-*`.
An appendix has none of that blast radius. If the author wants it numbered, ch51 is the
cheap version.

Proposed spine, if approved: the general idea and the inheritance contrast; core's
string-dispatch workaround; the retroactive naming of the JS registries; `component`
standalone with `_usage`/`_collection`/`_apply_on` and `WorkContext`; then the connector
vocabulary (Backend, Binding, Mapper, Adapter, Synchronizer, `queue_job`) as recognition
rather than hands-on. Nothing written yet, and nothing renumbered.

### 2026-08-17 — reader-clarity pass, ch14-24 (91 fixes, PRs #119-129)

The author read the shipped tutorial as a learner rather than as its writer, got stuck
repeatedly, and asked for chapters 14-24 to be made followable. That produced a new
standing M8 item (see §6), and it is worth recording *why* it is a separate exercise
from the read-through edit already on that list.

**A written chapter that passes every check can still be impossible to follow.** All 50
chapters were verified: code executed, output pasted from real runs, odoolings green.
None of that catches an instruction pointing at a control that is not on screen. The
worst finds were not typos:

- **ch22's hands-on contradicted itself.** Step 4 says press Confirm; step 5's diff is
  explicitly the one taken *before* confirming; step 6 then says "snapshot again, press
  Confirm" on an order that is already confirmed. Following the chapter literally makes
  step 5's output unreachable. Also, the Customer field step 2 tells the reader to set is
  hidden by core while `type` is `lead` (`_compute_is_partner_visible`), and the dialog
  that actually attaches the partner was never mentioned.
- **ch23 had three dead ends**: an Apps search that cannot succeed (`sale_loyalty` is
  `auto_install` and declares no `application`, while the Apps action filters to
  applications), a shell that silently reports stale data after a browser change (one
  transaction at REPEATABLE READ, `sql_db.py:373`), and a `diff` with no snapshot to
  compare against.
- **ch14** said "with `ValidationError` imported at the top" when the ch13 checkpoint
  imports no such thing, so pasting the constraint gives `NameError` at import time.
- **ch19's Gotcha was simply wrong**, and contradicted its own chapter: it demanded root
  declarations for fields the card template already declares. The parser settles it, the
  `t-name` branch returns `undefined` and `visitXML` only stops descending on an explicit
  `false`, so nested `<field>` nodes *are* collected.
- **ch20** told the reader to "Update" a wizard view file that does not exist yet, and
  never told them to delete the `_compute_totals` its own checkpoint has removed.

**Two process findings worth keeping.**

*The skeptic pass is not optional.* Agents audited each chapter and proposed exact
replacement text; a second pass checked every finding before it was applied. It caught an
agent faithfully reproducing a chapter's own wrong claim (ch22's installed-module count)
and another asserting that every view so far was typed from its arch root, which ch16's
`inherit_id` extension disproves. Roughly one in fifteen findings needed correcting, and
those would have shipped as confident, plausible errors.

*Shared-database drift bites again.* This is the third time (after "157 accounts" and
"seven journals"). A working machine's `functional` database has been through chapters
that the reader has not, so it answers questions differently: it reported four bridge
modules overriding `_action_confirm` where an in-order reader has three, `delivery`
having arrived via `website_sale` in ch42. The fix was to build a pristine
chapter-21-state database and quote *that*. **Rule: before quoting any count, list or
"which modules are installed" output in Parts 4-5, ask which chapter the reader is
standing in, not what your database says.**

The related-but-narrower sweep of 2026-08-16 (inline the real command instead of a bare
"(chapter N)" backref, show code instead of "see the checkpoint") is folded into the same
M8 item; it covered ch12-50 for those two defects only.

### 2026-08-12 (the last of the writing phase) — ch50 written, the tutorial's 50th and final chapter

Career map: reading core source effectively (a synthesis of techniques the tutorial
already used on the reader across 49 chapters, named explicitly rather than taught
fresh), official certification with real numbers pulled live from Odoo's own
listing (120 questions, 90 minutes, 70% pass, negative marking for wrong answers,
version-specific per major), OCA Days vs Odoo Experience, and the October rhythm
this project's own §9/§10 already commits to (no LTS, one major a year, re-verify
every October), turned into a checklist the reader applies to themselves via the
new `<MigrationChecklist>` component chapter 47 introduced.

**No LibreFleet code, Checkpoint "none"**, matching the closing tone: the real
verification is whatever the reader already built across chapters 8-49, not
anything new this chapter adds.

**§5.4's coverage checklist, flagged "verify before calling the syllabus done,"
was actually run, not rubber-stamped.** Grepped every dev-track and functional
item against the real chapter content (sample: `recordset` in 16 files,
`_read_group`/`formatted_read_group` confirmed live in ch48, `sudo(` in 6 files,
`HttpCase`/tour in 8 files). Two genuine, confirmed gaps turned up against the
D12 functional list: **eCommerce order → sale.order** (ch42's survey covered
Website Snippets and POS but never an actual `website_sale` checkout) and
**lock dates / period close** (zero mentions of `fiscalyear_lock_date` or
`period_lock_date` anywhere in Parts 4-5). Put to the author as an explicit
choice (defer as known follow-up, or backfill now); **author chose: backfill
both before shipping ch50.**

- **ch27 gained a real lock-dates section.** `res.company`'s five real lock
  fields confirmed live (`fiscalyear_lock_date`, `tax_lock_date`,
  `sale_lock_date`, `purchase_lock_date`, `hard_lock_date`, the last one new in
  19). A genuine, unplanned finding while testing: setting the broad locks
  (`fiscalyear_lock_date`/`hard_lock_date`) on `functional` failed outright with
  a real `RedirectWarning`, "unreconciled bank statement lines in the period you
  want to lock", Odoo checking the books are actually clean before it lets you
  lock them, which is precisely ch27's own opening line ("a month that will not
  close") firing for real rather than as a turn of phrase. `sale_lock_date`
  doesn't hit that check, so it became the hands-on: locked a real posted
  invoice's period, called `button_draft()`, got the real `UserError` ("You
  cannot add/modify entries prior to and inclusive of: Sales Lock Date"), reset
  the lock afterward. New Gotcha, new Quiz question, glossary +1 (`lock date`).
- **ch42 gained a real eCommerce checkout.** Installed `website_sale` on
  `functional` for real, enabled the Wire Transfer payment provider (needs no
  external account or fake credentials, the honest choice for a hands-on), and
  placed a genuine order through the actual storefront via the Chrome browser
  tools: picked a real product (Customizable Desk, White/Steel variant), real
  cross-sell upsell dialog, real cart, real checkout, real confirmation page
  ("Thank you for your order. Order S00047"). Two new real screenshots
  (`ch42-shop-product-variants.jpg`, `ch42-shop-order-confirmation.jpg`). Read
  the resulting `sale.order` from the shell: `website_id` set, real order line
  with the chosen variant, a real linked `payment.transaction`. **Genuine
  unplanned finding**: the order's `state` stayed `'sent'`, not `'sale'`,
  because a manual payment method can't confirm itself, a human has to see the
  wire transfer land first, `payment.transaction.state = 'pending'` confirmed
  directly. New Concepts subsection, new Hands-on steps, new Gotcha, new Quiz
  question, new odoolings checks (`website_sale is installed`,
  `a real order was placed through the online store`, both red-tested before
  the checkout, green after), glossary +1 (`payment provider`).
- Both enrichments re-verified: `npm run test:ci` green, `python3 odoolings.py
  check ch42 --db functional` green (6/6 including the two new checks).

§5.4's checklist now reads all ✅ across both lists, each of the two backfilled
items dated so a future reader of this plan can see they were a deliberate
later addition, not part of the original chapter.

### 2026-08-12 (later yet still) — ch49 written: deployments & ops, concept-level as planned

Genuinely concept-level, per the plan's own framing, unlike ch47/48: no LibreFleet
code changed, Checkpoint "none." Still held to the same "never ship unexecuted
code" bar, just applied to real CLI commands rather than a code refactor:

- **Real flags and defaults pulled straight from `odoo server --help`**, not
  memory: `--workers` (default 0, prefork disabled), `--max-cron-threads`
  (default 2), `--limit-time-cpu`/`--limit-time-real`/`--limit-memory-soft`, and
  the `--proxy-mode` warning text quoted verbatim.
- **`odoo db dump` run for real** against a scratch database (`test_ch39`,
  never `tutorial` itself): confirmed the zip actually contains `dump.sql`,
  `filestore/`, and `manifest.json` together by opening it with `zipfile`, not
  assumed from the `--help` text.
- **Full backup/restore round-trip verified**: `db dump` → `db load` into a
  freshly-named database, confirmed it exists in `psql -l`, then cleaned up.
- **`odoo neutralize` run for real** against a throwaway `db duplicate`, and its
  actual effect confirmed directly, not just described: `ir_config_parameter`'s
  `database.is_neutralized` flips to `true`. Throwaway database dropped
  afterward.
- **Multi-company section reuses ch27's own already-verified findings**
  (company-dependent `account.account.code` returning `False` silently across
  companies, bare `search([])` crossing company boundaries) rather than
  re-deriving them, since they're already real and on the record.
- odoo.sh vs Docker platforms and the "why yearly October releases..." framing
  (already ch1/ch47 territory) kept deliberately general: no odoo.sh account to
  verify specifics against, so the comparison stays at the level that's
  actually true rather than guessing at UI details.

**No odoolings check, no glossary additions** (`filestore` already existed from
an earlier chapter, checked for consistency, none needed). Housekeeping:
export-preview test's stub route bumped ch49 → ch50, the tutorial's last chapter.

### 2026-08-12 (later yet) — ch48 written: performance, measured against real query counts

Every number in this chapter is real, captured via `--log-sql` (`odoo.sql_db:DEBUG`)
against the `functional` database's real 22 invoices / 63 lines (per §5.8's D12
note that ch48's N+1 examples live on `account.move.line`), not estimated:

- **N+1**: a `search()`-per-invoice loop measured at 22 real queries against
  `account_move_line`; the batched `in`-domain version at 1. Same 63 lines back
  either way.
- **Prefetch**: iterating 63 already-fetched lines and reading
  `line.move_id.partner_id.name` on each measured at 4 real queries against
  `account_move`/`res_partner` combined, not 126, proving the ORM's automatic
  batching, and showing exactly why the N+1 loop above defeats it (a fresh
  `search()` per iteration has no batch to prefetch into).
- **Batch `create()`**: 200 records, one-by-one vs one call, 0.501s vs 0.145s in
  this Docker environment, ~3.5x, explicitly caveated as a network-latency-bound
  gap that's much larger over a real app-server-to-Postgres connection.
- **Indexes**: added a real one LibreFleet was missing (`customer_id` on
  `librefleet.service.order`, which backs a portal record rule filtering every
  request). Confirmed via `EXPLAIN` that Postgres ignores it on our 4-row table
  (correct planner behavior) while using the structurally identical index on
  `account_move_line`'s 179 rows, an honest "the planner decides, not you" lesson
  rather than a fabricated benchmark on data too small to show one.
- **`_read_group`/`formatted_read_group`**: real signature and output captured
  live against `account.move.line`, cross-referencing ch27's live finding that
  pre-19 `read_group()` keys its count differently (`<field>_count`, not
  `__count`), now properly demonstrated here as ch27's own note promised.

**Real code change**: `customer_id = fields.Many2one(..., index=True, ...)` in
`librefleet/models/service_order.py`, version bumped, checkpoint `ch48` holds both
modules. ch13 and ch37 (both exercise `customer_id` directly) re-verified green
after the upgrade.

**No odoolings check**: an index's existence isn't observable over XML-RPC the way
a field or record is; `\d table_name` over psql is the real proof, same reasoning
as chapters 38/44/45.

**Glossary +1**: `prefetch`, inserted alphabetically between `portal` and
`price-included tax`.

### 2026-08-12 (even later still) — ch47 written: migrations, Part 9 opens

Opens Part 9. Built the planned interactive component (§4.4): `<MigrationChecklist>`,
a chapter-scoped localStorage checklist (`web/components/migration-checklist.tsx`),
registered in `mdx.tsx`, its own storage key rather than growing the shared
`Progress` schema since nothing outside this one chapter reads it. Verified live in
Chrome, not just `npm run build`: clicked two items, confirmed the count updated
("2 / 9 done") and survived a full page reload.

**The hands-on is a real, currently-unmigrated OCA module, not a fabricated one.**
Found via `OCA/server-tools`'s live migration tracking issue
([#3400](https://github.com/OCA/server-tools/issues/3400)): `html_text`, still on
`18.0` at the time of writing. Copied its real source into `code/addons/` (temporary,
never committed, removed and uninstalled again after), confirmed the exact real
failure mode first (`WARNING ... The module html_text has an incompatible version,
setting installable=False`), then bumped only the manifest version and reinstalled:
clean install, `0 failed, 0 error(s) of 3 tests`, zero code changes needed. Cross-
checked independently against a real, currently open PR migrating the same module,
[`OCA/server-tools#3653`](https://github.com/OCA/server-tools/pull/3653): its
`ir_fields_converter.py` diffed byte-identical against the `18.0` source. Two
independent confirmations of the same finding, both real.

**The deprecation-list table is entirely sourced from this project's own build
history**, not invented for the chapter: `_sql_constraints`→`models.Constraint`
(ch14), `t-esc`→`t-out` server-side only (ch39, with the OWL-side non-deprecation
nuance preserved), `--without-demo=all` (ch4), controller `type="json"`→`"jsonrpc"`
(ch37), plus `read_group`/`name_get`/`odoo.osv` from the original D1 baseline
research. Every row cites the chapter that actually hit it.

**No odoolings check**, same reasoning as ch38/ch44/ch45: the module install +
test-suite run in the terminal is the verification, and this chapter's subject
(an external OCA module) was never part of `tutorial`'s own state to begin with;
it was installed, proven, and uninstalled again within the same session.

**Housekeeping**: export-preview test's stub route bumped ch47 → ch48. No new
glossary entries (OpenUpgrade, migration tracking issues, and `[MIG]` are process
concepts already covered by existing `commit tags`/`OCA`/`PSC` entries).

### 2026-08-12 (even later) — ch46 written: LibreFleet's first real OCA-quality extraction, Part 8 done

The Part 8 capstone: extracted the ch35 maintenance-reminder feature (two
`librefleet.vehicle` methods, a cron, a `base.automation` rule) out of `librefleet`
into a brand-new standalone module, `librefleet_maintenance_reminder`, tooled to
ch44's pre-commit standard from day one (own manifest, own `development_status`,
own real generated README from real `readme/` fragments, own tests).

**Two real, non-obvious problems surfaced during the actual extraction, both now
documented as the chapter's central Gotchas**, neither anticipated before doing the
work for real:

1. **Removing a data file from `data: [...]` and re-upgrading does not delete the
   `noupdate="1"` records that file already created.** Verified via a direct psql
   query: after a clean, error-free `-u librefleet`, the four old records
   (`ir.cron`, two `ir.actions.server`, one `base.automation`) were still sitting
   in the database under `module='librefleet'`. Installing the new module with
   fresh xmlids for the same feature would have silently doubled the automation.
   The textbook Odoo fix (an XML `<delete>` tag) turned out to be a dead end here:
   it needs `base.automation`'s model in the registry at data-load time, which
   requires the `base_automation` dependency that this exact refactor correctly
   removes from `librefleet`'s manifest, a genuine chicken-and-egg. Resolved with
   one-time, explicit SQL, in dependency-safe order (verified for real, twice: once
   naively in the wrong order to confirm it fails, once correctly).
2. **A `tests/__init__.py` with no import silently discovers zero tests.** No
   error, no warning, `--test-tags` just reports "0 tests". Hit for real while
   writing this chapter (an empty `__init__.py` left over from `touch`), caught by
   noticing the suspiciously-empty test count rather than by any tooling flagging it.

**New odoolings checks, `ch46`**: module installed, `librefleet`'s manifest no
longer lists `base_automation` (read via `ir.module.module.dependencies_id` →
`ir.module.module.dependency`, confirmed real over XML-RPC), and exactly one
matching `base.automation` record exists (the anti-duplication check, the sharpest
test of whether the cleanup actually worked). All three verified red (before the
SQL cleanup, the duplication check would have failed) and green (after) for real.
Chapter 35's own pre-existing checks were re-run unmodified and stayed green,
which is the whole point: a correct extraction is invisible from the outside.

**Checkpoint shape changed**: `code/checkpoints/ch46/` now holds two module
directories (`librefleet/`, `librefleet_maintenance_reminder/`) side by side,
the first checkpoint to do this. Future multi-module chapters should follow the
same shape rather than inventing a new one.

**Housekeeping**: export-preview test's stub route bumped ch46 → ch47 (Part 9's
opener, `09-integrator-craft/47-migrations`). No new glossary entries (classic
extension, base.automation, noupdate are all already defined).

### 2026-08-12 (later still, once more) — ch45 written: contributing to OCA, and a scoping decision on "do a real contribution"

The plan's §5.3 line for ch45 calls for the chapter to walk through "a real first
contribution (docs fix or small improvement)." Before starting, asked the author
whether the agent should actually fork a live OCA repo under their GitHub identity
and open a real PR against it, since that's a public, externally-visible action
under the author's name, not something covered by standing authorization. **Author's
answer: write the mechanics, don't open a live PR** (option 2 of 3 offered). The
chapter presents the exact real commands, and the actual CLA-signing and PR-opening
are left as the reader's own action, the same pattern the site already uses for
login (the agent can't authenticate either; the author does that once, personally).

**Every command in the chapter is still verified, just not against a live OCA
repo.** Simulated the full fork → remote → branch-off-version-branch →
commit → rebase-on-upstream → push sequence locally, using two bare git repos
standing in for "upstream" (OCA/fleet) and "origin" (the fork), including a
genuine upstream-moved-forward-in-the-meantime scenario. Caught and documented a
real, current gotcha this surfaced: plain `git pull upstream 19.0` refuses to run
on current git ("divergent branches, specify how to reconcile"), `--rebase` is
the fix and matches what a one-commit PR should look like anyway.

**Real facts pulled from live sources, not memory**: the CLA is a signed
PDF/email process to `cla@odoo-community.org` (ICLA vs Entity CLA distinction),
not a bot-comment flow, confirmed via `odoo-community.org/page/cla`. PR title
convention `[19.0][TAG] module: description`, the CI stack (pre-commit + tests +
Runboat + Codecov), and the review-etiquette bullets (thank the contributor first,
explain why not what, tag review type) came from `OCA/odoo-community.org`'s real
`CONTRIBUTING.rst` and the `get-involved/contribute` page. The three `/ocabot`
commands (`merge`, `rebase`, `migration`) came from `OCA/oca-github-bot`'s own
README.

**Housekeeping**: export-preview test's stub route bumped ch45 → ch46. No new
glossary entries (fork/upstream/CLA-mechanics are generic git/process concepts;
CLA, ocabot, Runboat, PSC, commit tags already exist from ch2/ch7/ch43).

### 2026-08-12 (later still, again) — ch44 written: pre-commit, ruff, pylint-odoo and readme generation, pointed at LibreFleet itself

Unlike ch43, a real hands-on chapter: wired up `.pre-commit-config.yaml`,
`.ruff.toml` and `.pylintrc` (a trimmed, real, hand-explained subset of
`OCA/fleet`'s actual config, verified live via `gh api`) and ran `pre-commit run
--all-files` against LibreFleet's real code for the first time ever, 36 chapters in.

**The findings were real, not staged.** First run: 15 ruff F401 hits on every
`models/__init__.py`-style registration import (fixed with a `per-file-ignores`
entry, the standard idiom, also present in `OCA/fleet`'s own `.ruff.toml`), two
genuine `translation-required` violations in `service_order.py`/`vehicle.py`
(`ValidationError` strings not routed through Odoo 19's `self.env._()`, fixed for
real in the actual source), and one `missing-return` false positive on
`_compute_access_url` (pylint-odoo's check can't distinguish a correctly-returning-
nothing compute from a forgotten `create`/`write` return; fixed via the documented
`no-missing-return` config escape hatch, not a code change).

**Manifest gained `development_status: Beta`** (declared, not left to the silent
default ch43 covered) and a version bump to `19.0.1.28.0`. **Wrote real
`readme/DESCRIPTION.md`/`CONTRIBUTORS.md`/`ROADMAP.md` fragments** and ran
`oca-gen-addon-readme` for real, producing a genuine generated `README.rst` with the
digest marker and badge row, same shape as the `fleet_vehicle_service_kanban`
example ch43 read.

**Verified for real**: `docker compose exec odoo ... -u librefleet --stop-after-init`
clean upgrade after all edits, `ir_module_module.latest_version` confirms
`19.0.1.28.0`, plus a spot-check of odoolings chapters touching the edited files
(ch09, ch35, ch37, ch41) to confirm nothing regressed. No odoolings check registered
for ch44 itself, same reasoning as ch38: the tool run is the verification, there's
nothing new in Odoo's own state to assert over XML-RPC.

**Housekeeping**: `web/tests/export-preview.test.mjs`'s hardcoded stub route bumped
ch44 → ch45. No new glossary entries: ruff/pylint-odoo/prettier/pre-commit are
general external tooling, and the glossary's scope (confirmed by grepping for
"Docker"/"git"/"psql", none present) is Odoo-specific jargon only.

### 2026-08-12 (later still) — ch43 written: OCA Safari opens Part 8

First chapter of Part 8, and like ch2 (which it deliberately doesn't repeat), a pure
research chapter: no `librefleet` code, no odoolings checks, Checkpoint "none". Ch2
already covers the OCA players map, repo-by-domain organization, PSC mention, and
branch-per-version with its own hands-on browse of `OCA/server-tools`; ch43 goes one
level deeper: finding modules via the OCA's own catalog
(`apps.odoo-community.org/modules`, reached from `odoo-community.org/apps`, distinct
from raw GitHub browsing and from the third-party `apps.odoo.com` store), judging
maturity via the `development_status` manifest key (Alpha/Beta/Production-Stable/
Mature, Beta the silent default) and the README badge row, and reading real OCA
source as study material.

**Case study: `OCA/fleet` next to LibreFleet.** Confirmed real via `gh api`: the
`19.0` branch holds `fleet_vehicle_service_kanban`, `fleet_vehicle_service_services`,
`fleet_vehicle_inspection`, and others, LibreFleet's direct real-world parallel. Read
two real manifests: `fleet_vehicle_service_services` declares no `development_status`
(confirming Beta as the true silent default), `fleet_vehicle_service_kanban` declares
`Production/Stable`. Read that module's generated `README.rst`: the
`oca-gen-addon-readme` warning comment plus `source digest: sha256:...` marker, and
the badge row (maturity, license, GitHub, Weblate "Translate me", Runboat "Try me").

**Glossary gained four terms**, all new jargon this chapter introduces and none of
which existed before: `CLA`, `development_status`, `ocabot`, `Weblate`. (`OCA`, `PSC`,
`Runboat`, `commit tags` already existed from ch2.)

**Housekeeping note**: `web/tests/export-preview.test.mjs` hardcodes the current
"next stub" chapter for its noindex/sitemap assertions (by design, per its own
comment: a literal count would go stale silently). Writing ch43 required bumping that
route from ch43 to ch44, same as every prior chapter completion; `npm run test:ci`
catches it if forgotten.

### 2026-08-12 (later) — ch42 written: website/snippets/POS survey, Part 7 (chapters 39-42) done

§5.3's lighter survey chapter, and the first hands-on chapter with **no `librefleet`
code at all**: Checkpoint is explicitly "none", and the hands-on runs entirely on
`functional`, chapters 21-30's database, closing the loop those chapters opened
(sale/purchase/stock/mrp/accounting all met a customer through a screen; POS is the
screen for a customer standing at a counter).

**Built a real till, not a described one.** Installed `point_of_sale` on `functional`,
opened a Bakery Shop session with a $150 float, rang up two real orders (one cash, one
card) through the actual offline SPA at `/pos/ui/...`, and closed the register.

**The chapter's gotcha found itself.** Closing the register with the Cash Count field
left at its default produced a genuine `-$167.24` "Difference" in red, a screenshot
worth more than a paragraph describing it: `ch42-pos-closing-discrepancy.jpg`. Not
staged, this was the actual first attempt clicking Close Register. Re-closed with the
real count entered, difference `$0.00` across the board, and both states are now in
the chapter as the "before" and "after" of the exact mistake a reader will make on
their own first close.

**Read the real accounting a session close produces**, not summarized: `POSS/.../0003`
(the consolidated sales entry, one receivable line per order rather than one move per
order) plus `PBNK1/...` and `CSH3/...` (one settlement move per payment method,
clearing the receivable into Outstanding Receipts for Card and straight into the cash
account for Cash, no bank statement needed since a physical drawer was just counted by
hand). Ties directly back to chapter 27's manual journal entries and chapter 28's
Outstanding Receipts pattern rather than introducing POS accounting as a new topic.

**Website/snippets kept deliberately light**, matching §5.3's "lighter" instruction:
installed `website`, confirmed for real that a page is exactly one `ir.ui.view`
(`arch_db` is ordinary QWeb) and that 191 `website.s_*` templates back the snippet
panel, captured the real Blocks panel. Attempted a live drag-and-drop of a snippet
into the page; the `computer` tool's `left_click_drag` did not trigger the builder's
drag handlers (needs finer-grained native drag events than a single synthetic
drag produces), so per the standing "don't rabbit-hole on browser automation" rule,
stopped after one attempt, discarded the half-edited page, and turned the drag itself
into exercise 4 rather than faking a screenshot of a result never actually produced.

Also verified and taught explicitly: **backend OWL components (chapters 39-41) do not
run on the website**, `web.assets_backend` and `web.assets_frontend` are different
bundles of the same framework. This closes a gap a reader coming straight off ch39-41
would plausibly assume otherwise.

4 odoolings checks against `--db functional`, all red-tested for real: the cash-count
check was flipped red by writing `cash_register_balance_end_real` back to 0 on the
closed session (reproducing the exact mistake) and confirmed it reports the same
-167.24 figure the UI did, before restoring. Glossary gained `Point of Sale` and
`snippet`. Three screenshots (cart, closing discrepancy, snippet panel), first chapter
to use `<Steps>` across a Movement-style hands-on this deep into Part 7.

**Part 7 (chapters 39-42, Frontend/OWL) is now fully written.** Next: Part 8, chapters
43-50, the OCA/expert tier, opening with ch43 (OCA safari).

### 2026-08-12 — ch41 written: the dashboard client action, and a counting trap worth the chapter

§5.3's "client action with an OWL component pulling data via ORM RPC", built as §5.5's
blueprint specifies (jobs per technician). Third registry pattern in three chapters
(systray → fields → actions), which is now an explicit throughline: the same
string-keyed lookup, failing the same unvalidated way each time.

**The chapter's real subject turned out to be where the arithmetic happens.** The
component uses `orm.formattedReadGroup` so Postgres does one `GROUP BY`, rather than
fetching every order and counting in JavaScript. Two odoolings checks exist purely to
catch the version that *looks* fine on two demo records: one fails if the code reaches
for `searchRead`, one fails if the drill-down rebuilds a domain by hand instead of
reusing each group's `__domain`.

**A genuinely valuable trap, found by testing rather than by planning.** Grouping by a
many2many double-counts: an order with two technicians belongs to both groups. Seeded
the workshop so this is *visible on the finished dashboard*, which reads "3 open
order(s)" above a column of 2 and 2. Verified from the shell (`search_count` 3, sum of
group counts 4) and quoted that transcript verbatim after re-running it to confirm the
exact repr. Anyone building a "total jobs" figure by summing that column ships a wrong
number and nothing warns them.

**Version fact, callout-worthy:** Odoo 19 replaced `read_group` with
`formatted_read_group` (`orm.readGroup` is simply gone) and changed the signature so
aggregates are their own argument. Older tutorials and Stack Overflow answers do not run
as written, so this got an "On Odoo 18 this differs" box rather than a footnote.

**A debugging fact worth more than the bug that revealed it:** while red-testing a
tag mismatch, the dashboard kept rendering perfectly in the tab that already had it
open, because the web client caches action definitions per tab. Only a fresh tab
produced the real failure (an Oops dialog plus `KeyNotFoundError: Cannot find key
"librefleet_dashbord" in the "actions" registry`). Nearly wrote the break-it lab from
the stale tab's behaviour; the chapter now teaches "open a fresh tab before you believe
anything" as its own lesson, because that state (live in the DB, broken in one tab, fine
in another, silent in the server log) is exactly where an afternoon disappears.

Reused ch40's slice-before-you-grep rule via `_dashboard_component_source()`. 5 checks,
three red-tested against their specific mistake (tag typo, `searchRead` instead of
grouping, hand-built drill-down domain). One screenshot. Glossary gained
`client action` and `read_group / formatted_read_group`. All 23 odoolings suites green,
including ch35 and ch37, whose state the seeding step touched.

### 2026-08-11 (really the last) — ch40 written: field widgets and patching

§5.3's two topics, "a custom field widget, patching existing components", written as
one argument rather than two unrelated halves: **registries are the front door,
patching is the fire escape, and choosing between them is the actual skill.** The
chapter's spine is that a registry entry affects only code that opts into it by name,
while a patch rewrites a shared class for every current and future user of it.

**Built two things.** A `librefleet_margin` field widget (green up-arrow on profit,
bold red down-arrow on a loss) applied to `margin` on the service order form, and a
`patch(FormController.prototype, ...)` overriding `onWillSaveRecord` to warn when
saving a losing order. Both verified in the browser: the widget photographed at
`-401.00` in red, the notification watched firing twice.

**A deliberate design decision, argued in a code comment rather than glossed:** the
patch *can* block the save by returning `false` and deliberately does not. A rule
enforced only in the browser is not enforced (an import or an RPC call bypasses it),
so chapter 20's server-side wizard stays the real control and the patch is a
convenience for the person clicking. Worth being explicit about, because the tempting
read of `onWillSaveRecord` is "here is where I enforce things".

**Reused ch39's bundle-reading technique and immediately found its limit.** A bare
substring check against a 9 MB bundle containing all of core is close to worthless:
`supportedTypes` alone appears 67 times, once per built-in widget, so a check for it
would pass even if the reader's own descriptor lacked it entirely. Added
`_margin_field_descriptor()`, which slices out just our descriptor before asserting.
This is a general lesson for ch41's checks too: **scope the slice before you grep.**

All four checks run red for real against their specific mistake (missing
`registry.add`, missing `supportedTypes` in *our* descriptor while core's 67 remain,
missing `widget=` in the view, missing `resModel` guard in the patch).

**The break-it lab was executed, not reasoned about.** The chapter claims that
removing the `resModel` guard leaves the patch running on every save in the client
while *appearing* harmless, because `record.data.margin` is `undefined` on a partner
and `undefined < 0` is `false`. Rather than assert that from JS semantics, removed the
guard, upgraded, edited and saved a real contact, and confirmed the save completed
silently with no notification. The lesson lands harder as an observation than as an
argument, and it is now safe to print.

4 odoolings checks, one screenshot (`ch40-margin-widget-loss.jpg`), glossary gained
`patch` and an expanded `widget`. All 22 odoolings suites green.

### 2026-08-11 (last of the day) — ch39 written: OWL fundamentals, Part 7 opens

First frontend chapter, and the first where the thing being taught cannot be verified
from the terminal at all. Built a systray component (`WorkshopClock`): an open-order
count fetched in `onWillStart` via `useService("orm")`, a clock ticking on a
`setInterval` cleaned up in `onWillUnmount`, and a refresh button.

**Verified in a real browser, which finally worked after six chapters of flakiness.**
The clock advancing between two screenshots proved `useState` reactivity for real;
creating an order from the shell and then clicking refresh moved the badge 1 → 2 with
no page reload, proving the ORM service round trip. First screenshot captured since
ch27: `ch39-workshop-clock-systray.jpg`.

**A genuinely hard problem, and the reason this chapter took real investigation:
how do you odoolings-check code that only runs in a browser?** Three approaches were
tried and two were wrong:

1. Read the compiled bundle from its `ir.attachment`. **Wrong, and dangerously so.**
   Assets rebuild only when the web client requests a hash Odoo has not cached, so the
   attachment can be stale, and worse, the browser may be running a *correct* cached
   bundle while the database holds a broken one. Caught this live: the check passed on
   a manifest that was missing the `.xml`, because it was grading a bundle nobody was
   running. A check that lies is worse than no check.
2. Add a staleness guard comparing the module's `write_date` to the attachment's
   `create_date`. Honest, but it just converted a false pass into a false failure the
   reader could not clear without knowing to reload the browser.
3. **Right answer: `/web/assets/debug/web.assets_web.js`.** Reading
   `web/controllers/binary.py` showed the `debug` unique token skips the attachment
   lookup entirely and rebuilds from the manifest on every request. Deterministic,
   always current, no cache to defeat. (Note `debug` serves the non-minified bundle, so
   the filename drops `.min`; `/web/assets/any/...` does NOT work, `any` matches any
   stored version including stale ones.)

All three checks were then run **red for real**, each against the specific mistake it
claims to catch: no `assets` key at all, the `*.xml` line missing, and a `t-name` typo.
The typo run also produced the genuine `OwlError: Missing template` from the browser
console, now quoted in the chapter's break-it lab.

**One more real find:** the first bundle request after editing a source file reliably
fails with a connection reset, because Odoo's file watcher restarts the server
mid-request. The check now retries up to three times rather than shipping a flaky
check and blaming the reader.

**Two things the chapter teaches that were only discovered by looking:**
- `text-bg-primary` on a badge renders as invisible-background plain text, because
  Odoo's brand purple *is* the Bootstrap primary and the navbar is that same purple.
  Switched to `text-bg-warning`. Only findable by looking at the screen.
- `t-esc` is **not** deprecated in OWL, unlike server-side QWeb where Odoo 19 logs a
  warning for it (`t-raw` is OWL's deprecated one). Core's client-side templates still
  use `t-esc` in 126 files. The chapter uses `t-out` anyway, for one habit across both
  engines, but the asymmetry is worth knowing before "fixing" core code.

3 odoolings checks (all red-tested), glossary gained `assets bundle` and `useState` and
the `OWL` entry grew. ch38's test suite re-run clean on a fresh `--without-demo`
database with the new assets present, and all 21 odoolings suites re-run green.

### 2026-08-11 (yet later, once more) — ch38 written: testing, M5 (chapters 31-38) done

Fifth and final write-chapter of Part 6. §5.3: `TransactionCase`, `HttpCase`/tours
intro, `--test-tags`, demo-data pitfalls, writing tests for everything built so far.

**Deliberate scope call, logged as a decision**: this chapter ships no
`CHAPTERS["ch38"]` entry in `odoolings.py`, the first hands-on chapter to do so.
odoolings verifies the reader's own already-running instance over RPC; this
chapter's whole subject is tests that build their own database state and run in a
throwaway transaction, the opposite kind of check. Forcing an RPC check here would
either be redundant with chapters 13/14/20/35's own checks or would have to
duplicate what `--test-tags` already proves better. The chapter's Verify section
runs the actual test suite instead and says so explicitly.

**Wrote four `TransactionCase` tests and one `HttpCase` test**, deliberately
covering earlier chapters rather than new functionality: chapter 14's overlap
constraint, chapter 13's margin computation, chapter 20's wizard guard, chapter 35's
reminder idempotency, and chapter 37's public controller. All fixtures are built in
`setUpClass`, no demo data referenced.

**The demo-data pitfall was reproduced for real, not described**: wrote a
throwaway test using `self.env.ref()` on a genuinely real demo xmlid
(`librefleet.vehicle_demo_ag_12_345`, confirmed to exist in
`data/librefleet.vehicle-demo.csv`), ran it against a database installed
`--without-demo`, and captured the actual `ValueError: External ID not found`
before deleting the test. This tutorial's own standing rule (chapter 4,
`--without-demo` by default) turned out to be exactly the same discipline a real
CI pipeline needs, not just an artifact of this tutorial's own setup.

**One test bug found writing this chapter, kept as a worked example**: the first
draft of the wizard-guard test picked a fixture that happened to pass
`assertLess(margin, 0)` by luck rather than by design (a flat labor fee dominating a
small parts loss). Fixed by choosing a fixture that unambiguously loses money and
keeping the `assertLess` as an explicit guard, illustrating a fixture-correctness
bug distinct from a code bug, both real, both worth showing.

**A version fact**: `--without-demo=all` (the pre-19 idiom) is deprecated, Odoo 19
wants a boolean and logs a warning + falls back to `True` when given `all`.

All ch08-ch20 and ch31-ch37 suites re-run clean via `python3 odoolings.py check`
after `librefleet` upgraded with the new `tests/` package present (tests do not run
automatically without `--test-tags`, so this only proves nothing else regressed).
Glossary gained one entry: `TransactionCase / HttpCase`.

**M5 (chapters 31-38, "Business Logic Like a Pro") is now fully written.** Next:
M6, chapters 39-42 (OWL and the web client), a new subject area rather than more of
the same, worth flagging to the author for a possible model-switch checkpoint.

No screenshot: same browser flakiness as ch28, ch30, ch35, ch36, ch37 (six chapters
now); also not obviously applicable here, this chapter's hands-on is entirely
terminal output, no UI claims to screenshot.

### 2026-08-11 (yet later, yet again) — ch37 written: controllers & portal, and the ch35/36 mystery solved

Fourth write-chapter of the walkthrough phase. §5.3's line: "HTTP routes, type='http'
vs 'json', auth levels, building the customer portal page; a taste of the website
builder", now assuming ch22/28 so the portal shows real orders and invoices.

**Mystery finally closed**: ch35's and ch36's PRs both flagged a "live user" (Tina
Technician) repeatedly resetting `SO/2026/0001` to draft mid-verification, four times
across two chapters. It was never a live browser session or the odoolings-starter
port conflict investigated along the way (though that conflict was real and separately
fixed, see below): it was `technician_rule_enforced` (ch10's own odoolings check),
which writes an order to "confirmed" then hardcodes it back to "draft" to prove the
record rule works, with no regard for what a later chapter needs that order to be.
Any regression sweep across ch08-ch20, which the walkthrough runs before every commit,
silently reset it. Fixed separately (PR #63, merged before this chapter): the check
now reads the order's actual stage first and restores it in a `finally` block.

**Separately, a real infrastructure issue surfaced mid-session**: `code-odoo-1`
(this repo's own container) had crashed, and `odoolings-starter-odoo-1` (a completely
different project, the reader-facing template, explicitly never meant to run
alongside this repo per §4.5) grabbed port 8069 in the gap and held it for hours.
Stopped with the author's confirmation, `code-odoo-1` brought back up cleanly on a
fresh network. Worth remembering: two Odoo projects sharing a host can silently
steal each other's ports, and "a live user is editing my data" is not the only
explanation for state drifting between checks, "which container actually answered
that curl" is another one to rule out first.

**Built**: two standalone controllers (`/librefleet/services`, `type="http"`,
`auth="public"`; `/librefleet/vehicles/lookup`, `type="jsonrpc"`, `auth="public"`),
then a full customer portal for `librefleet.service.order`: `portal.mixin` +
`_compute_access_url` override, a portal-scoped ACL + record rule (the same
two-layer split chapter 10 built for internal groups, now a third group on the same
model), a `CustomerPortal` extension adding a home tile, `/my/service-orders` list,
`/my/service-orders/<id>` detail, and `/my/service-orders/<id>/report` reusing
chapter 36's PDF action. Verified genuinely end to end: authenticated as a real
portal user (Anna Keller) via `/web/session/authenticate`, confirmed the record rule
actually hid `SO/2026/0002` (not hers) while showing `SO/2026/0001` (hers), then
confirmed the `access_token` share-link path works with zero session at all,
including the negative case (wrong token still redirects).

**Two real bugs found building it, kept as worked Gotchas:**
1. `portal_client_category_enable` defaults `False` on `portal.portal_my_home`; the
   home tile rendered nothing until an xpath explicitly set it `True`, the same
   two-step every core portal extension (`sale`, `project`, `account`) does.
2. `Content-Disposition`'s filename built raw from `reference` ("SO/2026/0001")
   carried a literal slash, which some browsers read as a path separator. Sanitized
   with `.replace("/", "_")`, caught by actually downloading the file rather than
   reading the code.

**A version fact worth its own callout**: Odoo 19 renamed `type="json"` to
`type="jsonrpc"` and kept the old name as a deprecated alias (confirmed in
`odoo/http.py`: it still runs, but logs `DeprecationWarning` server-side only, no
error to the caller). Reproduced for real in the chapter rather than just stated.

5 odoolings checks, two of them genuinely functional (`urllib` requests against the
reader's own running server, a new pattern for this file, previously everything went
through XML-RPC only; not a violation of §4.5 rule 4's filesystem-access ban, this
still only ever talks to the reader's own already-running Odoo). All ch08-ch20 and
ch31-ch36 suites re-run clean, twice, to prove the ch10 fix actually holds. Glossary
gained two entries: `controller`, `portal (customer portal, portal.mixin)`.

No screenshot: same browser flakiness as ch28, ch30, ch35, ch36 (five chapters now).

### 2026-08-11 (yet later still) — ch36 written: QWeb PDF reports

Third write-chapter of the walkthrough phase. §5.3's line named the topic
("PDF service report with header/footer, paper formats") and flagged that ch36
"now assumes ch27-28, so the canonical invoice-report example is grounded", meaning
the chapter should read core's real invoice report rather than invent an abstract
example, which it does in Concepts.

**Built a "Service Report" PDF for `librefleet.service.order`**, structured exactly
like `account.report_invoice`: a wrapper template (`t-call="web.html_container"`,
loops `docs`) calling a document template per record
(`t-call="web.external_layout"`, content in a `<div class="page">`). Verified for
real that this produces one page per record: rendered two orders in one call,
`pdfinfo` confirmed `Pages: 2`, with no page-counting code anywhere, the `page`
class does it. Binds to the Print menu the same way chapter 35's server action
bound to the Action menu, `binding_model_id` + `binding_type = "report"` instead of
`"action"`, a deliberate callback so the two chapters reinforce one mechanism
(`ir.actions.*` records binding to model views) rather than reading as unrelated.

**Two real bugs found rendering it, kept as worked Gotchas:**
1. `t-field` with `t-options='{"widget": "many2many_tags"}'` does not error on a
   QWeb report, it silently prints the recordset's `repr()` ("Technicians:
   res.users(5,)"), because that widget only exists in the web client. Fixed with
   `t-out="', '.join(o.technician_ids.mapped('name'))"`.
2. Rendering from `odoo shell --no-http` logs a `wkhtmltopdf: ... network error:
   ContentNotFoundError` warning, harmless: no running HTTP server means no
   `<img>` content can load, but text/tables render fine. Documented so it does not
   read as a real failure when a reader hits the same thing.

**A design decision, not a bug:** `margin` (chapter 13's computed field, what the
workshop earns) is deliberately never rendered on the document. One odoolings check
reads the template's `arch_db` for `o.margin` and fails red if it is ever added,
verified red on a duplicate before writing the real template.

Added `web` to librefleet's `depends` explicitly (was always installed transitively,
but the templates `t-call` into it, so an explicit dependency is correct regardless
of install order luck). 4 odoolings checks, exercised red (arch_db injection test)
and green. All ch08-ch20, ch31-ch35 suites re-run clean. Glossary gained one entry:
`QWeb report (ir.actions.report)`.

**Recurring issue flagged to the author:** a live browser session (user "Tina
Technician") repeatedly reset one service order's stage to draft mid-session during
both ch35 and ch36 development, three times total, breaking the automated-action
check each time. Re-fixed and re-verified green before each commit; still
unresolved as a root cause, likely an open tab against `localhost:8069`.

No screenshot: same browser flakiness as ch28, ch30, ch35 (now four chapters).

### 2026-08-11 (yet later) — ch35 written: cron, server and automated actions

Second chapter of the walkthrough's write-chapter phase (after ch30). §5.3's line was
one sentence, "Scheduled actions (cron), server actions, automated actions," and
§5.5's blueprint already named the feature: a maintenance-reminder cron on
`librefleet.vehicle`, moved here from its pre-renumber "ch25" reference by D13.

**Built one feature three ways on purpose**, not three unrelated examples: a daily
cron reminds the workshop about vehicles overdue for service, the same logic runs
on demand from the Vehicles list's Action menu, and an automated action retires the
reminder the moment a service order is actually marked done. The throughline is
`_inherits`: `ir.cron` delegates to `ir.actions.server` through
`ir_actions_server_id`, the exact composition pattern chapter 31 taught on
`librefleet.loaner`. Once that clicks, a cron stops looking like a separate feature
and becomes "a server action plus a schedule," which is literally what the code says.

**Two bugs found by running it, both real and both now Gotchas:**
1. `records` is `None` when a server action runs from a cron (no selection), so
   `records.action_send_maintenance_reminders()` throws `AttributeError` on `None`
   the first time Run Manually is clicked. Fixed with `records or model.search([])`,
   and left in the chapter as a worked bug rather than smoothed over, matching the
   plan's debugging-literacy differentiator.
2. `mail.activity.mixin` alone is not enough to call `action_feedback()`: it posts
   its completion note through `message_post_with_source()`, which lives on
   `mail.thread`. `librefleet.vehicle` now inherits both.

**A third finding, not a bug, worth flagging:** `ir.cron` and the `ir.actions.server`
it targets share one database row via `_inherits`. Setting `name` on both records (an
easy first instinct) silently overwrites the same field twice; the chapter settles on
one name, set once, on the action.

Added `base_automation` to librefleet's `depends` (pulls in `digest`, `resource`,
`sms` transitively, normal and expected). 5 odoolings checks, exercised red and green
during development (missing action name, missing done order, both caught for real,
not staged). All ch08-ch20 and ch31-ch34 suites re-run clean on `tutorial` afterward.
Glossary gained four entries: `activity`, `automated action`, `cron (scheduled
action)`, `server action`. `web/tests/export-preview.test.mjs` had ch35 hardcoded as
"the still-a-stub fixture", the same category of trap D13 caught elsewhere: bumped
its two hardcoded chapter numbers forward to ch36.

No screenshot: this session's browser tab now redirects every navigation to
`/odoo/discuss` regardless of target URL, the same failure mode as ch28 and ch30 but
now reproducing on a fresh tab too, which rules out per-tab state and points at the
browser session itself. Flagging for the author to restart the Chrome connection;
ch28, ch30 and ch35 can be caught up in one screenshot pass once it's healthy.

### 2026-08-11 (later still) — ch30 written; its §5.3 spec was pre-19 and had to be redesigned

First stub turned into a chapter, and the first time the syllabus itself was wrong rather
than merely incomplete. §5.3's ch30 line was written against an Odoo 15-18 mental model.
Three of the things it asks for **do not exist in Odoo 19**, which was only discoverable
by opening the container:

- **`stock.valuation.layer` is gone.** `"stock.valuation.layer" in env` is `False`.
  Valuation moved onto `stock.move.value`, with `remaining_value` carrying FIFO leftovers
  and `value_manual`/`value_justification` providing a manual-override audit trail. This
  is the single most expensive item in an 18 to 19 migration for anyone with custom
  costing code, and it is now ch30's headline.
- **The stock interim accounts are gone.** `property_stock_account_input_categ_id` and
  `..._output_categ_id` survive only in stale `.po` files. The routing moved to
  `stock.location.valuation_account_id`: each location *outside* the company names what
  value becomes when it arrives there (Customers means COGS, Inventory Loss means
  shrinkage, Production means WIP), while the category keeps the stock asset account.
  Read `_get_account_move_line_vals`, which is a single symmetric `if`, and
  `_should_be_valued`, which is three lines and defines "inside the company".
- **`manual_periodic` is now `periodic`**, and the labels changed from Manual/Automated to
  Periodic (at closing)/Perpetual (at invoicing).

Scope call (author informed, logged here because §5.3 no longer matches what shipped).
§5.3 listed eight topics for one chapter. Shipped: costing methods, periodic vs
perpetual, the account routing, COGS on delivery, and the valuation-mode migration trap.
**Deferred, deliberately:** landed costs (needs installing `stock_landed_costs`, a
self-contained flow), lock dates and period close, and defining a custom `account.report`.
The last is a reporting-engine topic that was bundled here only because Community ships
the engine without the statements; it belongs nearer the reporting/OCA work, not inside a
valuation chapter. Cramming eight topics would have produced a grab-bag; the five that
shipped form one argument.

The chapter got luckier than it deserved on material. The `functional` database already
contained, from chapters 22, 24, 25 and 26, everything needed for the lesson:

- 630.00 of valued receipts and **zero** journal entries, because the demo runs `periodic`
- a two-step receipt whose second leg is `is_valued=False`, because both ends are inside
  the company, which is the cleanest possible illustration of the boundary rule
- `WH/OUT/00044`, the delivery created in ch22 and made reservable in ch24, still sitting
  at `assigned` and never validated

So the hands-on validates *that* delivery, which posts the database's first ever stock
entry (STJ/2026/08/0001: Stock Valuation credit 132.63, COGS debit 132.63) and joins
Parts 4 and 5 exactly as §5.3 hoped, without inventing a scenario.

Two findings worth keeping:

1. **The Brake Pad Set had no product category at all**, unnoticed since ch21, so it
   valued at 0.00 whatever was paid for it. Now the chapter's opening hook and its first
   odoolings check. A product with no category is unpriceable by construction and nothing
   anywhere warns you.
2. **Switching valuation mode is not retroactive**, and the arithmetic proves itself:
   after the switch the warehouse holds 497.37 while account 110100 reports **-132.63**,
   a gap of exactly 630.00, precisely the receipts that predate the switch. A negative
   stock asset is the visible symptom, and the fix is an opening entry, not a costing
   change. This is the "why is the P&L wrong" ticket §5.3 wanted, arrived at honestly.

Five odoolings checks registered under `ch30`, run red (against a duplicate with the
category cleared) and green. All nine earlier `functional` check suites re-run and still
pass: the changes affect valuation only, and ORM-level checks on orders, invoices and
taxes are untouched. Three glossary entries added (COGS, costing method, inventory
valuation, valued move). Roadmap M4 flipped to done, which makes Parts 0 to 5 complete.

### 2026-08-11 (later) — i18n folded into ch34, closing the second audit gap

Second half of the audit above. `i18n basics` in §5.4 is now ✅, covered inside ch34 rather
than as its own chapter, so no renumber (the alternative was priced at 16 chapters and
declined). ch34 grows from ~1.5 h to ~2.5 h and gains four Hands-on steps, three odoolings
checks, two quiz questions, six Gotchas and an `i18n/` folder in its checkpoint.

Why ch34 is genuinely the right home rather than a convenient one: a `.po` **is** a data
file, and the chapter's existing master data turned out to be load-bearing for the lesson.
"Tire Rotation" is exportable as a translatable term **only because** it has a stable xml
id from step 1 *and* the field became `translate=True` in step 6. Data with no xml id has
nothing for a `.po` to point at, so the two halves of the chapter explain each other.

Everything below was verified in the container; several facts contradicted what the
obvious guess would have been:

- **`ir.translation` does not exist in Odoo 19** (`"ir.translation" in env` is `False`).
  Field values moved to `jsonb` columns, code strings to an in-memory catalog read from
  `i18n/*.po`. Any answer telling you to query it is pre-16.
- **Code translations are never in the database.** Confirmed via
  `odoo.tools.translate.code_translations`. Consequence worth teaching: a database backup
  cannot carry them, which is now a quiz question.
- **`translate=True` migrates the column**: `character varying` → `jsonb`, and Odoo moves
  existing values under an `en_US` key by itself. Watched it happen to all five service
  types, including the three hand-clicked in ch11. No migration script.
- **Odoo 19 has an `odoo i18n {loadlang,export,import}` subcommand**, replacing the old
  `--load-language` / `--i18n-export` server flags.
- `_()` still comes from `from odoo import _` in most of core (990 files under
  `addons/*/models/` vs 238 for the newer `self.env._()`), so the book teaches the import
  form and notes the other.
- Named placeholders (`%(margin).2f` with `margin=`) survive into the `.pot` msgid and
  interpolate correctly *inside* the French translation (`marge -240.00`), so ch20's
  verified `-210.90` transcript is unaffected by the rewrite.

Four gotchas found by doing it, none of which I would have predicted:

1. **`-l` is greedy** (`nargs='+'`), so `i18n export -l pot librefleet` eats the module as
   a language code and fails with `the following arguments are required: MODULE`. Module
   goes before the flag.
2. **Default export writes in-place and fails here**: container runs uid 100, the bind
   mount belongs to host uid 1000, so it dies with `PermissionError`. The recipe is
   `-o -` piped to a host-side redirect, which also ties back to ch6's new `-T` gotcha.
3. **`-l fr_FR` logs `Ignoring not found languages: fr_FR` and then works.** Upstream
   cosmetic bug: `_get_languages` matches on `code` OR `iso_code`, then diffs the request
   against `iso_code` only, and French is `code=fr_FR`/`iso_code=fr`. Passing `-l fr`
   avoids the scare. Read the source (`odoo/cli/i18n.py:129-135`) rather than guessing.
4. **`_()` resolves its catalog from the calling frame**, so calling it in `odoo shell`
   returns the source string even with the translation loaded and the language active.
   Verified both halves: English from the shell, French when the wizard actually raises it.
   The chapter tells readers to test code translations by triggering the real code path.

One deliberate consequence, documented in the chapter rather than hidden: `translate=True`
breaks raw SQL on that column, with `invalid input syntax for type json` (not the
"operator does not exist" I expected). ch34's own earlier psql commands are affected, and
because they run *before* step 6 they stay correct in reading order; step 6 says explicitly
what changes for anyone re-running them afterwards. ORM domains are untouched, which is why
all 17 chapter check suites on `tutorial` still pass unchanged.

### 2026-08-11 — syllabus coverage audit against an external checklist; pdb lands in ch6

Prompted by an external Odoo-onboarding checklist (a Camptocamp "Odoo core" skills list)
the author asked whether the tutorial covers it all. Audited §5.4's own coverage
checklist, which explicitly invites this ("agent: verify before calling the syllabus
done"), by grepping the real chapter files rather than trusting the syllabus prose.

Result, and the surprise is the second line:

- Everything on that checklist **except two items** is either written (module structure,
  models, views, ORM/domain/env, field types, both inheritance kinds,
  compute/onchange/constraints, shell, security rules, module data, mixins) or already
  planned with a stub in place (QWeb reports ch36, controllers/portal ch37, testing ch38,
  OWL ch39-42).
- **ch30 and ch35-50 are all still 24-line stubs.** 17 chapters. Written chapters are
  ch1-29 and ch31-34. This is worth stating plainly in the changelog because the syllabus
  reads as though Parts 6-9 exist, and they do not yet.
- Two items were genuinely unplanned, with no chapter and no slot: **i18n/translations**
  (only an unchecked `i18n basics ▢` in §5.4) and **`pdb`/`debugpy`** (named in §3.5's
  tooling list, homeless).

Decisions (author's call, offered with costs):

1. **Translations folds into ch34 Data Files** rather than becoming its own chapter.
   `.po` files *are* data files, ch34 already owns XML/CSV/`noupdate`/`ref()`, and this
   avoids a 16-chapter renumber. §5.4's `i18n basics` gets ticked from there. The
   renumber alternative was priced explicitly and declined, consistent with D13's
   renumber having broken `main` once already.
2. **`pdb` extends ch6** (Daily Driver Workflow), which already owns dev mode, log
   levels and the shell, so the debugger is the natural escalation from "read the log".
   No renumber, no new chapter.

Written and verified for ch6 in the real container, not from memory:

- `pdb.runcall(env["res.partner"].search, ...)` stops one line into core's `search` at
  `odoo/orm/models.py:1378`; `l`, `p domain`, `p self._name`, `pp`, `s`, `w`, `b`, `c`,
  `q` all captured from a genuine pty-driven session (the Bash tool cannot type into
  pdb, so the transcript was driven through `pty.fork`).
- `breakpoint()` works in reader-defined shell code, landing at `<console>`.
- **`docker compose exec` allocates a TTY by default**, so the book's existing shell
  command already works with pdb and needs no `-it`. The flag that breaks it is `-T`,
  which this book uses precisely when piping scripts, so the two are mutually exclusive.
  Written up as a Gotcha because it is a genuinely confusing interaction.
- A stranded `breakpoint()` with no terminal raises **`bdb.BdbQuit`** and fails the
  request. Verified, rather than the intuitive-but-wrong "it hangs forever", which is now
  the long distractor in the new quiz question.
- `debugpy` is **not** in the `odoo:19` image, so it is a pointer only, not a hands-on.
  Teaching it would mean changing the image or the compose file, and §4's rule 2 makes
  compose changes expensive (starter-repo mirror + drift check).

`docker-compose.yml` deliberately untouched: attaching a debugger to the *running server*
would need `stdin_open`/`tty`, and the honest workaround (call the method from
`odoo shell`) costs nothing and is what practitioners do anyway.

### 2026-08-09 (review pass, ch1-10) — the renumber's unpaid debt, and the house style
for Hands-on

A sweep back over the ten chapters already walked, asked for as "check everything is
correct, check the visuals, make the UI/UX richer, and write the conventions down so the
other chapters follow." Three separate findings, one of which had been live on the site
for days.

- **The D13 renumber falsified twelve cross-references and nobody noticed.** Inserting
  Parts 4-5 moved every part number after 3, and the migration fixed *chapter* numbers
  while leaving *part* numbers alone. So ch2 sent readers to "Part 6" for the OCA
  (it is Part 8), ch3 and ch4 sent them to "Part 5" for OWL (Part 7), ch3 called
  inheritance "Part 4" (Part 6), and ch7/ch8 pointed at Part 6 for OCA tooling four more
  times. Two counting claims rotted the same way ("the next 37 chapters" in ch3, now 47;
  "the next 35 chapters" in ch5, now 45), plus ch12's own index contradicting itself
  ("across six chapters" in a file that says "Eight chapters ago" two paragraphs up).
  All fixed. **The lesson is in §4.3's authoring rules now: prefer a chapter number to a
  part number in prose**, because "chapter 43" survives a reorganization and "Part 8"
  does not. Part references cannot be linted (every number 0-9 is a real part, so a wrong
  one still resolves), which is exactly why the convention has to carry the weight.
- **`tests/cross-refs.mjs`** is the regression net for what *can* be checked: every
  "chapter NN" in prose must name a chapter that exists (411 of them, all currently
  resolving), and every `<Mermaid>` must carry a `label`. Wired into `npm test`.
- **Twenty-six diagrams shipped with no `label`**, i.e. `aria-label="Diagram"` to a
  screen reader, because the component defaults it and a missing prop is invisible in
  review. Ch1-10's are written; the other 23 chapters sit in an explicit
  `UNLABELLED_BASELINE` in the test, to be deleted line by line as each chapter is
  walked. New unlabelled diagrams fail immediately.
- **`<Steps>`/`<Step>` is now the house style for Hands-on, not a ch8 experiment.**
  Applied to ch4, 5, 6, 7, 9 and 10 (31 steps). The component numbers the steps, so the
  headings drop their own numbers and stay `###` so the table of contents still lists
  them. `<Files>` likewise: ch9 and ch10 now show the module tree growing (four files,
  then seven, then nine) on the `--tone-sky` surface ch8 established. Both written into
  the `write-chapter` skill.
- **One stale instruction fixed:** ch8 still told readers to borrow the app icon from
  "the reference clone set up in Verify", a clone that was deleted on 2026-08-03. It is
  the checkpoint tarball now.
- **Two dense passages simplified** rather than rewritten: ch4's master-password callout
  (one 100-word sentence chain, now three short paragraphs) and ch6's `dev_mode`
  parenthetical.

Two things deliberately **not** done, both needing the author:

- **Ch5 and ch10 still have no screenshots**, and ch4 has eight. Ch10's payoff image is
  the Workshop privilege on a user's Access Rights tab, which needs a login the agent
  cannot perform (§6 rule 4b). Ch5's is the database *selector* (the "Manage databases"
  moment its step 2 describes), which needs a `tour`-only instance to be reader-faithful;
  the local server currently lists `functional` and `tutorial`, so capturing it now would
  show state no ch5 reader has.
- **The ch5-ch10 walkthroughs were never logged here.** Commits `e72029e`, `a145afd`,
  `c0b07a4`, `303779c`, `d5267ba` and `13b8cd6` carry the fixes, but §10 stops at ch4,
  so those sessions' findings live only in commit messages. Not reconstructed from the
  outside; flagged so the gap is visible rather than silently assumed filled.

### 2026-08-09 (walkthrough, ch4) — the first hands-on chapter, walked against a genuinely
fresh instance, eight screenshots, and a real Odoo mechanism nobody had verified

Ch4 is the reader's first contact with a running Odoo, so it got the most scrutiny of any
chapter so far: a truly empty instance (own Docker project, own volumes, copied from this
repo's own `docker-compose.yml`/`odoo.conf`, confirmed byte-identical to the starter, so no
new GitHub repo was needed to get reader-faithful state), the author creating the real
database live, and every UI claim checked against the actual screen rather than inferred.

- **The master password field's auto-suggestion is not decorative, and this was not
  previously known.** Read `odoo/addons/web/controllers/database.py`'s `create()`:
  when the current master password is the well-known insecure `admin` (which
  `code/odoo.conf` ships on purpose), whatever gets submitted in that field **becomes the
  real master password**, unconditionally, no check against the old one. Proved by
  posting a deliberately wrong value to `/web/database/create`: it succeeded, and a
  follow-up post of `admin` then failed with `Access Denied`, exactly as the mechanism
  predicts. Also proved it is **self-healing by container restart** in our setup: the
  change lives only in memory (`set_admin_password` mutates `self.options` before
  `save()` even attempts the doomed write to the read-only-mounted conf file), so a
  restart reloads `admin_passwd=admin` from disk. Added as a Callout; this is genuinely
  useful knowledge nobody had written down before.
- **The chatter's position is a real, source-verified breakpoint, not a guess.** Traced
  `mail/static/src/chatter/web/form_renderer.js`'s `mailLayout()`: side vs. bottom is
  decided by `uiService.size >= SIZES.XXL`, and `ui_service.js`'s `MEDIAS_BREAKPOINTS`
  puts XXL at **exactly 1400px**. The chapter said "at the bottom" as if universal; our
  own automation session runs at 1920px (confirmed via `window.innerWidth`, since
  `resize_window` is not actually honored in this environment, worth remembering for
  future screenshot sessions) so every screenshot here shows the side layout. Rewrote to
  state the mechanism instead of one fixed position, so neither the text nor the
  screenshot goes stale depending on a reader's own window width.
- **The debug field tooltip does not show "which module defined it," and the chapter
  said it did.** Triggered the tooltip for real (`Tax ID` on `res.partner`) and read
  every line: Label, Field, **Model**, Type, Widget, Context. No module line. Model and
  module are different things; conflating them was a real inaccuracy, not a nitpick.
  Fixed the claim, and confirmed separately that "which module" *is* answerable through
  the UI, just via a different screen (`ir.model.fields`' own form has an "In Apps"
  field) — which is exactly what exercise 2 already asks the reader to go find, so the
  exercise stays as written.
- **Sales pulling in Invoicing and Dashboards, verified to an actual dependency chain**,
  not assumed from watching the menu grow: `sale_management → sale → account_payment →
  account` (Invoicing) confirmed via each module's real `__manifest__.py`; Dashboards
  traced to `spreadsheet_dashboard_sale` in the installed-modules list rather than the
  `board` module I'd have guessed. Cross-referenced to chapter 8 (which teaches `depends`
  explicitly) after checking chapter 3 does not, despite an early draft of this callout
  claiming it did, caught before it shipped.
- **A stale module count, fixed with a live count:** `crm_lead` on a fresh install is
  **44** (verified against the real fresh instance), matching the chapter's own claim,
  which the "Verify" section's quoted 45 already explained as "44 plus the one you made."
- **Eight screenshots**, each earning its place by proving a specific claim: the
  database-manager form with the auto-generated password banner, the app switcher before
  and after CRM+Sales, the Pipeline kanban, an opportunity's chatter, a quotation's
  workflow buttons and status bar, a user's Access Rights tab (existence of the *tab*
  needed calling out explicitly, since the Users list view alone never shows it), the
  debug tooltip, and the `crm.lead` Fields list. All plain demo/placeholder data (Odoo's
  own stock "Mitchell Admin" persona, not anything from this session), nothing to redact.
- Icons added to ch4's Further Reading, matching the ch1-3 convention.

Environment notes for next time: `resize_window` does not reliably control the real
render viewport in this automation setup; verify with `window.innerWidth` before trusting
a requested size. The throwaway fresh-instance Docker project (`ch4fresh`) was torn down
with `-v` after use; the main `code` stack (`tutorial` + `functional`) was stopped to free
port 8069 during the fresh-instance test and restarted afterward, both databases intact.

### 2026-08-09 (walkthrough, ch1-3) — an `Icon` component, and its own decisions

Author asked mid-walkthrough for icons "almost everywhere," naming
[Phosphor](https://phosphoricons.com) specifically, plus real brand logos downloaded from
source where a generic glyph would not do. Scoped as its own piece of work before chapter
work resumed, per the §7.1 rule this very case is now the example of.

- **`@phosphor-icons/react` added as a direct dependency** (MIT, peer dep `react >= 16.8`,
  we run 19.2.8). Confirmed the library ships a **per-icon SSR entry point**
  (`@phosphor-icons/react/dist/ssr/<Name>`, verified by unpacking the tarball) with no
  `'use client'` directive anywhere in that build: each icon is a plain `forwardRef`
  returning an inline `<svg>`, `fill="currentColor"` and `size="1em"` by default. Built and
  exported the site: the icons appear in the static HTML with **zero client JS chunk**
  (checked `out/_next/static/chunks` for a phosphor entry: none), so "almost everywhere"
  costs nothing at runtime.
- **`components/icon.tsx`: a curated `ICONS` allow-list, not a `name: string` dynamic
  import.** Every entry is a real static import, so the bundle only grows by icons
  genuinely referenced, and a typo is a build/test failure rather than a silent blank space
  in production. 26 names to start (link-source kinds: `docs`, `source`, `video`, `talk`,
  `forum`, `reddit`, `store`, `news`, `external`; a handful of recurring concepts; three
  status glyphs), registered once in `getMDXComponents` as `<Icon name="..." />`.
- **One real bug, not obvious until rendered:** Tailwind's own `preflight.css` sets every
  bare `svg` to `display: block`, which is correct for a 400px Mermaid diagram and wrong
  for a glyph sitting mid-sentence — first attempt put each icon on its own line above the
  link it was meant to sit beside. Fixed in the component (`inline-block`, plus a
  hand-picked `align-[-0.15em]` nudge against Geist's baseline), not per usage, so every
  future `<Icon>` in every future chapter gets it for free.
- **`tests/icon-names.mjs`, wired into `npm test`**, matching the project's existing
  discipline of gating every author-facing convention (quiz balance, glossary blank lines,
  the image-optimizer guard). Parses the real `ICONS` object out of `icon.tsx` rather than
  hand-maintaining a second list, so the check can't drift from the registry it's checking
  against. Proven to catch a deliberately wrong name before wiring it in.
- **Applied to ch1-3's "Further reading" bullets and ch2's "Where the knowledge lives"
  table** as the worked example: a leading icon for the *kind* of source (docs/source
  repo/video/forum/store), which is a genuinely repeated pattern across nearly every
  chapter to come, not decoration for its own sake. **Not** retrofitted across the 26
  chapters not yet walked; applied chapter by chapter as each is walked, same as
  screenshots.
- **Real downloaded brand logos, deliberately not used yet.** Phosphor already bundles
  monochrome `*Logo` glyphs for GitHub, YouTube, Reddit etc., which is what "source",
  "video" and "reddit" resolve to above; those match the site's existing pure-line,
  `currentColor`, theme-aware Mermaid aesthetic. A full-color downloaded logo (Odoo's own
  mark, OCA's sunburst) would be the right call for a brand that genuinely needs
  recognizing on sight and that Phosphor has no glyph for, but none of ch1-3's content
  needed one, and introducing one is a bigger decision (each brand has its own usage
  guidelines: minimum size, clear space, color) worth making deliberately when a real case
  shows up rather than pre-emptively for a chapter that doesn't need it.

### 2026-08-06 (CI) — main went red on an action deprecation, not on our code

Five consecutive deploys failed. Diagnosis worth keeping, because the obvious readings were
both wrong:

- **`build` succeeded every time**; only `deploy` failed, each attempt reaching
  `deployment_in_progress` and then "Timeout reached, aborting!".
- **Not our content.** PR #17 changed *only this markdown file*, which cannot alter
  `web/out`, yet `78e8c7e` deployed at 11:38 and the near-identical artifact would not at
  11:59.
- **Not a stuck deployment.** First theory was that #18 being cancelled mid-deploy had left
  the environment blocked. Checking the deployment statuses killed it: every deployment
  progressed `queued → in_progress → failure` on its own, so nothing was holding the lock.
- **Not a Pages outage.** githubstatus reported Pages operational with no open incidents.
- **The cause** was in a warning we had been ignoring: *"Node.js 20 is deprecated. The
  following actions target Node.js 20 but are being forced to run on Node.js 24:
  actions/deploy-pages@v4."* `deploy-pages@v4` declares `using: node20`; `@v5` declares
  `using: node24`. The runners began force-migrating today, which is exactly when the job
  started failing. Bumped to `@v5`, and `upload-pages-artifact@v3` → `@v5` since the pair
  is versioned in lockstep.

`actions/checkout@v4` and `actions/setup-node@v4` are still node20 and will get the same
treatment eventually. Left alone deliberately: the build job is green, and the lesson here is
that changing things that work while chasing a failure makes the failure harder to attribute.
Bump them when they break, or when there is a quiet moment.

**Transferable bit:** when CI goes red, read which *job* failed before assuming it was the
last content change. A green `build` with a red `deploy` is almost never the chapter you
just wrote.

### 2026-08-05 (audit) — every menu path in every written chapter, checked

The author asked to verify the already-written chapters before continuing to ch30, which
was the right call. Full sweep of the 25 menu paths across both databases, resolving each
hop by name and comparing its `group_ids` against `admin.all_group_ids`. Script kept at
`scratchpad/checkmenus.py`; worth rebuilding if this needs doing again.

**The rule that explains most of the mistakes:** inside an app, level 1 is the menu-bar
dropdown (Operations, Products, Configuration), a level-2 item **that has children is a
section heading and is not clickable**, and level 3 is the item you click. So a
reader-facing path names the dropdown and the item and **skips the heading**:
`Inventory → Configuration → Warehouses` is right even though the record sits under
*Warehouse Management*. Getting this backwards produces errors in both directions, and both
kinds were present.

- **Three real errors, all fixed here.** `Inventory → Configuration → Reordering Rules`
  does not exist at all: no menu points at either action on
  `stock.warehouse.orderpoint`, and the rules live on the replenishment screen
  (`Inventory → Operations → Replenishment`, whose menu is an `ir.actions.server`). Ch26
  omitted a whole dropdown twice: `Inventory → Operations → Physical Inventory` and
  `Manufacturing → Operations → Manufacturing Orders`.
- Ch25 also now warns that Replenishment opens with **To Reorder** and **Not Snoozed**
  pre-filtered, so a new rule for a well-stocked product is not in the list you land on.
- **Two false alarms, resolved by looking rather than trusting the script.** Ch4's
  `CRM → …` and `Sales → …` paths are fine: the reader installs those apps in ch4 itself,
  and they are simply absent from our `tutorial` database. **Correction to my first answer
  here:** ch4 must be shot against the **`tour`** database, not `functional`. `tour` already
  exists from when ch4 was written and holds exactly ch4's end state (`crm` +
  `sale_management` + demo, 67 modules, 39 partners). `functional` would have been wrong:
  it also has purchase, stock, mrp and loyalty installed, so its menu bar shows apps a ch4
  reader has not installed yet, and ch4's entire point is watching the menu change as you
  install two apps. **Screenshot each chapter against the database that chapter's reader
  actually has**, which for the dev track is `tutorial`, for Parts 4-5 is `functional`, and
  for ch4 alone is `tour`.
  Ch10's `Settings → Technical → Access Rights` is correct, *Security* being a heading.
- **Everything else verified reachable**: ch21 Products, ch22 CRM and Quotations, ch24
  RFQ, ch25 Warehouses, ch26 Bills of Materials, ch27 Journals, ch29's six, ch8 Update
  Apps List, ch11's two LibreFleet menus, ch31 Loaner Cars.
- Two chapters (ch18, ch31) still say "author tour, screenshots pending" in their own
  prose. Those sentences come out when the screenshots go in.

### 2026-08-05 (policy) — screenshots are chapter work, not an M8 pass

Corrected the same day it was written, on the author's challenge ("when did we agree about
no screenshots?"). He is right that no such agreement existed. `CLAUDE.md` rule 5 says only
that screenshots must not be faked and that the author re-executes the tour; his own words
this session were "remember to add screenshots **for me** at the end". The agent read that
as "capture nothing per chapter, do one pass at M8 with the author in the room" and wrote
that into §6 rule 4b. That was an inference presented as a shared decision, which is the
failure worth remembering: **do not turn the author's preference into a stronger standing
rule than he stated, and do not attribute the result to "we".**

Now: the agent captures screenshots while writing each chapter (§6 rule 4b lists the five
mechanics), the author's manual re-execution stays the acceptance gate, and ch4 plus ch21-29
are a one-off backfill under M8. The only genuine reason the delay looked reasonable is that
the image pipeline was broken until today, so anything shipped earlier would have 404'd.

### 2026-08-05 (ch27/ch29 UI paths) — five wrong interface claims in one browser session

The M8 dry run put a real browser on `functional` for the first time. **One screen produced
four wrong claims, and a fifth came from trying to fix them.** This is the whole argument
for the M8 pass, and the ratio should be assumed to hold for the other chapters.

- **`ir.ui.menu` lies about what a user sees.** Walking `root.child_id` shows the tree that
  *exists*; the web client filters it by `group_ids`. `root.with_user(admin).child_id` does
  **not** filter either. The only honest checks are a real browser, or reading `group_ids`
  per item and comparing against `user.all_group_ids`. My first ch27 path "fix" earlier the
  same day was derived from an unfiltered walk and was still wrong.
- **Community hides more than the app name.** `Chart of Accounts`, `Journal Entries`,
  accounting `Reporting` and `Multi-Ledger` are gated behind **`account.group_account_readonly`**
  ("Show Accounting Features - Readonly"), which Community grants to **nobody**. The
  Accounting privilege (id 6) offers only *Invoicing* and *Administrator* and neither
  implies it, and Odoo 19's privilege-based user form exposes **no checkbox** for it. So
  "tick the group on the user" is also wrong, which is the fifth bad instruction, caught
  before it shipped only because the user form was opened to confirm it.
- **Actions are not gated, only menus are.** Both screens load fine at
  `/odoo/action-account.action_account_form` and
  `/odoo/action-account.action_move_journal_line`, verified in the browser. Ch27 now
  explains the gate once in a callout and uses those URLs; ch29 points back to it for the
  one account it has to create. Reaching a gated menu's action by URL is now taught as a
  technique, which is better content than the wrong menu path was.
- **"Accounting" under Configuration is a section heading, not a submenu.** The path is
  `Invoicing → Configuration → Taxes`, not `… → Configuration → Accounting → Taxes`. Both
  chapters corrected. Ungated and genuinely where expected: **Taxes**, **Fiscal Positions**,
  Currencies, Payment Terms. Gated but admin-reachable: Journals, Settings, Configuration.
- **Three ch29 field labels were wrong**, all from the same screen: it is **Tax Name** not
  "Name", **Fiscal Position** singular not "Fiscal Positions" (the field is
  `fiscal_position_ids` with no explicit `string`, so Odoo derives a singular label from the
  name), and `document_type`'s "Related to" label is **never rendered** on the tax form,
  since the table you are in implies it.
- **Verified correct on the same screen**, for what it is worth: `Tax Computation` =
  Percentage, `Tax Type` = Sales, the two `DISTRIBUTION FOR INVOICES` / `FOR REFUNDS`
  tables with `%` / `Based On` / `Account` / `Tax Grids` columns, `Base` and `of tax` as the
  Based On values, and 60.00 / 40.00 against Tax Received / City Tax Received.
- **Practical note for the pass:** the browser tool returned **1568x739** on some calls and
  **1447x850** on others in the same session, so viewport is not stable by default. Pin it
  with `resize_window` before capturing anything, or the screenshots will not match.

### 2026-08-05 (build) — the site could not have shipped a single screenshot

Found while dry-running the M8 screenshot pipeline on one throwaway image, before
capturing anything real. Worth reading as a cautionary tale about which of our gates
actually gate things.

- **`next.config.mjs` was missing `images: { unoptimized: true }`.** Fumadocs maps
  markdown `![]()` to `next/image` (`defaultMdxComponents` → `fumadocs-core/framework`),
  and with `output: 'export'` and no `unoptimized`, the build **succeeds** and then emits
  `src="/_next/image/?url=…&w=…&q=75"` for every image. There is no optimizer on GitHub
  Pages. Proven by serving `out/` and fetching the URL the browser would ask for:
  **404**, while `npm run build` reported success and `npm run test:ci` was green.
- Fixed with that one line. Same URL after the fix: `200`, and zero `_next/image`
  references in the exported HTML.
- **Why every existing gate missed it:** the build does not error, `test:export` only
  asserted on route status codes, and *nothing in the repo contains an image*, so there
  was nothing to break. It would have surfaced at M8, after a whole capture session, or
  worse, in production where `npm run dev` (which has a live optimizer) would have looked
  perfect. This is the same shape as the D13 lesson: a gate that passes because it never
  looks at the thing.
- **`tests/export-preview.test.mjs` now walks every route in the sitemap** and asserts no
  page references `/_next/image`, and that every `<img src>` returns 200. Proven red by
  commenting the config line out: it fails with the fix instruction in the message. The
  guard currently has no images to check, which is the point: it is armed for M8.
- Pipeline otherwise confirmed working: `web/public/screens/…` referenced as `/screens/…`,
  markdown image syntax renders with Fumadocs styling, and the file is copied into `out/`.
  Screenshots come out of the browser tool as **jpeg at 1568px**, so verify small UI text
  survives before committing to a full pass.

### 2026-08-05 (ch29) — taxes and fiscal positions, and two Odoo 19 model changes

- **Ch29 written and executed in `functional`**, continuing from ch28's end state. Six
  flows, one per §5.3 topic: split a tax's distribution across two accounts, create a
  price-included tax, discover where an unaccounted tax lands, fix it, ship to a German
  customer and watch the tax get replaced, then make a rounding cent appear and revert.
  Seven odoolings checks, each proven red before green.
- **Two Odoo 19 changes verified in the container, both of which invalidate what every
  older tutorial and blog post says.** These were found by reading
  `addons/account/models/account_tax.py` and `partner.py` on disk, not from memory, and
  the second one changes arithmetic:
  1. **`account.fiscal.position.tax` no longer exists** (`"account.fiscal.position.tax"
     in env` → `False`). The src→dest mapping moved onto the tax: a fiscal position holds
     a *many2many* `tax_ids`, and each replacement tax names what it stands in for in
     `original_tax_ids` ("Replaces"), with `replacing_tax_ids` as the readonly mirror and
     `is_domestic` computed/stored. `fp.tax_map` is computed by walking that backwards and
     its values are **lists** (one tax can be replaced by several). Verified:
     `ft.tax_map == {1: [3], 2: [4]}`.
  2. **`tax_calculation_rounding_method` defaults to `round_globally` in 19**, and its
     label is **"Round per Tax"** (so grepping the interface for "globally" finds
     nothing). Odoo 18's default was `round_per_line`, labelled "Round Globally". An
     upgraded 18 database keeps its stored value, so 18 and 19 disagree by a cent on the
     same order: three lines of 10.10 at 15% total 34.86 per line, 34.85 per tax. Both
     verified by building the orders.
- **`price_include` is a computed field in 19**, derived from the tax's
  `price_include_override` (`tax_included`/`tax_excluded`) falling back to
  `company.account_price_include`. Writing `price_include` does nothing. The company-wide
  setting is **read-only once the database has any journal entry**
  (`has_accounting_entries` is `True` in `functional`), so on any live database the
  per-tax override is the only lever. Chapter teaches the override, not the setting.
- **The best accidental discovery, kept as a hands-on beat rather than a footnote:** a
  brand new tax's four repartition lines have **no account**, and Odoo's fallback for a
  tax line without one is *the account the base line used*. So a freshly created tax posts
  its tax straight into income, on an invoice that balances and looks perfect. Verified:
  28.04 credited to Product Sales. Step 2 of the hands-on does it on purpose and step 3
  fixes it, because this is a large share of real "why is the P&L wrong" tickets and it is
  one empty cell.
- **Repartition factors are relative weights in practice, not absolute percentages.**
  `@api.constrains('...repartition_line_ids')` on `account.tax` requires the positive "of
  tax" factors to total 100% (and negative ones -100%), and requires the invoice and refund
  tables to match line for line, so the form refuses anything else. Writing straight onto
  `account.tax.repartition.line` skips that check, and then the tax total still comes out
  right: 50/40 on a 30.00 tax gives **16.67 / 13.33**, not 15.00 / 12.00, because the
  shortfall is redistributed by weight. This corrected a wrong assertion message I had
  written into the ch29 check ("would silently lose the rest"); it is now the ⭐⭐⭐
  break-it lab, with the real mechanism as the answer.
- **`compute_all` is public but cannot be called over XML-RPC**: its return dict carries
  an `account.tax.group` recordset under `group`, so the marshaller raises
  `KeyError: <class 'odoo.orm.models.account.tax'>`. Recorded as a gotcha, and it is why
  the ch29 checks verify tax-included arithmetic by reading a posted invoice's lines
  rather than by asking the tax to compute.
- **Reverse charge verified as a real shape** (⭐⭐ exercise): a tax with +100% and -100%
  "of tax" lines posts two tax lines of 30.00 on a 200.00 bill while `amount_tax` reads
  0.00. Aiming the negative side at a `liability_payable` account fails with "Any journal
  item on a payable account must have a due date", which is why the exercise says to
  create a second current-liability account.
- **A check that was green before the reader did anything, caught and retightened.** The
  first version of the export check looked for any sale order for a non-US customer with a
  fiscal position and no tax. The demo data ships **17** such orders (Gemini Furniture), so
  it passed on a fresh database. It is now anchored on the Brake Pad Set *and* requires the
  line's tax to carry a non-empty `original_tax_ids`, since zero tax alone would also be
  true of a line with no tax at all. Worth generalising: **any check whose subject exists
  in demo data must be anchored on something the reader made.**
- **WATCHED gained `account.account` and `account.tax`** (sixth and seventh instance of the
  allowlist only being right for chapters already written against it). Deliberately *not*
  added: `tax_line_id` on `account.move.line`, which would have made ch28's already-quoted
  diff transcript wrong, and `account.tax.repartition.line`, whose base rows have no
  labellable field and would print twelve `id=N` lines per tax.
- **Ch27's three UI paths were wrong and are fixed.** Community's accounting app is called
  **Invoicing**, and its configuration menus sit one level deeper than the Enterprise
  app's: the real paths are `Invoicing → Configuration → Accounting → Chart of Accounts`
  / `→ Journals` and `Invoicing → Accounting → Transactions → Journal Entries`. Verified by
  walking `ir.ui.menu`. Ch29 says this once, in prose, where the reader first needs it.
- **One pre-existing glued glossary entry fixed** (`**decoration-***`). The audit script
  used since the 14-entry incident has a blind spot: its `^\*\*[^*]+\*\*:` pattern cannot
  match an entry whose *name* contains an asterisk. Use `^\*\*.+?\*\*(?::| \()` instead.
  132 entries now, none glued.
- Screenshots and the author's own hands-on pass remain pending for ch21-29, per §4 rule 5.

### 2026-08-05 (ch25/ch26, one PR) — inventory and manufacturing, plus a cross-chapter check bug

- **Ch25 and ch26 written and executed together**, continuing in `functional` from ch24's
  end state in one coherent sequence (ch25's purchase adds 5 brake pads to reach 15 on
  hand, ch26 manufactures 4 more to reach 19), so the numbers quoted in each chapter tie
  together across both.
- **Ch25** deepens ch24's stock-move idea rather than repeating it: on-hand vs forecast
  (verified: `qty_available` 10.0 vs `virtual_available` 6.0, the gap being `outgoing_qty`
  4.0 already reserved to chapter 22's delivery), multi-step routes (switching reception
  to two steps confirmed that the **second leg is created only once the first is
  validated**, not upfront, and that `purchase.order.picking_ids` only ever shows the
  first leg, under-reporting a multi-step route), and reordering rules (created for real,
  explicitly deferred to chapter 35 for the scheduled action that acts on them, since this
  is a "meet the fact, not the mechanism" chapter for cron). The warehouse is reverted to
  one-step at the end so later chapters see the simple case by default.
- **Ch26** gives the Brake Pad Set an actual bill of materials (two components, one
  operation against a work center) and manufactures it for real. **Verified, found by
  testing**: an `mrp.production` gets its sequence number at **creation**, in `draft`,
  breaking the "no name until confirmed/posted" pattern every other document in this part
  follows (sale orders, purchase orders, invoices). Component consumption was checked
  against the BoM ratio exactly (0.5 Friction + 1.0 Plate per unit, times 4 produced =
  2.0 and 4.0 consumed), and the whole thing plays out as a third instance of the
  double-entry-for-goods idea: components arrive positive at a virtual **Production**
  location, the finished good leaves it negative, mirroring ch24's Vendors/Stock quants
  and ch27's debit/credit.
- **Found and fixed a real cross-chapter bug during the regression sweep, not introduced by
  this PR.** Ch22's `order_is_invoiceable_on_confirmation` check asserted
  `invoice_status == 'to invoice'`, but ch28's own hands-on later invoices that exact
  order, moving it to `'invoiced'`. Any reader who finishes ch28 and re-runs `check ch22`
  (to double-check earlier work, which the tool explicitly invites) got a false failure.
  Widened to accept either value. Caught only because the regression sweep re-runs every
  chapter's checks together rather than checking each one in isolation once and moving on;
  worth doing after every new chapter from here on, not just at milestone boundaries.
- **Two more allowlist gaps**, same recurring pattern as ch21/24/28: `purchase.order.line`
  needed `receipt_status`/`invoice_status` added to its parent, `stock.warehouse.orderpoint`
  was entirely unwatched. Both fixed with label overrides where the default rendered as a
  bare id.
- **A second draft caught a real transcript bug before it shipped**: ch26 originally
  referenced a shell variable (`front`) carried over from ch25's *separate* shell session,
  and was missing the `docker compose exec ... odoo shell` line before its first Python
  block. Neither chapter's session state crosses a file boundary; only the database does.
  Fixed by defining `front` in ch26's own session and adding the missing shell-entry line.
- Glossary +7 across both chapters (*on-hand vs forecast*, *picking*, *reordering rule*,
  *routing*, *bill of materials*, *manufacturing order*, *Production*), inserted with the
  blank line and verified afterwards that nothing is glued.
- Screenshots pending the author, per standing rule 5.

### 2026-08-05 (ch24) — purchase, and the moment the apps stop being separate

- **Ch24 written and executed.** Procure-to-pay as the mirror of ch22, which makes it cheap
  to learn, plus the **three-way match** as the genuinely new idea: `product_qty`,
  `qty_received` and `qty_invoiced` are tracked separately *so they can disagree*, and the
  disagreement is the deliverable.
- **The best thing in this chapter was unscripted.** Validating the receipt produced, in one
  diff: the two equal-and-opposite quants (`WH/Stock` +10, `Vendors` -10, the move's two ends
  and a literal parallel to ch27's debit/credit), **and** `WH/OUT/00044 state: confirmed ->
  assigned`, which is *ch22's customer delivery reserving stock it had been waiting for*.
  Nobody triggered it: inventory is a shared pool, not a per-order ledger. That is the
  moment Parts 4-5 stop reading as a tour of separate apps, and it only exists because the
  chapters share one database in sequence. Worth protecting when ch25-26 are written.
- **Verified**: `purchase.order.state` is draft/sent/to approve/purchase/cancel;
  `receipt_status` is **`False`** on a draft, not `'pending'` (so it is not always one of
  the three documented values); a vendor bill is `account.move` with `move_type='in_invoice'`
  debiting **Expenses** and crediting **Account Payable**, the exact mirror of ch28's
  invoice, numbered from the Purchases journal (`BILL/2026/08/0002`); posting needs an
  `invoice_date` or it stalls.
- Tool: added `purchase.order.line` to the watched allowlist (and `receipt_status`/
  `invoice_status` to `purchase.order`), since the RFQ diff showed the order but not its
  line. **Third instance of the same pattern** after ch21's `product.product` and ch28's
  `account.payment`: the allowlist is only right for chapters already written against it.
- Glossary +2 (*RFQ / purchase order*, *three-way match*), this time inserted **with the
  blank line** the previous PR's 14-entry repair taught me to add, and verified afterwards
  that no entry is glued.
- Screenshots pending the author, per standing rule 5.

### 2026-08-05 (ch23) — pricing, and three things called "the discount"

- **Ch23 written and executed.** The chapter's spine is that a price can be changed by
  three unrelated mechanisms, each leaving a different trace, which is why "the discount is
  wrong" is such a hard ticket. All three were produced for real on one product: a
  **pricelist rule** rewrites `price_unit` (79.00 to 60.00) and leaves `discount` at zero;
  the **discount field** would do the opposite; a **claimed reward** appends *its own line*
  at `price_unit=-12.0` and touches neither.
- **Verified**: pricelists are **off by default** (zero records until the
  `product.group_product_pricelist` flag is ticked), and enabling it creates **three**
  Default pricelists, one per company. `applied_on`'s numeric prefixes are literally the
  specificity sort key, demonstrated with two competing rules: the brake pads take the flat
  variant price of 60.00 while an Office Chair with no rule of its own falls through to the
  global 10% and prices at 63.00. Rules do not stack.
- **`_try_apply_code` validates but does not apply**, returning a mapping of claimable
  rewards; claiming needs a second `_apply_program_reward` call per reward. Calling only the
  first is a **silent** no-op, which is how I first "applied" a promotion and got nothing.
  Now taught rather than rediscovered.
- **A check that could not fail, caught by testing red.** The first version of "the more
  specific rule wins" read a *saved* order line's `price_unit`, so editing the rule
  afterwards left it green: a line takes its price at creation and is never repriced. Fixed
  to assert the rule's configuration **and** its observed effect, which then goes red
  properly. Worth generalising: for these functional checks, verifying only stored
  outcomes can produce checks that never fail, so assert the configuration that caused
  them too.
- `product.pricelist._get_product_price` is private and RPC-refuses, same boundary as
  ch28's `_create_invoices`, so there is no public "what would this cost" call. Noted in
  the chapter and worked around in the check.
- Glossary +2 (*pricelist*, *reward*).
- **Repaired 14 glossary entries I had been silently breaking since ch21.** The helper I
  was using to insert entries alphabetically wrote `new_text + "\n" + anchor`, with no blank
  line, so every insertion glued the *following* entry onto the new one's paragraph. Fourteen
  entries across the ch21, ch22, ch27, ch28 and ch23 additions were affected, and **four
  merged PRs shipped with the damage**. Only `recordset` ever surfaced, because it is the one
  a `<Term>` component actually looks up, which failed the build with
  `<Term k="recordset">: no such glossary entry`. Anything not referenced by a `<Term>` was
  broken invisibly. Lesson for future entries: markdown needs the blank line, and the
  glossary is only self-checking where a `<Term>` happens to reference it.
- Screenshots pending the author, per standing rule 5.

### 2026-08-05 (hotfix) — the renumber broke a test I never ran

- **Main was red and I put it there.** `tests/export-preview.test.mjs` asserts that
  planned (stub) lessons stay navigable and that the sitemap lists only complete pages,
  and it hard-codes routes. The D13 renumber moved
  `04-business-logic/25-cron-server-automated-actions` to
  `06-business-logic/35-...` and `24-data-files` to `34-data-files`, so the test 404'd.
- **Why every local check passed anyway:** `npm test` is only
  `test:progress && test:quiz`. `test:export` is a **separate script**, run by CI *after*
  the build because it serves `out/`. So the one suite that could catch a renumber
  regression was the one suite I never invoked. §5.8's runbook step 9 said "npm run build,
  npm test" and was therefore incomplete as written.
- **Fixed the brittleness, not just the paths.** The magic `30` ("home plus 29 complete
  docs pages") would have gone stale again on the very next chapter, and did: the sitemap
  is now 34. The test now derives the expected count by walking `content/docs` and
  counting `.mdx` files that lack the Stub callout, which self-maintains as stubs become
  chapters.
- **Process fix so this cannot recur:** added `npm run test:ci`
  (`test && build && test:export`, CI's exact order) and pointed CLAUDE.md's command list
  at it, with a note about why `npm test` alone is insufficient. Use that before any push.

### 2026-08-05 (ch28) — invoicing, payments, reconciliation; M4's key set done

- **Ch28 written and executed**, closing the loop ch22 opened: the confirmed order is
  invoiced, posted, then paid in **two instalments on purpose** so the reader watches
  `payment_state` go `not_paid` → `partial` → `paid` rather than jumping straight to paid.
- **The chapter's correction, and the reason it is worth its length**: `payment_state` is
  *computed*, and what it summarises is reconciliation. The diff makes the causation
  visible: the invoice's own receivable line stays untouched through the first payment and
  only flips with `reconciled: None -> True` when the second covers the rest, with
  `payment_state: partial -> paid` following as the consequence. Two
  `account.partial.reconcile` records of 200.00 and 163.40 are what "paid" actually means.
- **Verified**: a registered payment creates an `account.payment` *and* an `account.move`
  with `move_type='entry'` in the bank journal (`PBNK1/2026/00001`), so ch27's duality
  extends to payments; the posted invoice has three lines (Product Sales 316.00 credit,
  a 15% Tax Received 47.40 credit, Account Receivable 363.40 debit) which is a clean
  hand-off to ch29; `account.payment.register` defaults its amount to the residual;
  payment states include `in_process` before `paid`, so Outstanding Receipts is not the
  bank balance. Community ships the whole reconciliation engine, only the assisted bank
  widget is Enterprise.
- The earlier tool-validation stumble is now taught properly: `_create_invoices` is
  private and RPC-refused, so the wizard (`sale.advance.payment.inv`) is the supported
  path, and that is stated as a Gotcha rather than rediscovered by the reader.
- Tool: `account.payment` gained `display_name` to its watched fields and a label
  override, since it was rendering as `id=1`. Same class of fix as ch21's
  `product.product`, which supports the note there that the allowlist is only right for
  the chapters already written against it.
- Glossary +3 (*reconciliation*, *payment_state*, *payment term*).
- **M4's highest-value set (ch21, ch22, ch27, ch28) is complete.** Remaining in M4:
  ch23-26 (pricing, purchase, inventory, manufacturing), ch29-30 (taxes, valuation),
  `boss4`, and the functional vocabulary sweep. Screenshots for all four written chapters
  are pending the author, per standing rule 5.

### 2026-08-05 (ch27) — accounting foundations, and a company-dependent field

- **Ch27 written and executed**, the chapter §5.3 called the highest-value one in Parts
  4-5, and it earns that: the reader hand-writes a balanced journal entry, then opens the
  invoice ch22 produced and finds it is the same model. Odoo's refusal, **"The entry is
  not balanced."**, was triggered for real rather than described.
- **A significant Odoo 19 finding: `account.account.code` is computed, NOT stored, and
  company-dependent**, backed by an `account.code.mapping` model. Reading it while a
  different company is active returns `False` **silently**: verified on one
  `account.move.line`, where the wrong company gives `False` and
  `with_company(inv.company_id)` gives `'400000'`. This is a trap for any report or
  migration script, and it also means a psql query against a `code` column on
  `account_account` will not find what its author expects. Now a Gotcha and a ⭐⭐⭐ lab.
- **Second multi-company trap, also verified**: the demo database has **three** companies
  and 14 journals, only 7 of which belong to the active one, and the shell does **not**
  apply the company filter the interface does. A bare `search([])` in a script crosses
  company boundaries in a way the equivalent UI action would not.
- Verified: `move_type` has seven values (`entry`, `out_invoice`, `out_refund`,
  `in_invoice`, `in_refund`, `out_receipt`, `in_receipt`); a draft move's `name` is
  `False`, not `"/"`, and the journal sequence numbers it at posting
  (`MISC/2026/08/0002`); the generic chart installs 157 accounts.
- **Two chapter snippets corrected by running the exact printed text.** `read_group`
  returns the count under `move_type_count` in 19, **not** `__count`, so the printed
  loop raised `KeyError`; replaced with a `search_count` loop over the selection (clearer,
  and it orders to match the Concepts table), with the key change noted as an aside since
  ch48 will use `read_group` properly. An escaped apostrophe in a quiz option also broke
  the MDX build, caught pre-merge.
- Check design note: the balance check now validates **one** move rather than summing
  across the matched set, because a reader may legitimately have written more than one
  entry. My own leftover test entry is what exposed that.
- Glossary +4 (*account.move / account.move.line*, *chart of accounts*, *debit / credit*,
  *journal*). Screenshots pending the author, per standing rule 5.

### 2026-08-05 (ch22) — sales, and core's empty hook

- **Ch22 written and executed** in the `functional` database, continuing from ch21's end
  state (it sells the Brake Pad Set created there, which is what makes Parts 4-5 feel
  like one run rather than nine disconnected tours).
- **The chapter's real payoff turned out better than the plan predicted.** §5.3 said the
  read-what-it-did moment would be `sale/models/sale_order.py::_action_confirm`. Reading
  it revealed the method body is **empty**, just a docstring inviting extension, and that
  seven `sale_order.py` files define it (the base plus six modules). `sale_stock`'s
  override is two lines: `_action_launch_stock_rule()` then `super()`. So "confirming a
  sale creates a delivery" is core using ch31's classic extension on its own model, which
  teaches the golden rule far better than any invented example. Only `sale`,
  `sale_purchase` and `sale_stock` are installed in our database, which is itself the
  explanation for why *this* order grew a delivery and not a repair order.
- **Verified facts, none recalled.** `sale.order.state` has exactly draft, sent, sale,
  cancel: **there is no `done` state in 19**, locking is a separate `locked` boolean, so
  18-era code testing `state == 'done'` is silently dead (same shape as ch21's
  `type == 'product'`, and now a paired callout). `invoice_status` is independent of
  `state`. `crm.lead.type` is lead/opportunity on one model, so conversion creates
  nothing, confirmed by the diff showing `+1 crm.lead` for the whole sequence.
- **The invoice-policy contrast, measured rather than asserted**: `Brake Pad Set` has
  `invoice_policy='order'` and `Office Chair` has `'delivery'`, both `type='consu'`. So
  the confirmed order reads `qty_delivered=0.0` with `qty_to_invoice=4.0` and
  `invoice_status='to invoice'`, while the same order quoting a chair would refuse to
  invoice. This also explains the error hit during the ch21-era tool validation, which is
  now a taught lesson rather than a stumble.
- **Three quoted `grep` commands were corrected after testing the exact text.** The
  `grep -rl .../addons/*/models/sale_order.py` form fails for the reader, because the
  glob expands in *their* shell where those paths do not exist; it needs
  `bash -lc '...'` to expand inside the container. Two others had `-A` values that did
  not match the lines shown. This is the audit's unrunnable-transcript class caught
  pre-merge by re-running every command exactly as printed.
- Checks are deliberately **name-agnostic** (order numbers differ per reader, since the
  sequence keeps counting), matching on business state instead. Red proven by reverting
  the order to draft via SQL, which renumbers nothing and so keeps the quoted transcripts
  valid; green restored after.
- Glossary +4 (*extension hook*, *invoice policy*, *invoice_status*, *lead / opportunity*).
  Screenshots pending the author, per standing rule 5.

### 2026-08-05 (ch21) — the business spine, and two facts the plan had wrong

- **Ch21 written and fully executed** against a purpose-built `functional` demo database
  (six apps, demo data), following §4.3 rule 3's two-movement shape: run the flow in the
  interface, then read what it did. Checks ran red before the hands-on and green after,
  and every transcript was recaptured on a **clean** database after the exploratory one
  had drifted (on the polluted database "customer and vendor both" read 1; on a fresh one
  it is 0, so the first number was unreproducible, which is precisely the failure mode the
  2026-08-03 audit was about).
- **Two version-sensitive facts corrected, both checked in the container rather than
  recalled.** Odoo 19's `product.template.type` is `consu` (Goods), `service`, `combo`,
  with **no `product` type**; storable became a separate boolean `is_storable`
  ("Track Inventory") contributed by `stock`, not by `product`. And `uom.uom` has **no
  `category_id` and no `uom_type`** any more: each unit declares `relative_factor`
  against a `relative_uom_id`, giving a tree with a recursively computed `factor` and a
  `parent_path`. §5.3's ch21 line said "UoM categories" and has been fixed.
- **A defect in `snapshot`/`diff` that only writing a chapter could expose**:
  `product.product` was missing from the watched allowlist, so creating a template with
  attributes reported `+1 product.template` and hid the two generated variants, which is
  the chapter's entire lesson. Added, along with a `display_name` label override, since a
  freshly generated variant has no internal reference and rendered as `id=71`. Worth
  remembering as a pattern: the allowlist is only right for the chapters already written
  against it, so expect to extend it in ch22-30.
- Also verified and used: `product_variant_count` is not stored, so searching on it
  raises `ValueError: Cannot convert ... to SQL because it is not stored` (now a Gotcha,
  and it ties back to ch13); translatable fields are JSON in Postgres, so psql needs
  `name->>'en_US'`; `product.product.name` is `related='product_tmpl_id.name'`.
- Glossary +4 (*product attribute*, *product template / product variant*, *rank*,
  *is_storable*, *unit of measure*). Screenshots for the product form and the
  developer-mode bug menu are **pending the author's own pass**, per standing rule 5.

### 2026-08-05 (later) — M3.5 renumber executed, and `snapshot`/`diff` proven

- **M3.5 done.** §5.8's runbook executed: ch21-40 → ch31-50, Parts 4-7 → 6-9, 4
  checkpoint dirs, odoolings keys, `ch24-demo` → `ch34-demo`, plus Parts 4-5 scaffolded
  with 10 stubs. Sidebar now reads 1 to 50 with no backwards jump. The dry run earned
  its place three times over: **range expressions** (`chapters 21–32` shifted only its
  first endpoint, producing `31–32` and the nonsensical `43–40`, so ranges are now
  excluded from the script and fixed by hand as semantic edits since the *Parts* numbers
  change too); **title frontmatter** (bare leading numbers were not covered by the
  chapter-reference patterns at all, leaving all 20 renamed files claiming their old
  number); and three line-wrapped refs plus a quiz string containing *version* numbers
  that each needed individual inspection. Keeping the `ch` pattern case-sensitive spared
  the `CH22-AAA` license plates in ch32's real transcript from being rewritten.
- **`odoolings snapshot` / `odoolings diff` built and validated against a real
  `functional` demo database**, because §4.4 committed ten chapters to depending on it
  and it was recommended on theory rather than evidence. It holds up. Confirming a
  quotation reports the state flip *and* the silently created delivery order; creating
  an invoice reports `+1 account.move` with `+2 account.move.line` showing **debit
  173.00 Account Receivable / credit 173.00 Product Sales**, which is double-entry made
  visible from one button click, exactly the ch27 lesson demonstrated rather than
  asserted. It also correctly reports "nothing changed" when an action fails, so it does
  not invent activity.
- **Facts learned while validating, all of which are chapter material** (verified, not
  recalled): `sale.order._create_invoices` is private and **cannot** be called over
  RPC, so the reader-facing path is the `sale.advance.payment.inv` wizard, which is what
  the "Create Invoice" button actually opens. `stock.picking.button_validate` returns an
  `ir.actions.act_window` for a `confirm.stock.sms` popup rather than completing, and
  needs `context={"skip_sms": True}` to run headless (a real gotcha for ch25 and for any
  test that drives deliveries). Odoo 19 refuses to invoice before delivery when the
  product's invoicing policy is "Delivered Quantities", and the error text names the fix,
  which is ch22's delivery-vs-invoice-policy lesson arriving unprompted. An invoice's
  `name` is `None` until posting, when the sequence assigns `INV/2026/00010`: numbering
  happens at post time, not creation, which connects ch27's inalterability material to
  ch34's sequences.
- Two defects found and fixed in the tool itself: invoice-line names carry the whole
  multi-line product description, which wrecked the one-record-per-line output (now
  whitespace-collapsed and length-bounded), and `stock.move` was labelled by the picking
  reference it inherits rather than by its product (now a per-model label override).
- `.odoolings-snapshot.json` added to both this repo's and the starter's `.gitignore`.
  The tool writes exactly one dotfile in the working directory and still never reads the
  reader's module, so §4.5's location-independence contract holds.
- **Next:** ch21, ch22, ch27, ch28 (the highest-unblocking-value set per M4).

### 2026-08-05 — D12/D13: the functional act, and a renumber to make room for it

Planning only. No chapter written, no renumber executed yet; §5.8 is the runbook and
M3.5 is the blocking milestone.

- **Why this exists.** The author's Camptocamp onboarding includes functional training
  (CRM, Sales, Purchase, Inventory, MRP, Accounting, POS, Website/eCommerce,
  Subscriptions, and a cross-app "branded T-shirt" use case), and asked whether it
  belongs in Odoolings. It does, but not as an add-on: **the existing plan already
  leans on functional knowledge it never teaches.** The old ch22 says "extend the Sales
  flow", ch26's report is an invoice, ch27's portal shows invoices and orders, ch38's
  N+1 examples are over `account.move.line`, and LibreFleet's `part` to
  `product.product` bridge is an abstraction without it. Odoo is not domain-agnostic
  the way Django is: `account.move`, `stock.move` and `sale.order` *are* the framework's
  substance, so functional illiteracy is a hole in the framework, not a gap in breadth.
- **Two new parts, not a parallel track** (D12): **Part 4 "How Odoo runs a business"**
  (ch 21-26: the partner/product spine, sales, pricing, purchase, inventory,
  manufacturing) and **Part 5 "Odoo's accounting core"** (ch 27-30: double-entry and the
  `account.move` duality, invoicing/payments/reconciliation, taxes/fiscal positions,
  inventory valuation and period close) plus `boss4`. Split into two parts of 6 and 4
  rather than one of 10, so both match the size of existing parts (Part 2 has 8, Part 3
  has 5, Parts 5-7 have 4 each), and so the reader gets a completion milestone and a
  mastery bar halfway through. A separate "functional track" with its own F1-F14
  numbering was considered and **rejected**: it would read as bolted on forever, which
  is exactly what the author asked to avoid.
- **Framed as the story's turning point, which is what stops it feeling out of place.**
  Parts 2-3 build LibreFleet as an island (its own `standard_cost`/`list_price`, quietly
  reimplementing a slice of `product.product`); Parts 4-5 are the reveal that Odoo
  already ships all of it; Part 6 is then the payoff. Three acts: build a module, meet
  the system, work inside the system, which is also a developer's real first year.
- **Taught the developer way, and this is the differentiator.** One template, no fork
  (§4.3 rule 3): Hands-on always splits into "Run the flow" (UI) then "Read what it
  did" (psql, shell, the generated `stock.move`/`account.move`, and the core source
  method that ran, e.g. `sale_order.py::_action_confirm`). A functional chapter that
  only narrates clicking is a failed chapter, and that is precisely the weakness of
  existing Odoo functional training. Exercises become ticket-shaped ("the discount on
  this quote is wrong, find why"). odoolings verifies *business state* over XML-RPC,
  which no functional training anywhere does.
- **New tool: `odoolings snapshot` / `odoolings diff`** (§4.4). Click Confirm on a
  quotation, get back "+1 `stock.picking`, +2 `stock.move`, state draft→sale". Turns
  "what did that button actually do?" into a method the reader owns. Stays inside D10
  (pure XML-RPC, no filesystem). Must be built before ch21.
- **Verified in the container rather than assumed** (2026-08-05). Installable on 19
  Community: `crm`, `sale`(+`_management`/`_stock`), `purchase`(+`_stock`),
  `stock`(+`_account`/`_landed_costs`), `mrp`(+`_account`), `account`, `analytic`,
  `payment`, `delivery`, `sale_loyalty`, `point_of_sale`, `website`, `website_sale`.
  Community `account` is much richer than its "Invoicing" label suggests: full
  `account.move`/`.move.line`, journals, chart of accounts, taxes + fiscal positions +
  repartition lines, payments + terms, partial/full reconcile + reconcile models, bank
  statements, all six lock dates, and the `account.report` **engine**. Confirmed absent
  from disk (Enterprise): `account_accountant`, `account_reports` (so the P&L/Balance
  Sheet/Aged *definitions*, though the engine ships, which becomes a Community
  exercise), `sale_commission`. `sale_subscription` has an `ir.module.module` row but no
  files and state `uninstallable`.
- **The two Community gaps become builds, not omissions.** Subscriptions and
  commissions are `boss4` stretch goals implemented as LibreFleet features. A developer
  who builds recurring billing has learned more than one who clicked through the
  Enterprise app, and it converts a limitation into the most dev-relevant content there.
- **Renumber (D13), and why now.** The new parts must land after Part 3 (the "read it"
  half needs ch9-15's ORM/psql/shell) and before the old ch22. Every scheme that avoids
  renumbering yields a sidebar reading ch20, ch41, ch21. So ch21-40 → ch31-50, Parts 4-7
  → 6-9, planned `boss4`/`boss5` → `boss5`/`boss6`, total 40 → 50 chapters. Cost was
  measured, not guessed: 20 file renames (**only 4 are written chapters**), 4 part
  folders, 4 checkpoint dirs, ~21 forward refs in ch1-20, ~46 mixed refs inside ch21-24,
  9 in the glossary, 11 in odoolings. **This is the cheapest the migration will ever
  be**, and the one real trap is documented in §5.8 step 5: refs to ch1-20 must not
  move while ch21-40 must, and both appear in the same paragraphs, so a blind sed
  corrupts content.
- **Also distributed rather than duplicated:** POS lands in ch42 (it is Odoo's largest,
  offline-first OWL app, so it belongs with the OWL part), eCommerce context in ch37
  (controllers and portal), and ch4 is explicitly rescoped to stay *first contact* with
  a forward pointer instead of trying to teach flows.
- Scope honesty: this grows the syllabus 40 → 50 chapters (+25%) and adds real tooling
  work. It does not attempt to produce functional consultants; chart-of-accounts design
  and jurisdiction tax compliance are career skills, not chapters (§5.7).

### 2026-08-04 (SEO foundation) — earn discovery with complete lessons

- The home title, description, hero copy and GitHub README now clearly describe the
  product as a free, open-source Odoo 19 development tutorial without keyword stuffing.
- Added `WebSite`, `Course`, `Person`, `LearningResource` and breadcrumb JSON-LD that
  matches visible content. The site intentionally does not imitate Google's course-list
  rich-result markup: that feature requires at least three courses, while Odoolings is
  one coherent course with published lessons.
- Canonical and sitemap URLs now agree on trailing slashes. The 16 unwritten chapter
  stubs remain navigable so readers can see the curriculum, but emit `noindex,follow`
  and stay out of the sitemap until their real descriptions replace the shared stub
  marker. Published lessons remain indexable and discoverable through the course graph.

### 2026-08-04 (later still) — the deferred migration happens

- **Executed the migration the previous entry deferred.** `ronitjadhav/odoo-tutorial`
  was squashed to a single, solely-authored commit (no coauthor trailer) and pushed as
  the root commit of a fresh `ronitjadhav/odoolings`, which is now the live repo. GitHub
  Pages on the new repo is configured with `build_type: workflow` and the custom domain
  `odoolings.ronit.io`; `basePath` was removed entirely (the site serves from the
  domain's root via `public/CNAME`), which is the one-variable cutover the "shared
  constants" refactor in the previous entry was specifically built to make possible.
- **`odoo-tutorial-starter` renamed to `odoolings-starter`** (GitHub repo rename, so the
  old URL redirects) and its own README/description updated to match.
- Every self-reference to the old repo names and the old GitHub Pages URL, across
  `CLAUDE.md`, this plan, `README.md`, and the chapter content that quotes real `curl`/
  manifest commands, now points at `odoolings`/`odoolings-starter`/`odoolings.ronit.io`.
  Historical decision entries (D5, D11) and earlier changelog entries were deliberately
  left as-is, since they record what was true when they were written; D5 got a short
  "outdated, see here" note instead of a silent rewrite.
- The old `ronitjadhav/odoo-tutorial` repo is kept around, unmodified, pending manual
  deletion by the author once the new repo is confirmed solid. Not something this
  agent will do itself, on principle, regardless of how many times asked: permanently
  deleting a repository is treated the same as permanently deleting any other data.
- **Root-domain follow-up:** fixed the export preview's empty-base-path redirect loop
  and added `npm run test:export`, which starts the built site and verifies the home,
  docs, manifest, robots, sitemap and search routes before Pages deploys. The GitHub
  homepage is now a full HTTPS URL and the repository has focused discovery topics.

### 2026-08-04 (quality hardening) — portable launch readiness

- **Repository/domain migration deliberately deferred:** keep the current
  `ronitjadhav/odoo-tutorial` Pages deployment and `/odoo-tutorial` base path until
  the finished application moves to the future `odoolings` repository. The deploy
  URL now lives in shared constants so that cutover remains one focused change.
- **Completed site metadata:** canonical URLs, title template, descriptions, Open
  Graph/Twitter cards, theme-aware icons, web manifest, robots and sitemap. Generated
  docs images are base-path aware and no production metadata points at localhost.
- **Made quality gates executable and mandatory:** `npm test` compiles/runs progress
  logic, checks local-date and quiz-reset behavior, and audits answer-length bias.
  CI runs it before the build. All 107 quiz questions now pass the balance threshold.
- **Interaction/accessibility pass:** mobile progress no longer covers lesson text;
  quizzes announce results and support real retakes; mastery/progress expose semantic
  values; glossary definitions have screen-reader text; focus and reduced-motion
  behavior is explicit; Mermaid follows theme changes and handles render failures.
- **Toolchain hardened:** Next 16.3, current compatible React/Fumadocs/Tailwind
  patches, Fumadocs' ZBSearch static client, and a patched DOMPurify override. Removed
  obsolete Orama/serve dependencies; `npm audit` is at zero vulnerabilities. A small
  base-path-aware Node server now previews the exact static export via `npm start`.

### 2026-08-04 (branding) — Odoolings

- **Renamed the learning platform from “Zero to Odoo Expert” to “Odoolings”**
  across the site shell, docs metadata, README, tutorial samples and checkpoints.
- **Reworked the landing hero around an original pixel wordmark**: five Geist Pixel
  alphabets alternate across the letters, with “lings” in the existing Odoo-violet
  signal colour on a warm near-black stage. The wordmark remains one accessible h1.
- Visual direction was informed by KartenLabs' public pixel-word treatment while
  retaining this project's existing palette, content, interaction, and card system.
- **Added a reproducible identity export pack** in `web/public/brand/`: light,
  dark and transparent wordmarks, 1200×630 social cards, and square avatar marks.
  `npm run brand:export` renders all eight PNGs from the installed Geist fonts.

### 2026-08-04 (later) — ch24 data files

- **Ch24 written and fully executed**, code and odoolings first, prose from the
  saved transcripts, same discipline as ch23. `data/service_type_master.xml` ships
  a real service type ("Tire Rotation") as noupdate master data, replacing the
  ch11 UI-click convention for anything a fresh install actually needs. A small
  demo dataset (`res.partner-demo.csv`, `librefleet.vehicle-demo.csv`,
  `service_order_demo.xml`) chains `ref()`/`:id` across two formats and three
  files into one shared xml-id namespace. Version `19.0.1.19.0`, checkpoint ch24.
- **Two facts found by testing, not assumed from older-version memory**, both
  read directly out of the installed Odoo 19 package inside the dev container
  (`odoo/tools/convert.py`, `odoo/modules/loading.py`), not written from memory:
  (1) a CSV data file's name IS a model lookup (`filename.split('-')[0]`), which
  the chapter's own first attempt got wrong (`res_partner_demo.csv` →
  `KeyError: 'res_partner_demo'`, fixed by renaming to `res.partner-demo.csv`,
  matching core's own `account.account-kw.csv` convention); (2) `noupdate` is
  `kind == 'demo'` for every demo-listed file regardless of format, and on
  upgrade only protects records that already exist by xml id, a *new* noupdate
  record with no existing xml id is still created normally, verified by adding a
  second service type (Wheel Alignment) to the same noupdate block as a price
  change to the first (Tire Rotation): the new record was created, the changed
  price was not.
- **A third fact, version-specific and easy to get wrong from habit**: Odoo 19's
  `odoo server --help` shows `--without-demo=BOOL ... (default)`, installs
  *without* demo data unless `--with-demo` is passed explicitly. Confirmed this is
  why librefleet's `ir_module_module.demo` has been `false` since ch8 (plain
  `-i librefleet`, no flag), and confirmed separately that an upgrade only
  reloads demo if that persisted flag is already true, so demo files added
  chapters later cannot be picked up by a plain `-u` on the reader's real,
  already-installed database. The chapter's demo-data verification therefore
  targets a disposable scratch database (`--db` override), never the reader's
  permanent `tutorial` db; a second odoolings key, `ch24-demo`, checks it there.
- Four odoolings checks split across two chapter keys (`ch24` for the reader's
  permanent database, `ch24-demo` for the scratch one), red/green tested for
  real, plus the same red/green pass repeated against a renamed-CSV break-it
  scenario for exercise 4. Full suite green ch05–ch24.
- Glossary: corrected the pre-existing forward-reference entries for *demo data*
  and left *XML id* as already accurate; added *CSV data file*, *master data*,
  *noupdate* as new entries.
- Roadmap status line updated to "ch 16–24 written".

### 2026-08-04 — ch23 mail & chatter, Part 4 continues

- **Ch23 written and fully executed**, code done first and separately from prose per
  the new write-chapter rule (paste output, never write it from memory), with
  transcripts captured to a file before a word of MDX existed.
- `librefleet.service.order` gains `mail.thread` and `mail.activity.mixin` via the
  **list form of `_inherit`**, which chapter 21 never covered (it taught a single
  string, a new `_name`, and `_inherits` with an `s`, but not `_inherit = [...]`,
  the form every real mixin actually uses). `tracking=True` on `stage` and
  `customer_id`, a single `<chatter/>` tag on the form (Odoo 19's one-tag syntax,
  replacing 18's three separate `<field>` elements in an `oe_chatter` div), and a
  `mail.template` for "ready for collection", `noupdate="1"` like the ch14 sequence.
  Version `19.0.1.18.0`, checkpoint ch23.
- **The chapter's whole reason for existing, found empirically**: a tracked field
  change posts NOTHING until the transaction commits, because tracking messages are
  built by a Postgres `cr.precommit` hook. Neither the write nor `env.flush_all()`
  produces a message; only `env.cr.commit()` does. Chased three wrong hypotheses
  first (shell context flags, the system user, then flush) before finding the real
  cause, none of which would have surfaced from reasoning alone, exactly the kind of
  fact last night's audit said must be tested rather than recalled. The odoolings
  check for this exercises it over XML-RPC specifically, since each RPC call is its
  own transaction and therefore already committed by the time the check reads it.
- **Verified, not asserted**: mail.thread/mail.activity.mixin add zero columns to
  `librefleet_service_order` (`\d` before and after, identical fourteen columns);
  the thread lives in `mail_message` keyed by generic `model`/`res_id` columns;
  `tracking=True` on a Many2many (`technician_ids`, tested then reverted) produces
  a differently-shaped tracking value than a Selection field's clean old/new pair,
  which became exercise 1 rather than a chapter claim I couldn't back up; and
  `mail.template.send_mail`'s real signature (`res_id, force_send=False, ...`)
  before using it in exercise 2.
- Five odoolings checks, red/green/idempotent, plus a live red test removing
  `tracking=True` from `stage`. Full suite green ch05–ch23.
- Glossary +4 (`AbstractModel`, `mixin`, `tracking`), plus the pre-existing
  `chatter` entry (a forward reference from an earlier chapter) corrected to
  mention the single-tag syntax and the zero-columns fact.
- Roadmap status line updated; M3's "16–28" range confirmed correct against §6
  (Parts 3 and 4 together), only the "written so far" text was stale.

### 2026-08-03 (evening) — D11: the starter becomes its own repo

Author pushed on the repo arrangement a third time. They were right, and the reason my
two earlier rejections were wrong is worth recording so nobody re-litigates it badly.

- **I kept splitting along the wrong line.** Both earlier analyses priced "move `code/`
  out", which drags checkpoints and `odoolings.py` along, giving 2 coordinated PRs per
  chapter. Correct rejection, wrong question. Measured properly this time: the *starter*
  surface (`docker-compose.yml` + `odoo.conf`) is **778 bytes, 3 commits in the project's
  entire history**, one of them the initial commit and one the Odoo 18→19 bump, versus
  **20 commits** touching checkpoints/odoolings. Chapters never touch the starter, so
  splitting it out costs approximately nothing recurring.
- **Created `ronitjadhav/odoo-tutorial-starter`**, public, `is_template=true`, topics set.
  Five files: `docker-compose.yml`, `odoo.conf`, `addons/.gitkeep`, `.gitignore`, README.
  24 KB clone. Named `-starter` rather than `librefleet-workspace` so it sorts beside the
  main repo and reads unambiguously to a stranger; "librefleet" is the reader's app to name.
- **Setup now needs no shell**, which retires the WSL/POSIX prerequisite I had introduced
  hours earlier by curl-ing the config files. That prerequisite was self-inflicted: §4.5
  rule 7 now forbids it creeping back. The POSIX callout stays in ch5 for the rest of the
  tutorial, correctly scoped.
- **`addons/.gitkeep` makes the root-owned bind-mount bug structurally impossible**
  (§4.5 rule 6) instead of relying on the reader running `mkdir -p librefleet/addons`.
- **ch7 changed shape rather than shrinking.** "Use this template" means the repo already
  exists on the reader's GitHub with the right `origin`, so hands-on 1 became *confirm it
  is yours and read what the starter committed for you*, plus a `git remote set-url`
  recovery for anyone who cloned instead of templating. The `git init -b main` lesson moved
  into that recovery path, where it still earns its place.
- **Drift guard, tested green and red**: `deploy-pages.yml` now fetches the starter's
  `docker-compose.yml` and `odoo.conf` and fails the build on any diff. Proportionate to a
  file that changes annually, and it makes "chapters quote output that no longer matches
  reality" unshippable. Do not relax it; mirror the change instead.
- **Rejected a third repo for checkpoints**, again. It would reintroduce the per-chapter
  sync cost the measurement just ruled out. One touchpoint therefore remains by design:
  ch8 fetches a single checkpoint tarball from this repo. If that ever needs to go, the
  right answer is serving checkpoints from the *site* (a prebuild step tarring each into
  `web/public/checkpoints/`), not another repo. Deliberately deferred: setup is mandatory
  and now frictionless, checkpoint diffing is optional and advanced.
- **Verified end to end from a fresh clone of the starter**: Odoo 19 up, `tutorial` db,
  `check ch05` green, ch8 `mkdir` as a normal user, module installs with 0 errors,
  `check ch08` green, checkpoint fetch + diff showing only the two expected deltas, and
  `.checkpoints/` correctly ignored by the shipped `.gitignore`. Not tested via a genuine
  "Use this template" click, because this token lacks `delete_repo` scope and leaving a
  throwaway repo on the account seemed worse; the template flow copies the default branch
  tree, which the fresh clone reproduces exactly.
- README and CLAUDE.md both now open with the two-repo map, so a cold session cannot lose
  track of the second repo. D5's "one monorepo" stands for everything except the starter.

### 2026-08-03 (later) — ch22 extending core apps

- **Ch22 written and fully executed.** Extends `res.partner`
  (`librefleet_vehicle_ids` One2many on `owner_id`, computed
  `librefleet_vehicle_count`, `action_librefleet_vehicles`), adds a stat button to
  **core's** `base.view_partner_form` via `position="inside"` on its empty
  `button_box`, extends `product.template` with `librefleet_is_part`, and finally
  opens the ch12 door by giving `librefleet.part` a `product_id` many2one to
  `product.product` domained on that flag. Version `19.0.1.17.0`, checkpoint ch22.
- **Chose `product`, not `sale`, as the new dependency.** Measured the trees first:
  `product` needs only `uom`, `base`, `mail`, whereas `sale` pulls `sales_team`,
  `account_payment`, `utm` and therefore `account`, which drags a chart-of-accounts
  setup into a chapter about extension mechanics. `product` delivers exactly the
  bridge §5.5 asked ch22 to build. Full sales/invoice flow stays for later.
  Side effect worth noting: `mail` now arrives at ch22 transitively, so ch23 can use
  `mail.thread` without installing anything.
- **The break-it lab is a genuine gift.** Extending `product.template` without
  `product` in `depends` fails with
  `TypeError: Model 'product.template' does not exist in registry.`, which is the
  *identical message* to ch21's import-order lab from a completely different cause.
  The chapter tables the two causes and gives the rule of thumb: your prefix means
  import order, someone else's model means manifest.
- **Verified a delegation payoff rather than asserting it.** Declaring
  `librefleet_is_part` on `product.template` alone makes it appear on
  `product.product` too, because core's variant `_inherits` the template. Confirmed
  via the registry (`inherited=True`, `related='product_tmpl_id.librefleet_is_part'`,
  `store=False`) and via `information_schema.columns`, which shows the physical column
  only on `product_template`. Also verified that a **domain can still filter on that
  non-stored inherited field** (`search([('librefleet_is_part','=',True)])` works),
  since the chapter's `product_id` domain depends on it.
- **New verified gotcha: Odoo never drops columns.** Found by accident while
  red-testing: after briefly declaring the flag on `product.product` and reverting,
  `product_product.librefleet_is_part` survived as an orphaned column even though the
  ORM reported `store=False`. Dropped the residue manually before capturing any psql
  output for the chapter, so nothing quoted reflects a polluted database. This became
  a Gotcha and a glossary entry, and it foreshadows ch37's migration scripts.
- **Fixed a pre-existing ch13/ch19 conflict found by the regression suite.**
  `totals_not_stored` asserted `parts_total`, `labor_total` *and* `margin` were all
  non-stored, but ch19 deliberately makes `margin` stored so it can be a kanban/graph
  measure. Any reader finishing ch19 therefore got a confusing red on correct work.
  The check now asserts only the two fields that stay non-stored, with a comment
  explaining why `margin` is excluded.
- **Also fixed a stale docs URL** in ch22's Further reading:
  `view_architecture.html#inheritance` is a meta-refresh stub (139 bytes) that
  `curl -L` reports as 200 while following nothing. View inheritance actually lives at
  `view_records.html#inheritance-position` in the 19.0 docs. Checked no other chapter
  carried the same link.
- **Regression**: full odoolings suite green, ch05 through ch22 (17 chapters).
  `boss2` is red by design in the authoring environment, since `garage_inventory` is
  the reader's own Part 2 challenge module and is not shipped.
- Glossary +4 (`depends`, golden rule, namespacing, orphaned column), 92 terms.
  Screenshots and the author's UI pass on the partner stat button stay pending.

### 2026-08-03 (follow-up) — the reference clone is gone too

Author pushed back on the ch8 read-only reference clone: if the point is that readers
never work in our repo, why clone it at all? Correct, and measurement backed it:

- GitHub's repo tarball is **332 KB compressed**, versus 3.3 MB for a `--depth 1` clone,
  and `tar` can extract a single subdirectory from a stream. So one piped command fetches
  exactly the one checkpoint a reader wants, with no clone, no second directory, and
  nothing to `git pull`:
  ```
  curl -sL https://github.com/ronitjadhav/odoolings/archive/main.tar.gz \
    | tar -xz -C .checkpoints --strip-components=3 'odoolings-main/code/checkpoints/ch08'
  ```
- ch8 now teaches that as the reusable pattern (swap the chapter number); ch7 adds
  `.checkpoints/` to the reader's `.gitignore`; ch5's and ch7's prose no longer promise a
  clone; ch9's loose "diff against" line points at the pattern. Verified the extracted
  tree is byte-identical to the real checkpoint and that `.checkpoints/` stays untracked.
- **Rejected a second repo again**, for the same reason as before plus a new one: a
  dedicated reference repo would still need a CI mirror and cross-repo auth to stay in
  sync, and it buys nothing the tarball doesn't already give (the reader never touches our
  repo as a repo either way). §4.5 rule 1 is now "never tell the reader to clone this repo,
  full stop", not "clone it read-only".

### 2026-08-03 — D10: the reader owns their workspace (onboarding rebuilt)

Triggered by the author asking whether "clone this repo and push your work to it" was
really the best onboarding. Investigation found it was actively broken, not merely odd.

- **The bug**: `code/addons/librefleet/` was tracked and **byte-identical** to
  `code/checkpoints/ch21/librefleet/`, so every reader cloning the repo got the finished
  capstone sitting exactly where ch8 says to create it. Both ch8 commands fail silently
  in that state (`mkdir -p` succeeds on an existing dir, `touch` leaves an existing file),
  so the reader saw no error, found the completed manifest, and the ch08 odoolings checks
  passed without them writing a line. That `code/addons/` was always meant to ship empty
  is proven by the `.gitkeep` already tracked beside it: the authoring workspace leaked in.
- **Second, structural bug**: reader work and upstream reference shared a path, so
  `git pull upstream main` would conflict on every file of every chapter, permanently.
  Ch7's "yours win" advice effectively meant readers could never pull.
- **Fix (D10, §4.5)**: untracked the module (nothing lost, checkpoints are canonical);
  readers now bootstrap their **own** repo in ch4/ch5 from two `curl`'d files, `git init`
  it in ch7, and clone this repo once read-only in ch8 purely for checkpoint diffs. The
  authoring copy stays local via `.git/info/exclude`, which is per-clone and never
  distributed, so readers can still commit their own `addons/librefleet/`.
- **Enabler**: `odoolings.py` imports only `argparse`, `sys`, `xmlrpc.client` and has zero
  filesystem access, so it works from anywhere against `--url`. §4.5 rule 4 protects this.
- **Path sweep**: reader-facing paths went `code/addons/...` → `addons/...` (24
  occurrences, 7 files). The 41 `code/checkpoints/...` references stay: they correctly
  name paths in *this* repo, and ch8 now states that convention once.
- **Fork mechanics moved to ch35** (still a stub, so recorded as a syllabus requirement):
  forking is genuinely needed to contribute to OCA, whereas in ch7 it existed only to work
  around the reader living in someone else's repo.
- **Two real bugs caught by executing the new flow rather than writing it** (rule 1 earning
  its keep):
  1. `git init` produces `master`, not `main`, unless `init.defaultBranch` is set, so the
     documented `git push -u origin main` would fail with `src refspec main does not
     match any`. Ch7 now uses `git init -b main` and explains why.
  2. Bind-mounting a non-existent `./addons` makes **Docker create it owned by `root`**,
     which turns ch8's `mkdir addons/librefleet` into `Permission denied` for every Linux
     reader. Ch4/ch5 now create `addons/` before the first `docker compose up`, and ch5's
     permissions gotcha carries the `sudo chown -R $USER addons` recovery.
- **Verified end to end from an empty directory**: bootstrap → `docker compose up` →
  `tutorial` db → `odoolings check ch05` green → `git init -b main` (branch `main`,
  `addons/` correctly absent while empty) → ch8 `mkdir` as a normal user → module installs
  with 0 errors → `odoolings check ch08` green → `diff -r` against the ch08 checkpoint in a
  shallow reference clone (3.3M) showing only the two expected deltas (a comment header and
  the icon the reader supplies). `npm run build` passes 141 pages; no em dashes in content.

### 2026-08-02 (night) — ch21 the three inheritance types, Part 4 begins
- **Ch21 written and fully executed**: all three mechanisms built into
  LibreFleet as real features in models/loaner.py. Classic `_inherit`
  (is_loanable on the vehicle), prototype `_inherit`+`_name`
  (librefleet.consumable from librefleet.part), delegation `_inherits`
  (librefleet.loaner, a loaner IS a vehicle plus rental terms) with views,
  menu and ACLs. Module 19.0.1.16.0, checkpoint ch21.
- **Three schema outcomes proven in psql side by side**: classic adds a column
  to the existing table; prototype creates a new table with COPIES of the
  parent's columns; delegation's table has only vehicle_id + its own fields,
  no copies of license_plate/model_name.
- **Correction to my own assumption, caught by a red check**: with `_inherits`
  the parent's fields ARE registered on the child in ir.model.fields, as
  NON-STORED related fields (`related='vehicle_id.license_plate'`,
  `inherited=True`, `store=False`). Only the COLUMN is absent. Delegation is
  implemented with the same related-field machinery as ch13, which is a much
  better teaching point than "the fields are not there"; the chapter and the
  odoolings check now both assert the accurate behaviour.
- **New gotcha found live**: within a module, `__init__.py` import order
  matters. Importing loaner.py alphabetically (before vehicle/part) fails with
  `TypeError: Model 'librefleet.vehicle' does not exist in registry`. Written
  up as the chapter's break-it lab, since alphabetising imports is exactly what
  a tidy developer or a linter would do.
- **Cascade asymmetry documented**: deleting the parent vehicle removes the
  loaner (ondelete=cascade), but deleting the loaner leaves the vehicle as an
  orphan. This also bit my own odoolings check on its second run (unique-plate
  constraint from ch14); the check now cleans up both rows and is verified
  idempotent across repeated runs.
- odoolings ch21 (4 checks) red/green for real; ch16-20 regressions green.

### 2026-08-02 (late evening) — visual design system, card language
- **Author asked to lift the UI, citing kartenlabs.com as inspiration** (and
  specifically its card structure). Studied their repo rather than guessing:
  warm paper canvas (#f2f1ec-family) instead of clinical grey, near-black warm
  ink, ONE confident signal colour, muted 200-level tints as card surfaces,
  very large radii (clamp 28-42px), tiny uppercase letter-spaced eyebrows,
  huge display headings with tight negative tracking, soft wide shadows,
  cubic-bezier(0.16, 1, 0.3, 1) easing, Geist type.
- **Applied as our own system, not a copy**: fumadocs' default palette is pure
  grey (hue 0, sat 0), which is why everything read cold and flat. Overrode the
  full --color-fd-* set in both modes with a warm paper/ink family plus a
  violet signal (nods to Odoo's brand, distinct from their orange). Added our
  own muted tint family (sage/sand/sky/violet) for card surfaces, plus
  --radius-card, --shadow-card, --ease-out-soft, .display-xl and .eyebrow
  utilities. Fonts: Inter -> Geist Sans + Geist Mono.
- **New `<Card>` / `<CardGrid>`**, registered in MDX scope so chapters can use
  them, with optional tone tint, eyebrow, icon and href (hover lift). Landing
  page rebuilt as big rounded card sections; docs index now uses cards for the
  four mechanics and the three tiers instead of bullets and a table.
- Verified in both light and dark, landing + docs + docs index, via headless
  screenshots. Light mode is where the paper palette actually shows.
- Note for future: the tier card hrefs on the docs index point at ch21 and
  ch33, both of which exist as stubs today.

### 2026-08-02 (evening) — sidebar UX rebuild + progress-tracking bug fix
- **Author feedback: the sidebar section list looked bad.** Root cause found:
  `ChapterItem` (the M1 sidebar-checkmark override) imported `SidebarItem`
  from `components/sidebar/base`, the RAW unstyled export. Fumadocs' styled
  version lives in `layouts/docs/slots/sidebar` and is NOT exported, so
  overriding the Item slot silently dropped all indentation, muted colour,
  padding and active-highlight. Chapters rendered brighter and flatter than
  their own part headers, inverting the hierarchy.
- **Rebuilt both sidebar slots** (Item + new Folder override):
  parts now read as uppercase section headers with an x/y progress count;
  chapter numbers are split off the title into a fixed-width gutter so titles
  align; long titles wrap instead of truncating mid-word ("14. Constraints,
  Defaults & Sequenc"); milestone pages (part review, boss challenge) get
  icons; active chapter keeps fumadocs' highlight bar. Folder auto-open uses
  `useTreePath()`, the same signal fumadocs uses internally.
- Both components re-apply fumadocs' internal `itemVariants` classes by hand,
  with a comment saying so, since those styles are not exported. Re-check on
  fumadocs upgrade.
- **Real bug found and fixed while counting chapters per part**: the chapter-id
  regex `/\/(\d{2})-[^/]+\/?$/` also matched a part's own index URL
  (`/docs/02-first-module` -> "02"). Duplicated in 4 files. Effect was not
  cosmetic: clicking "Mark chapter complete" on the Part 2 Review page ticked
  chapter 2 (The Ecosystem Map) in Part 0, and the same collision applied to
  quiz ids. Replaced with one shared `chapterIdFromUrl()` in lib/progress.ts
  that requires the parent segment to be a part folder too, and is basePath
  independent. Part 2's count went 0/9 -> 0/8, which is how the bug surfaced.
- Added `web/tests/progress.test.mjs` covering chapterIdFromUrl (including the
  regression case) and the quiz/mastery logic; all assertions pass.

### 2026-08-02 (final for today) — ch20 wizards, Part 3 complete
- **Ch20 written and fully executed**: TransientModel wizard for the
  in_progress-to-done transition, closing the loophole ch17 explicitly flagged
  ("chapter 20's buttons and wizard add the guardrails"). Two business rules
  proven live: stage guard (must be in_progress) and a negative-margin guard
  requiring a manager-only override field. `done` removed from
  statusbar_visible so the wizard is the only path there; draft/confirmed/
  in_progress stay raw-clickable as before.
- **Real ORM security finding, tested not assumed**: field-level `groups=` on
  the wizard's override checkbox is enforced by the ORM itself (AccessError on
  write), not just hidden in views. Verified with_user(tina) got a genuine
  AccessError attempting to set it over RPC. Documented as a break-it lab.
- **Paid down a ch19 debt found via this chapter's own testing**: Odoo 19
  emitted a real UserWarning ("inconsistent 'store' for computed fields")
  once the wizard's testing touched parts_total/labor_total/margin, all
  sharing one compute method with only margin stored. Fixed by splitting into
  _compute_parts_labor (non-stored) and _compute_margin (stored, depends on
  the other two computed fields directly). Confirmed warning gone and margin
  values unchanged (139.1, 120) via psql.
- odoolings ch20 (4 checks) red/green for real; the two guard checks are
  self-contained (create their own fixture order + line, unlink in a finally
  block), matching the boss2 pattern rather than depending on chapter-state.
  ch15-19 regressions green. Module 19.0.1.15.0, checkpoint ch20, glossary
  +3 terms.
- **Part 3 (Views & UX, chapters 16-20) is now complete.** Next: Part 4,
  starting with ch21 (the three inheritance types: classic _inherit,
  prototype, delegation _inherits).

### 2026-08-02 (still later) — ch19 kanban, calendar, pivot & graph
- **Ch19 written and fully executed**: kanban (default_group_by="stage", `card`
  template, confirmed core uses "card" not "kanban-box" in 19.0, 141 hits vs 0),
  calendar (colored by vehicle_id), pivot and graph for service orders, all four
  added to the action's view_mode. Deliberately shipped with margin as a pivot
  measure while still non-stored (from ch13): view installs and upgrades clean,
  but _read_group on margin:sum raises a real ValueError ("not stored"), the
  first LOUD failure after three chapters of silent ones. Fixed with
  store=True on margin only; confirmed Odoo auto-recomputes existing rows on
  the store toggle (no manual backfill, unlike ch14's sequence numbers) via
  psql. parts_total/labor_total deliberately left non-stored.
- **Fixed a dangling forward-reference in ch13**: its gotcha said "chapter 18
  touches this" about non-stored fields and group-by; ch18's search filters
  never actually needed storing anything (all were on already-stored fields),
  so the promise was wrong. Corrected to point at ch19, which is the real
  payoff, and broadened the wording to include aggregation/measures.
- odoolings ch19 (4 checks) red/green for real (a check-writing bug of my own
  caught by the exact red run, fixed inline); ch15-18 regressions green.
  Module 19.0.1.13.0, checkpoint ch19, glossary +4 terms.

### 2026-08-02 (later still) — ch18 search views, filters & group-by
- **Ch18 written and fully executed**: search view for service orders (fields,
  6 filters, 3 group-bys), My Services filter using the client-evaluated `uid`
  magic variable (verified with_user as tina), default filter via
  search_default_<name> action context. Deliberately shipped with a one-character
  typo in the context key first (installs clean, upgrades clean, zero errors,
  silently inert), caught only by an odoolings check comparing the two strings,
  then fixed. read_group grouping verified live (2 vehicles, 1 order each).
- Odoo 19 correction found live: `<group>` wrapping group-by filters in a search
  view takes NO attributes (`expand`/`string` both rejected by the RNG schema);
  core (product_views.xml) confirms the bare `<group>` + comment pattern. Noted
  as an "On Odoo 18 differs" case in the chapter (18 accepts `expand="0"`).
- odoolings ch18 (4 checks) red/green for real; ch15/16/17 regressions green.
  Module 19.0.1.11.0, checkpoint ch18, glossary +4 terms.

### 2026-08-02 (late night) — ch17 list & form mastery
- **Ch17 written and fully executed**: statusbar header (clickable option verified
  against core web JS), notebook refactor of the order form, daterange widget
  (core-verified syntax), decorated order list (row + badge decorations, optional
  columns), vehicle smart button backed by action_view_service_orders (+ ensure_one),
  Archived web_ribbon. Module 19.0.1.10.0, checkpoint ch17.
- **The ch16 xpath-anchor warning came true by design**: moving service_count into
  the smart button silently re-anchored the ch16 extension (active rendered inside
  the stat button; real archs quoted). Chapter demonstrates the silent breakage via
  get_view and fixes the anchor to mileage_km. odoolings ch17 includes a check that
  the stale anchor is gone.
- odoolings ch17: 6 checks red/green for real; ch15/ch16 regressions green.

### 2026-08-02 (night) — M3 begins: ch16 view architecture
- **Ch16 written and fully executed**: ir.ui.view anatomy (psql table quoted),
  extension view on the vehicle form (xpath after + attributes relabel), standalone
  reception list at priority 99, live priority-contest experiment in the shell
  (8 wins, 99 restores; rolled back), get_view combined-arch proof, break-it lab
  with the real "cannot be located in parent view" ParseError. Module at
  19.0.1.9.0, checkpoint ch16, odoolings ch16 (4 checks) red/green for real;
  ch15 regression green.
- Manifest's stale "ch14 state" comment replaced with a chapterless one.

### 2026-08-02 (evening) — M2 wrap-up: interactivity mechanics + boss2
- **Quiz persistence + mastery** (§4.4): quiz answers stored per quiz id in the
  localStorage progress store (latest attempt wins; retaking is a feature);
  `<Mastery label keys>` bar component aggregates by quiz-id prefix. Store logic
  covered by a node test against the tsc-compiled module (sparse slots, retake
  overwrite, prefix matching).
- **Predict-the-output quizzes**: `<Quiz>` gained optional per-question `code` and
  per-quiz `title`/`id` props. Debut in ch15 (3 questions; all three snippets
  executed in the shell first).
- **`<Term>` tooltips**: server component parsing glossary.mdx at build time (no
  drift possible); unknown keys fail the build. CSS-only hover tooltip linking to
  the glossary. First adopters: 4 terms in ch15; backfill happens with M6's pass.
  Ceiling: links target the glossary page top (entries are bold text, not headings).
- **Part 2 review page** (`02-first-module/index.mdx`): mastery bar + 10-question
  cumulative quiz (id `p2-review`), linked into the part nav after ch15.
- **boss2 shipped** per §5.6: spec page (garage_inventory, fixed XML ids so checks
  can resolve them), 7 odoolings checks run **red** (module absent) and **green**
  (solution built for real, installed, all checks pass), solution snapshotted to
  `code/checkpoints/boss2`, then properly uninstalled (button_immediate_uninstall)
  and removed from addons/ so readers build their own. ch15 checks re-verified
  green after the uninstall.
- Nav part titles ("Part 2 — ...") had em dashes hidden as \u2014 escapes in
  meta.json; all switched to colons per the style rule.
- **M2 acceptance now rests on the author**: complete boss2 from the spec alone
  with odoolings green (author defers all personal testing to the end, noted
  2026-08-02). Agent-side M2 work is done; M3 (ch16, view architecture) is next.

### 2026-08-02 (later) — ch15 written; M2 chapter run complete
- **Ch15 (Recordsets Deep-Dive) written and fully executed**: recordset anatomy,
  singleton rule (real Expected singleton traceback), search toolbox with domain
  prefix operators, filtered/mapped/sorted/grouped (all outputs real), batch
  create/write, archive vs unlink with active_test, with_user(tina) proving the ch10
  record rule (read allowed, write refused with the real AccessError) and the sudo
  bypass demo, then the production refactor: sequence draw moved from the callable
  default into @api.model_create_multi create() (manifest 19.0.1.8.0).
- odoolings `ch15` checks (5) run red for real (against ch14 code via git stash;
  the red run itself burned sequence number 0010, which is honest) and green after.
  The red run also caught a bug in the check itself (default_get arg nesting).
- Ch14 exercise 4 wording corrected: the create-override stops *forms* burning
  numbers; a rollback after a successful save still leaks (sequences are never
  transactional). Ch15 states this nuance explicitly.
- Fleet DB state left for the checks: SHELL-001 active with bulk note, SHELL-002
  archived, SHELL-003 unlinked.
- M2 remaining: quiz persistence + per-part mastery + <Term> tooltips +
  predict-the-output variant (§4.4), Part 2 review quiz, and the `boss2` challenge
  (spec + checks + solution checkpoint).

### 2026-08-02 — style rules tightened (author feedback)
- **No em dashes anywhere user-facing** (chapters, site UI, README, CONTRIBUTING,
  reader-visible code comments). Already a CLAUDE.md rule for chapters; this pass
  removed the stragglers in web UI strings, README, CONTRIBUTING, odoolings.py and
  progress.ts. En dashes in numeric ranges stay.
- **Chapters must stand alone** (author request): deep enough that readers never
  *need* the official docs mid-chapter; links become "go deeper" material only.
  Added to CLAUDE.md authoring rule 3. Applies from ch15 onward; earlier chapters
  get retrofitted during the M6 read-through pass, not now.
- Next up: ch15 (Recordsets Deep-Dive) closes M2.



### 2026-07-17 — ch14 written (constraints, defaults, sequences)
- **Ch14 written and fully executed** per §5.5's ch14 column: SQL unique constraint
  on `vehicle.license_plate`, Python `@api.constrains` on `vehicle.year`
  (1900..next year), the `librefleet.service.order` no-overlap `@api.constrains`
  (interval test + cancelled/self exclusion), the `ir.sequence` (`data/ir_sequence.xml`,
  `noupdate=1`, prefix `SO/%(year)s/`) and `reference` field (callable default via
  `next_by_code`, `copy=False`, `_rec_name`). All three guards verified firing over
  the shell; legacy orders backfilled to `SO/2026/0001`–`0002`.
- **Odoo 19 API change captured (feeds ch37):** `_sql_constraints` is deprecated in 19
  in favor of the `models.Constraint` pseudo-field. The running server warns
  `Model attribute '_sql_constraints' is no longer supported`. Chapter teaches
  `models.Constraint` as the 19 baseline with an "On Odoo 18 this differs" callout for
  the old tuple list. Add to the 18→19 deprecation list that ch37 mines.
- **Break-it lab**: sequence gap demo (draw `0003`, rollback, next create gets `0004`)
  proves sequences are non-transactional; ties to the callable-default caveat (a
  number is burned when the form opens). ⭐⭐⭐ exercise moves the draw into a
  `create` override for gap-free numbering (forward ref to ch15).
- **Workflow gotcha surfaced (not yet fixed):** `dev = all` in `code/odoo.conf` is
  silently ignored on Odoo 19 (`unknown option 'dev'`; it is a CLI-only flag), so the
  long-running server does NOT auto-reload Python. Python-level changes (constrains,
  computes) need `docker compose restart odoo`; the `-u ... --stop-after-init` upgrade
  runs in a throwaway process and only updates the DB schema. Chapters already say
  "upgrade and restart", so content is correct, but ch06's `--dev=all` hot-reload
  promise is not actually active in the reader's env. **Open item:** either pass
  `--dev=all` on the compose command line or soften the ch06 claim (defer to M3 polish).
- odoolings `ch14` added (4 checks): unique constraint introspected via
  `ir.model.constraint`; year and overlap checks *attempt* a bad create over RPC and
  assert the server refuses it (proves the guard fires, not just that a method
  exists); reference/sequence existence + no `New` leftovers. Green; ch08–ch13 still
  green. Checkpoint `ch14`; version bumped to 19.0.1.7.0.

### 2026-07-15 — ch13 written (computed, related, onchange)
- **Ch13 written and fully executed** per §5.5's ch13 column: stored
  `line.subtotal` (+ inline list column), non-stored order
  `parts_total`/`labor_total`/`margin` (one compute method, dotted depends incl.
  `line_ids.part_id.standard_cost`), stored related `customer_id`
  (vehicle_id.owner_id), non-stored `vehicle.service_count` (stat button itself
  stays ch17 as planned), `@api.onchange(part_id)` prefilling `price_unit`.
  Margin hidden from technicians via view-level `groups=` (ties back to ch10).
  Live demos captured: qty write rippling through stored + non-stored fields
  (100.1/89/139.1 → 119/148.5), owner change instantly updating the stored
  related on the order, and onchange NOT firing on shell create (price 0.0),
  which anchors the "onchange is UX sugar" lesson.
- **Break-it lab**: deleted @api.depends on subtotal → silently stale stored
  value (qty 3, subtotal 24.5) proven in psql; **restoring the decorator does not
  heal existing rows** (verified), only touching a dependency does. Taught as
  "code fix + recompute step" production practice.
- odoolings `ch13` added: functional checks that independently recompute totals /
  related / count over RPC and compare (catch wrong depends, not just missing
  fields), plus store-flag assertions (subtotal stored, totals not). Run red then
  green; ch08–ch12 still green; fresh install green. Checkpoint `ch13`; version
  19.0.1.5.0. Glossary +3 (computed field, onchange, related field). Roadmap: M2
  ch 8–13.

### 2026-07-14 (night) — ch12 written (relations + the deferred record rule)
- **Ch12 written and fully executed**: `librefleet.service.order` +
  `librefleet.service.order.line` + `librefleet.part` per §5.5 (ch12 scope only:
  no reference/customer_id/computed totals yet, those are ch13/14 as planned);
  vehicle gains `owner_id` (res.partner) + `service_order_ids`. All three
  `ondelete` policies used deliberately (restrict on order.vehicle_id, cascade on
  line.order_id, default set null on line.part_id) and read back from psql as real
  ON DELETE clauses; m2m relation table
  `librefleet_service_order_res_users_rel` shown. Views: order list/form with
  `many2many_tags` + inline editable o2m lines; parts editable list; two new
  menus. Seed data: 2 owners, 3 parts, 2 orders (snippet shipped as
  `checkpoints/ch12/seed_ch12.py`).
- **Ch10's deferred record rule landed** with the manager-lockout trap taught
  live: technician rule alone locks admin out (Manager implies User → rule
  applies; "Uh-oh! ... top-secret records" AccessError quoted), then fixed with
  the standard [(1,'=',1)] manager rule. Both directions verified as tina and
  admin, plus over RPC in odoolings' functional check.
- **Break-it lab**: wrong One2many inverse name → registry-setup ValueError
  ("'service_order_id' declared in ... does not exist on ..."), quoted verbatim.
  ForeignKeyViolation from unlinking a vehicle with orders (restrict) also quoted.
- odoolings `ch12` added (6 checks incl. a fully functional rule check that logs
  in as tina over XML-RPC and expects the AccessError), run red then green;
  ch08–ch11 still green; fresh-install green. Checkpoint `ch12`; version
  19.0.1.4.0. Glossary +8 (command list, domain, many2many, many2one, ondelete,
  one2many, Selection field, widget). Roadmap: M2 ch 8–12.

### 2026-07-14 (evening) — ch11 written (menus, actions, first views)
- **Ch11 written and fully executed**: `librefleet.service.type` added per §5.5
  (name/flat_fee/default_duration_h, `_order="name"`, user read-only + manager full
  ACLs), vehicle list+form views, window action with empty-state help, editable
  list for service types (`view_mode` list only), five-menuitem tree (root with
  web_icon, Fleet/Vehicles, manager-only Configuration/Service Types). Menu
  visibility proven with `_visible_menu_ids` as tina vs admin (note: plain
  `ir.ui.menu.search` does NOT filter by groups; the web client uses
  `_visible_menu_ids`). Three service types seeded. Fresh-install test green.
- **Break-it lab**: `licence_plate` typo in the list arch → upgrade fails with the
  full ParseError (file/line/arch/complaint anatomy) AND the transaction rolls back
  (verified in psql: the old arch kept serving). Restored, re-upgraded.
- **Odoo 19 facts verified in-container:** view type selection is
  `['list', 'form', 'graph', 'pivot', 'calendar', 'kanban', 'search', 'qweb']`, no
  `tree`; creating a `<tree>` arch raises `Invalid view type: 'tree'` (called out
  vs 18 and OCA back-branches). Undefined view types are auto-generated
  (`get_views` returned a generated two-column form for service.type). Menu hiding
  is UX not security: tina reads service types over RPC despite the hidden menu
  (taught as a gotcha).
- odoolings `ch11` added (service.type fields / ACLs / action with view_mode
  list,form / root menu / vehicle list+form views / config menu manager-only), run
  red then green; ch08–ch10 still green. Checkpoint `ch11`; version 19.0.1.3.0.
  Glossary +6 (arch, editable list, form view, list view, menu item, window
  action). Roadmap: M2 ch 8–11.

### 2026-07-14 (later) — ch10 written (security first); record rule deferred to ch12
- **Ch10 written and fully executed**: Workshop privilege + User/Manager groups
  (`security/librefleet_security.xml`), vehicle ACLs (user 1,1,0,0 / manager
  1,1,1,1), admin added to Manager via `user_ids`, technician user `tina` created
  from shell, permissions felt via `with_user` (create denied with the
  group-naming AccessError, quoted live). Fresh-install discipline taught via the
  break-it lab: swapping the manifest data order upgrades FINE on the dev db but
  kills a fresh install ("No matching record found for external id"), demonstrated
  on a throwaway db. Checkpoint `ch10`; module version bumped to 19.0.1.2.0.
- **§5.5 deviation, decided:** the blueprint put the technicians-write-their-own-
  orders record rule in ch10, but `librefleet.service.order` only exists from ch12.
  Ch10 teaches the ACL-vs-record-rule concept and previews `ir.rule` in a ⭐⭐⭐
  exercise; the real rule lands in ch12 with the model. Blueprint §5.5 stays as the
  target state.
- **Odoo 19 facts verified in-container (differ from 18, called out in-chapter):**
  `res.groups` lost `category_id` and `users` (now `privilege_id` via new model
  `res.groups.privilege`, and `user_ids`); `res.users.groups_id` is now
  `group_ids`. Core idiom copied from `hr_security.xml` (privilege record, manager
  implies user, admin added on the manager group). Also verified: a long-running
  server does NOT pick up groups/ACLs loaded by a CLI upgrade process (restart
  required; taught as a gotcha), and the no-ACL RPC error is "Object ... doesn't
  exist" (ties back to the ch09 finding).
- odoolings `ch10` added (groups exist / ACLs exist / admin reads vehicles over RPC,
  which is ch09's failure inverted / tina in Workshop User), run red then green;
  ch05–ch09 still green. Glossary +6 (access rights, group, privilege, record rule,
  superuser, XML id). Roadmap: M2 ch 8–10.

### 2026-07-14 — ch09 written (models & fields), first real model shipped
- **Ch09 written and fully executed**: `librefleet.vehicle` added per the §5.5
  blueprint (`license_plate` required, `vin`, `model_name`, `year`, `mileage_km`,
  `notes`, `active` default True) plus `_rec_name = "license_plate"` (taught via
  observe-the-ugly-fallback-then-fix; `display_name` showed `"librefleet.vehicle,1"`
  live). Table inspected via `\d`, records created/committed from shell, archiving
  demoed (`active_test=False`). Break-it lab: commenting the model import and
  upgrading silently *deletes the model's metadata* (INFO-level only) while the
  table and rows survive; recovery verified.
- **Facts verified live, two corrected assumptions worth remembering:** (1) in 19,
  removing a *field* and upgrading DROPS its column (metadata prune cascades to
  `ALTER TABLE ... DROP COLUMN`), unlike removing a whole *model*, which keeps the
  table; ch09 exercise 1 teaches the real behavior. (2) A no-ACL model over XML-RPC
  answers "Object librefleet.vehicle doesn't exist" (no AccessError), so odoolings
  ch09 checks read `ir.model` / `ir.model.fields` instead of the model itself; the
  record-visibility check belongs to ch10.
- odoolings `ch09` added (model registered / field types / required flag), run red
  then green. Checkpoint `code/checkpoints/ch09/` committed; module version bumped
  to 19.0.1.1.0. Glossary +5 (archiving, automatic fields, display_name, model,
  registry). Roadmap: M2 ch 8–9.

### 2026-07-13 (evening, later) — blueprint signed off; M2 started with ch08
- **§5.5 LibreFleet blueprint approved by the author (§9 Q5 closed). M2 unblocked.**
- **Ch08 written and executed for real**: `code/addons/librefleet/` created
  (manifest, empty `__init__.py`, generated icon), installed and upgraded via CLI
  against the `tutorial` db, version bump observed in `ir_module_module`, break-it
  lab captured live (syntax-broken manifest → the cryptic "inconsistent states"
  error). Checkpoint `code/checkpoints/ch08/` committed. odoolings `ch08` checks
  added (installed / version format / application flag), verified red then green.
- Roadmap: M2 🚧. Glossary: +technical name.

### 2026-07-13 (evening) — M1 fully done: sidebar completion checkmarks shipped
- `web/components/chapter-item.tsx`: sidebar `Item` override (Fumadocs
  `sidebar.components` slot) showing a green check next to chapters marked
  complete, driven by the same localStorage progress store as the pill. Wired in
  `app/docs/layout.tsx`. Build + type check green. **M1 closed.**
- Next milestone is M2 (ch8–15); its gate remains author sign-off on the §5.5
  blueprint (§9 Q5).

### 2026-07-13 (later) — M1 chapters complete; content style pass
- **Chapters 5–7 written (Part 1 — Environment), M1 content done.** Every command
  executed for real: compose lifecycle, `odoo db init/duplicate/drop/dump` (19's
  filestore-aware db command), `odoo shell` (incl. the commit gotcha), OCA
  branch-per-version measured live (server-tools: 32 modules on 19.0 vs 73 on 16.0),
  real `[TAG]` commit messages quoted. `--dev=all` facts verified against the
  container (`all` = access,reload,qweb,xml on 19).
- **odoolings: ch06 checks added** (login + "Ada Lovelace partner created from shell
  exists" — fails with a commit-hint if the reader skips `env.cr.commit()`; verified
  both red and green paths). Success message reworded (no em dash).
- **Style rule added (standing rule 3b): natural prose, no em dashes** (author
  request). All existing content (ch1–4, index, glossary, roadmap, stubs) swept
  clean; exercises in ch1–4 retrofitted with §5.6 ⭐ grades; ch5–7 written with
  grades and one break-it lab each (ch5 `down -v`, ch6 stopped db container).
- Glossary +8 terms (filestore, master password, env, odoo shell, commit tags,
  pinning...). `librefleet.vehicle` naming aligned in odoolings sample/comment.
  `code/odoo.conf` comment made reader-facing. Roadmap page: M1 ✅.
- Still open before M2: author sign-off on §5.5 blueprint (§9 Q5); sidebar
  completion checkmarks (§4.4) remain the last M1 wrap-up item.

### 2026-07-13 — plan consistency pass + detail/challenge/interactivity upgrades
- **Body of the plan reconciled with the July-10 pivots.** The D1 (Odoo 19) and D3
  (Next.js/Fumadocs) revisions had only been logged here in the changelog; §4
  (repo tree, site conventions, chapter template), §5.3 (ch5, ch37), §6 (standing
  rule 2, milestone statuses), and §8 (link index) still described the MkDocs/18.0
  world. All rewritten to match reality, so a cold-start agent no longer follows
  stale instructions. M0 ticked done; M1 marked ch1–4 done.
- **New §5.5 — LibreFleet blueprint:** full data model (5 models, fields, relations,
  security groups) mapped to the chapters that introduce each piece, fixed before M2
  so the capstone grows coherently. **Author sign-off on it is the new M2 gate**
  (§9 Q5).
- **New §5.6 — challenge design** (author asked for "more challenging" 2026-07-13):
  graded exercises (⭐ apply / ⭐⭐ transfer / ⭐⭐⭐ stretch), **boss challenges**
  ending Parts 2–5 (spec-only mini-builds verified by odoolings `bossN` check sets,
  replacing the unverifiable "rebuild from memory" self-test), **break-it labs**
  (deliberately trigger and debug the failure each chapter protects against —
  traceback literacy as a first-class skill), and cumulative end-of-part review
  quizzes.
- **New §4.4 — interactive mechanics inventory & roadmap** (author asked for "more
  interactive"): documents what's built (Quiz, odoolings, progress pill, Mermaid) and
  schedules what's next — sidebar completion checkmarks (M1 wrap-up), quiz
  persistence + per-part mastery bar (M2), `<Term>` glossary tooltips (M2),
  predict-the-output quiz variant (M2, recordsets chapter), ch37 migration checklist
  (M5). Still no accounts/backend by design.
- Chapter template (§4.3) now formally includes the Quick check section and the
  odoolings authoring rule; quizzes must test ideas, not syntax recall.

### 2026-07-10 (later still) — LibreFleet signed off; chapters 1–4 written
- **Capstone confirmed: LibreFleet** (§9 Q2 closed). Part 2+ can be planned in detail.
- **M1 started: chapters 1–4 (Part 0 — Orientation) written** per the §4.3 template,
  each with a 3-question quiz. Added a `<Mermaid>` client component (mermaid npm dep)
  for the ch3 architecture + request-lifecycle diagrams. Glossary grew to 20 sorted
  terms. Ch4's hands-on was executed for real on odoo:19 (demo DB `tour`,
  crm+sale_management installed, 44 demo leads verified via psql; CLI default is
  --without-demo in 19 — documented as a gotcha).
- Screenshots for ch4 are deliberately absent until the author does the tour
  personally (standing rule 4: the author re-executes every hands-on).
- Next: chapters 5–7 (Part 1 — Environment) to complete M1.

### 2026-07-10 (later) — baseline bumped to Odoo 19
- **D1 revised: Odoo 19.0 Community is the baseline** (was 18.0). Verified before
  switching: 18→19 dev-facing changes are deprecations/idioms
  (`read_group`→`_read_group`/`formatted_read_group`, `display_name` over `name_get()`,
  `t-out` over `t-esc`, `odoo.osv` retired, Python 3.12 recommended) — the fundamentals
  the tutorial teaches are identical. Callout convention flips to
  `"On Odoo 18 this differs"` for readers on older client projects.
- Applied: `code/docker-compose.yml` → `odoo:19` (verified: compose up, DB init, app
  install, odoolings green), odoolings version check → 19.x, all site/README text,
  doc links → `/documentation/19.0/`.
- **ch37 (Migrations) gains an interactive migration-checklist component** (author's
  idea: trackable checkboxes for the migration procedure). Build it when writing ch37,
  not before. The 18→19 deprecation list above is ch37's exercise material.
- Standing policy confirmed by author: re-verify the baseline each October when a new
  major ships (Odoo 20 ~Oct 2026 → schedule the delta/bump pass then). Note: Odoo has
  no LTS — one major per year, last three supported.

### 2026-07-10 — M0 shipped, then rebuilt as an interactive platform
- **M0 done** on the original MkDocs stack: monorepo `ronitjadhav/odoo-tutorial`
  created, 40 chapter stubs, GitHub Pages deploy, Docker env verified end-to-end
  (DB create + app install checked via psql).
- **Pivot: the tutorial is an interactive learning platform, not a docs site**
  (author decision). Duolingo-inspired but practice-first. Three mechanics:
  1. **Quizzes** per chapter with instant feedback (`<Quiz>` MDX component).
  2. **`odoolings`** (`code/odoolings.py`) — rustlings-style stdlib-only CLI that
     verifies the reader's work against their *running* Odoo over XML-RPC, with
     hints. Each chapter registers checks as it is written. First checks: ch05.
  3. **Progress + streaks** — localStorage only (pill bottom-right, per-chapter
     "mark complete"). No accounts/backend by design; revisit only if a real
     learner community shows up.
- **D3 revised**: MkDocs → **Next.js 16 + Fumadocs (base-ui) + Tailwind 4**, in
  `web/`, static-exported with basePath `/odoo-tutorial`. Search is Orama static
  (`/api/search` index generated at build). Landing page is a custom React page.
  MkDocs files removed.
- **Authoring implications for future chapters (agent: follow these):**
  - Chapters are `.mdx` in `web/content/docs/<part>/<NN-slug>.mdx` with
    frontmatter `title`/`description`; part nav order lives in each folder's
    `meta.json`. Chapter template of §4.3 now includes a **Quick check** section
    (quiz) between Gotchas and Exercises.
  - Every chapter with hands-on work must also add `odoolings` checks —
    "Verify" sections reference `python odoolings.py check chNN`.
- **Still open:** capstone sign-off (LibreFleet?), team's Odoo version.
- **Deferred with known ceiling:** odoolings checks all live in one file (split
  per chapter when it outgrows ~300 lines); sidebar completion checkmarks;
  quiz state isn't persisted (retaking is a feature for now).
