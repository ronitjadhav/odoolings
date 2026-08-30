# Odoolings — agent guide

Interactive tutorial platform teaching Odoo 19 development, plus the companion code
readers build against. Live at https://odoolings.ronit.io/.

**Source of truth: `ODOO_TUTORIAL_MASTER_PLAN.md`.** Read it before non-trivial work:
§4 site/authoring conventions, §4.5 the reader-workspace contract, §5.3 syllabus, §5.5
LibreFleet data blueprint, §5.6 challenge design, §6 milestones and standing rules.
**Every decision or milestone change must be logged in its §10 changelog**, so work can
resume cold.

## This project spans TWO repositories

| Repo | Owns | Touched |
|---|---|---|
| `ronitjadhav/odoolings` (this checkout) | site, chapter MDX, `code/checkpoints/`, `code/odoolings.py`, the plan | every chapter |
| `ronitjadhav/odoolings-starter` | GitHub **template** readers instantiate: `docker-compose.yml`, `odoo.conf`, `addons/.gitkeep`, `.gitignore`, README | almost never |

Rules that matter when working here:

1. **Chapter work never touches the starter.** One PR in this repo per chapter, as always.
2. **`code/docker-compose.yml` and `code/odoo.conf` are the source of truth.** The starter
   holds copies. `.github/workflows/deploy-pages.yml` fails the build if they drift, so if
   you change either file you MUST mirror it to the starter in the same session, then
   re-run the workflow. Do not "fix" the drift check by relaxing it.
   **This is also why Dependabot does not watch the `docker` ecosystem**: an automated
   `odoo:19` or `postgres:16` bump would break CI on its own PR (the starter would still
   hold the old tag) and would bypass rule 3. `.github/dependabot.yml` says so at length;
   do not add a `docker` entry to it.
3. **The starter's default branch must match D1's baseline Odoo version** (19.0 today).
   When the baseline bumps, branch the old version in the starter first (branch-per-version,
   exactly what ch7 teaches), then move its `main`.
4. **Readers never clone this repo.** Never write a chapter step that tells them to. They
   use the starter, `curl` the checker (ch5), and fetch single checkpoints by tarball (ch8).
   See §4.5 for the full contract.
5. To work on the starter, clone it separately:
   `git clone https://github.com/ronitjadhav/odoolings-starter.git`. It is not a
   submodule and is not vendored here on purpose, so remember it exists.

## Layout

- `web/` — Next.js 16 + Fumadocs + Tailwind 4, static export, served from the root of
  the custom domain `odoolings.ronit.io` (`public/CNAME`), no basePath.
  Chapters are MDX in `web/content/docs/<part>/<NN-slug>.mdx`; nav order in each
  folder's `meta.json`. Custom components in `web/components/` (Quiz, Mermaid,
  progress pill, mark-complete).
- `code/` — reader-facing: `docker-compose.yml` (odoo:19 + postgres:16), `odoo.conf`,
  `odoolings.py` (stdlib-only XML-RPC work checker), `checkpoints/` (per-chapter
  snapshots, the reference readers diff against).
  **`code/addons/` ships empty on purpose.** Readers build LibreFleet in a workspace
  repo of their own (ch5), never in a clone of this one. `code/addons/librefleet/` is
  the authoring workspace: it is git-excluded locally via `.git/info/exclude`, so on a
  fresh clone recreate it with `cp -r code/checkpoints/ch<latest>/librefleet
  code/addons/`. Never `git add` it; the committed artifact is the checkpoint.

## Commands

```bash
cd web && npm run dev        # local site
cd web && npm test           # progress logic + quiz quality gates
cd web && npm run test:ci   # what CI runs, IN ORDER: test, build, test:export.
                            # Use this before any push. `npm test` alone skips
                            # test:export, which needs out/ and so only fails in
                            # CI (that gap let the D13 renumber break main).
cd web && npm run build     # build alone: validates all MDX
cd code && docker compose up -d          # the tutorial's Odoo environment
python3 code/odoolings.py check chNN     # verify a chapter's hands-on state
python3 code/odoolings.py check chNN --db functional     # Parts 4-5 chapters
```

**Three local databases, one per reader path.** Verify and screenshot each chapter
against the one *that chapter's reader* actually has, or the screens will show apps
they have not installed:

| db | Holds | Used by |
|---|---|---|
| `tour` | `crm` + `sale_management` + demo | ch4 only (its whole point is the menu changing as you install two apps) |
| `tutorial` | LibreFleet, no business apps | the dev track: ch5-20, ch31-34 |
| `functional` | sale/purchase/stock/mrp/crm/loyalty + demo | Parts 4-5: ch21-30 |

## Non-negotiable authoring rules

1. **Never ship unexecuted code.** Every command and snippet in a chapter is run for
   real in the Docker env first; quoted output is real output.
2. **Style: natural, conversational prose. No em dashes (—).** Use commas, colons,
   parentheses, or a new sentence. En dashes in numeric ranges (`1–7`) are fine.
3. **Original prose only.** Never copy from Odoo docs/source/blogs. Link out
   generously, always version-pinned to `/documentation/19.0/`.
   **Chapters must stand alone**: cover each topic deeply enough that the reader
   does not need the official docs to follow along. Links are supplementary
   ("go deeper"), never required reading for the chapter's own material.
4. Chapters follow the §4.3 template exactly (incl. Quick check quiz and ⭐-graded
   exercises); hands-on chapters register odoolings checks; new jargon gets a
   glossary entry the same day.
5. **Capture screenshots as part of writing the chapter**, from the real running
   instance, via the Chrome tools (author's decision, 2026-08-05). Never invent or
   describe one you did not take. The author's own manual re-execution is still the
   acceptance gate, but it is a *review* step, not a precondition for the images.
   The agent cannot log in (entering a password is off-limits), so the author signs
   in to `localhost:8069` once; the Chrome profile keeps the session for later runs.
   See the plan's §6 rule 4b for the mechanics that must be got right (viewport,
   `images: { unoptimized: true }`, checking claims against `group_ids`).
6. To write a new chapter, use the `write-chapter` skill in `.claude/skills/`.

Content license CC BY-SA 4.0, code AGPL-3. Commit style: `M<N>: ...` for milestone
work on this repo; tutorial code examples teach OCA style (`[TAG] module: ...`).
