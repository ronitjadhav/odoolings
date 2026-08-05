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
- Diagrams: the `<Mermaid>` client component (architecture, request lifecycle, ERDs).
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
5. **Fork mechanics** (`git remote rename origin upstream`, etc.) belong in ch35 where
   they fork an OCA repo to submit a real PR, not in ch7 where they used to exist only
   to work around living in someone else's repo. The starter is a **template**, not a
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

### 5.4 Concept coverage checklist (agent: verify before calling the syllabus done)
ORM CRUD ▢ recordsets ▢ env/context ▢ compute/related/onchange ▢ constraints ▢
sequences ▢ all 3 inheritance types ▢ view inheritance/xpath ▢ all view types ▢
wizards ▢ security (groups/ACL/record rules/sudo) ▢ mail.thread ▢ cron ▢
server actions ▢ QWeb reports ▢ controllers ▢ portal ▢ OWL component ▢ widget ▢
assets ▢ tests (unit + tour) ▢ data files/noupdate ▢ i18n basics ▢ pre-commit/OCA
conventions ▢ migration exercise ▢ performance patterns ▢ deployment concepts ▢

Functional coverage (added 2026-08-05, D12; Parts 4-5):
partner/company model ▢ product.template vs product.product + variants ▢ UoM ▢
sale.order lifecycle ▢ CRM pipeline ▢ pricelist resolution ▢ discounts/promotions ▢
purchase.order + three-way match ▢ stock.move/quant/picking ▢ warehouses & locations ▢
mrp.bom + mrp.production ▢ double-entry ▢ account.move duality (invoice = journal
entry) ▢ journals & chart of accounts ▢ payment + reconciliation ▢ payment terms ▢
taxes (incl./excl.) + fiscal positions ▢ inventory valuation (std/FIFO/AVCO) + COGS ▢
lock dates/period close ▢ account.report engine ▢ POS session → journal entry ▢
eCommerce order → sale.order ▢

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
  invoice wizard (ch20), QWeb PDF report (ch26), portal view (ch27), maintenance-
  reminder cron (ch25), OWL jobs-per-technician dashboard (ch31).
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

---

## 10. Changelog (running log — update whenever a decision or milestone changes)

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
