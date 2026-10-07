# Contributing

This is a learning project written in public. Corrections are the most valuable thing
you can send.

**Found something wrong?** Open an issue, or click the ✏️ edit icon on any page to send
a PR directly. Odoo moves fast and chapters go stale, so factual fixes are always welcome.

**Adding content?** Follow the chapter template used by every page: *Why this matters ·
Concepts · Hands-on · Verify · Gotchas · Quick check · Exercises · Further reading*.

Chapters are MDX files in `web/content/docs/`. Quizzes use the `<Quiz>` component
(see chapter 1 for the shape). Chapters with hands-on work should also register
checks in `code/odoolings.py` so readers can verify their module automatically.

Two rules:

1. **Original prose only.** Never paste text from the Odoo docs, books, or blog posts.
   Link to them instead.
2. **Never ship unexecuted code.** Every snippet must run in the `code/docker-compose.yml`
   environment first, and pasted output must be real.

Contributions to prose are licensed CC BY-SA 4.0; contributions to `code/` are AGPL-3.0.

## Working on the repo

### Commands

```bash
cd web && npm run dev        # local site
cd web && npm test           # progress logic + quiz quality gates
cd web && npm run test:ci    # what CI runs, in order: test, build, test:export
cd web && npm run build      # build alone: validates all MDX
cd code && docker compose up -d                       # the tutorial's Odoo
python3 code/odoolings.py check chNN                  # a chapter's hands-on state
python3 code/odoolings.py check chNN --db functional  # Parts 4-5 chapters
```

Run `npm run test:ci` before pushing. `npm test` alone skips `test:export`, which
needs `out/` and so only fails in CI.

### Three local databases, one per reader path

Verify and screenshot each chapter against the database *that chapter's reader*
has, or the screens will show apps they have not installed.

| db | Holds | Used by |
|---|---|---|
| `tour` | `crm` + `sale_management` + demo | ch4 only (its point is the menu changing as two apps install) |
| `tutorial` | LibreFleet, no business apps | the dev track: ch5-20, ch31-34 |
| `functional` | sale/purchase/stock/mrp/crm/loyalty + demo | Parts 4-5: ch21-30 |

### The authoring workspace

`code/addons/` ships empty on purpose. Locally, `code/addons/librefleet/` is the
authoring workspace. On a fresh clone, add `code/addons/librefleet/` to
`.git/info/exclude` and recreate it with
`cp -r code/checkpoints/ch<latest>/librefleet code/addons/`. Never commit it: the
checkpoint in `code/checkpoints/chNN/` is the committed artifact.

### The reader's workspace and the starter

Readers build LibreFleet in a repository of their own, created from
[odoolings-starter](https://github.com/ronitjadhav/odoolings-starter), a GitHub
template (not a fork, so they have no upstream to send pull requests to). The starter
is a separate repository, not a submodule and not vendored here. Every chapter
respects these rules:

- **Never tell the reader to clone this repository**, not as a workspace and not as a
  reference. They `curl` `odoolings.py` (chapter 5) and fetch a single checkpoint by
  tarball (chapter 8):

  ```bash
  curl -sL https://github.com/ronitjadhav/odoolings/archive/main.tar.gz \
    | tar -xz -C .checkpoints --strip-components=3 'odoolings-main/code/checkpoints/chNN'
  ```
- Reader-facing paths are `addons/librefleet/...`, never `code/addons/...`.
  `code/checkpoints/chNN` is still right in a chapter's Checkpoint line and in diff
  commands, since it names a path in this repository.
- `odoolings.py` stays location-independent: pure XML-RPC against `--url`, never
  reading the reader's files.
- Setup needs no shell: "Use this template", `git clone` and `docker compose up`.
- `code/docker-compose.yml` and `code/odoo.conf` here are the source of truth. If you
  change either, mirror it to the starter in the same session, then re-run the
  workflow. Never relax the drift check. This is also why Dependabot does not watch
  the `docker` ecosystem (`.github/dependabot.yml` explains).
- The starter keeps `addons/.gitkeep`: bind-mount a missing directory and Docker
  creates it owned by root, so chapter 8's `mkdir` fails for every Linux reader.
- The starter's default branch matches the baseline Odoo version (19.0 today). When
  the baseline bumps, branch the old version in the starter first (branch-per-version,
  exactly what chapter 7 teaches), then move its `main`.
- Chapter work never touches the starter: one pull request here per chapter.

### Writing a chapter

Every chapter follows one skeleton:

```markdown
---
title: "NN. Chapter Title"
description: One sentence.
---

**Goal:** one sentence. · **Time:** ~X h · **Checkpoint:** `code/checkpoints/chNN`

## Why this matters     <- motivation, real-world framing
## Concepts             <- original explanation, diagrams
## Hands-on             <- steps on LibreFleet, real commands, real output
## Verify               <- `python3 odoolings.py check chNN` plus one UI/psql/shell proof
## Gotchas              <- pitfalls met while writing and testing the chapter
## Quick check          <- <Quiz> with 3-5 questions, each with a `why`
## Exercises            <- graded ⭐/⭐⭐/⭐⭐⭐, no inline solutions
## Further reading      <- official docs, OCA examples
```

- **UI first, shell optional.** Wherever a reader can do a step by clicking (creating
  records, settings, **Apps → ⋮ → Upgrade**, reading results through developer mode
  and **Settings → Technical**), the UI is the main path and the command goes in a
  second tab:

  ```mdx
  <UiOrShell>
  <Tab>
  ...the clicks, with a screenshot per step...
  </Tab>
  <Tab>
  ...the same step in the shell...
  </Tab>
  </UiOrShell>
  ```

  The reader's choice of tab is remembered across chapters. The shell stays the only
  path where it is the lesson: the ORM in `odoo shell`, tests, git, reading core source.
- **Hands-on chapters register `odoolings` checks** for their end state, and Verify
  runs them. New jargon gets a glossary entry (`web/content/docs/glossary.mdx`) the
  same day.
- **Quizzes test ideas** (predict the behavior, pick the approach), not syntax a reader
  can look up.
- **Exercises:** ⭐ Apply (same pattern, new target), ⭐⭐ Transfer (combine with earlier
  chapters, no steps given), ⭐⭐⭐ Stretch (needs reading beyond the chapter; optional).
  Add a break-it lab where it teaches something: cause the failure the chapter guards
  against, read the real traceback, then fix it.
- **Functional chapters (Parts 4-5)** keep the same skeleton. Hands-on has two
  movements, in order: "Run the flow" in the UI, then "Read what it did" (`psql`,
  `odoo shell`, the records created, the core method that ran). Verify runs against
  the `functional` database. Exercises are ticket-shaped: "the client says this
  discount is wrong, find why" beats "explore the pricelist screen".
- **Components:** `<Steps>`/`<Step>` for Hands-on, with `###` headings that carry no
  number of their own. `<Files className="bg-(--tone-sky)">` showing the whole module
  tree after any step that adds a file. `<Mermaid label="...">`, where `label` is
  required (it is the `aria-label`) and line breaks are `<br/>`. Callouts:
  `type="info" title="Official docs"`, `type="warn" title="Gotcha"`,
  `type="info" title="In the field"`, `type="info" title="On Odoo 18 this differs"`.
- **Style:** natural, conversational prose, and **no em dashes**: use commas, colons,
  parentheses or a new sentence. En dashes in numeric ranges (`1–7`) are fine. Name
  chapters in cross-references ("chapter 31"), not parts: part numbers move.
- **Chapters stand alone:** deep enough that the reader never needs the official docs
  to follow along. Links out are for going deeper, always pinned to
  `/documentation/19.0/`.
- **Screenshots** come from the real running instance, captured while the chapter is
  written, with the browser viewport pinned so a chapter's images match. Every UI step
  gets one, with what the reader must click or read outlined in red, taken against a
  database in the state that chapter's reader has (and named like theirs: developer
  mode prints the database name in the top bar). Files go in
  `web/public/screens/`, referenced as `/screens/...` with plain markdown `![]()`
  (MDX has no `<http://...>` autolinks; it parses them as JSX). Check every UI claim
  against the screen, not against `ir.ui.menu`: the web client filters menus by
  `group_ids`. Keep `images: { unoptimized: true }` in `web/next.config.mjs`, or every
  image 404s in production while the build stays green.

Commit messages: `M<N>: ...` for milestone work on this repository. The tutorial's own
code examples teach OCA style (`[TAG] module: ...`).
