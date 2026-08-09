---
name: write-chapter
description: Write or rewrite one tutorial chapter (web/content/docs MDX) following the project's template, verification workflow, and style rules. Use whenever asked to write, draft, or finish a chapter NN of the Odoo tutorial.
---

# Write a tutorial chapter

Produce one chapter as `web/content/docs/<part>/<NN-slug>.mdx`, fully verified.
Work through the phases in order; do not skip verification.

## Phase 1 — Gather context (read, don't guess)

1. `ODOO_TUTORIAL_MASTER_PLAN.md`: the chapter's line in §5.3, the §4.3 template,
   §5.5 (LibreFleet blueprint — which models/fields THIS chapter introduces), §5.6
   (exercise grading), and the §10 changelog for recent decisions.
2. The two neighbouring chapters' MDX, to match tone and avoid re-explaining.
3. The existing stub file (keep its filename and frontmatter shape).
4. Verify every version-sensitive fact against https://www.odoo.com/documentation/19.0/
   or the running container, never from memory. Baseline is Odoo 19 Community;
   differences for 18 go in an "On Odoo 18 this differs" callout.

## Phase 2 — Execute the hands-on FIRST

Nothing goes in the chapter that was not run for real:

```bash
cd code && docker compose up -d          # env: odoo:19 + postgres:16
docker compose exec odoo odoo <cmd> -c /etc/odoo/odoo.conf ...   # CLI work
docker compose exec -T odoo odoo shell -c /etc/odoo/odoo.conf -d tutorial --no-http
docker compose exec db psql -U odoo -d tutorial -c "..."
```

- Capture real output and quote it (trim noise, never invent).
  **Paste it, never retype it, and never write it from memory after the fact.** The
  2026-08-03 audit of ch1-22 found that essentially every defect was in quoted output
  rather than in code: every checkpoint installed and upgraded cleanly and the whole
  odoolings suite was green, while transcripts were unrunnable. Six examples, all from
  prose written after a correct test: a session whose first command aborts the Postgres
  transaction so the next two cannot produce the quoted errors; absolute sequence numbers
  no reader can reproduce; a `sudo()` line aimed at the wrong recordset; two chapters
  using `exec -T`, where a bare expression prints nothing at all; a create with no commit
  followed by "quit the shell". Copy the terminal buffer into the chapter, then re-read
  the chapter's commands **in order, in a clean database**, and confirm each quoted line
  is one the run actually produced.
- **Anything a step introduces must be registered in every place it needs to be.** Model
  file in `models/__init__.py`, XML file in the manifest `data` list, new model in
  `security/ir.model.access.csv`, plus the version bump. ch21 shipped asking for a view
  and menu without the manifest entry, which is a hard `External ID not found` failure.
  Diff your chapter's instructions against the checkpoint before shipping.
- Module code for ch8+ goes in `code/addons/librefleet/`, and a snapshot in
  `code/checkpoints/chNN/` at the end. Install/upgrade with
  `-d tutorial -i/-u librefleet --stop-after-init` and prove it loads.
  **`code/addons/librefleet/` is the authoring workspace and must never be committed**
  (it is git-excluded locally; the checkpoint is the committed artifact). On a fresh
  clone, recreate it: `cp -r code/checkpoints/ch<latest>/librefleet code/addons/`.
- **Reader-facing paths are `addons/librefleet/...`, never `code/addons/...`** (plan
  §4.5): the reader works in their own repo, not a clone of ours. `code/checkpoints/`
  in the Checkpoint header and in diff commands is correct, it names our repo.
- If a fact contradicts the plan (API changed, flag renamed), fix the chapter AND
  log it in the plan's §10 changelog.

## Phase 3 — Register odoolings checks (hands-on chapters only)

In `code/odoolings.py`, add a `CHAPTERS["chNN"]` entry: one check per observable
outcome of the hands-on (model exists, field type right, record created...). Checks
call `env.call(model, method, *args)` over XML-RPC; positional args after method are
the args list (a search domain is ONE arg: `env.call("res.partner", "search",
[("name", "=", "X")])`). Each check gets a hint that teaches (name the likely
mistake). **Run the check red (before the work) and green (after), for real.**

## Phase 4 — Write the MDX

Skeleton (exact section order):

```mdx
---
title: "NN. Chapter Title"
description: One sentence, no em dashes.
---

**Goal:** one sentence. · **Time:** ~X h · **Checkpoint:** `code/checkpoints/chNN` (or "none, ...")

## Why this matters        ← motivation, real-world integrator framing
## Concepts                ← original explanation; <Mermaid> for structures/flows
## Hands-on                ← numbered steps, real commands, real output
## Verify                  ← `python3 odoolings.py check chNN` + one psql/shell/UI proof
## Gotchas                 ← 3–5, each a bold one-liner + why it bites
## Quick check             ← <Quiz> 3–5 questions
## Exercises               ← graded: ⭐ apply, ⭐⭐ transfer, ⭐⭐⭐ stretch; include one break-it lab where instructive
## Further reading         ← 2–4 links, official docs version-pinned to 19.0
```

Components (already registered in MDX scope, no imports):

- `<Quiz questions={[{q, options: [...], answer: <index>, why}]} />` — quiz ideas,
  not syntax recall; `why` explains even for a correct answer.
  **Never let the correct option be the longest one.** It is the easiest tell in the
  world and it makes the quiz measure nothing: an audit on 2026-08-03 found the key was
  the longest option in 87 of 99 questions, so a reader could score 87% without reading
  a word. At least one distractor must be as long and as specific as the key; put the
  mechanism detail in `why`, which is where it teaches, not in the option, where it
  gives the answer away. Check before shipping:
  `python3 -c` over the block, or just eyeball that the key is not the longest string.
- `<Callout type="info|warn" title="...">` — titles used: "Official docs", "Gotcha",
  "In the field" (integrator/OCA/Camptocamp practice), "On Odoo 18 this differs".
- `<Mermaid chart={\`...\`} />` for diagrams. Add `wide` only if the diagram's natural
  width genuinely exceeds the prose column (a multi-year timeline, not a 4-box
  flowchart); check in the browser first, `wide` is a no-op if it wasn't needed.
- `<Icon name="..." />` for the small glyphs on "Further reading" bullets and any
  source-type table, picking the *kind* of link (`docs`, `source`, `video`, `talk`,
  `forum`, `reddit`, `store`...). Names must exist in `web/components/icon.tsx`'s
  `ICONS` map; `npm test` fails the build on an unknown name. Don't invent a use beyond
  that pattern without checking with the author first.

Style: natural, conversational, second person. **No em dashes anywhere** (prose,
quiz strings, diagram labels); commas/colons/parentheses instead. En dashes only in
numeric ranges. Never copy sentences from docs or other tutorials.

**A Hands-on step that fills in several distinct fields on one screen gets a bulleted
field list, one bullet per field (`**Field Name:** value`), never a single sentence
listing them with commas and "and."** Caught live during the ch4 walkthrough
(2026-08-09): "Fill the rest: database name `tour`, pick your email/password for the
admin user, and (important) check Demo data. Demo data fills..." crammed five actions
and an explanation into one paragraph. Keep the *why* out of the list itself, either a
short sentence after it or folded into a nearby `<Callout>` rather than said twice. This
is about genuine multi-field forms, not any sentence with more than one clause: a short
run of 2-3 actions (click a button, name a repo, run a command) reads fine as prose,
especially right before a code block that carries the concrete steps.

## Phase 5 — Housekeeping (all of it, every chapter)

1. Glossary (`web/content/docs/glossary.mdx`): add every new jargon term,
   alphabetically, same day.
2. Roadmap (`web/content/docs/roadmap.mdx`) and plan §6 milestone checkboxes if a
   milestone's status changed; §10 changelog entry for anything decided.
3. `cd web && npm run build` must pass (catches MDX errors).
4. `grep -rn '—' web/content/docs/` must come back empty.
5. **Capture screenshots as part of writing the chapter** (author's decision,
   2026-08-05, superseding any older instinct to defer them), from the real running
   instance, via the Chrome tools. Files go in `web/public/screens/…`, referenced from
   MDX as `/screens/…` with plain markdown `![]()`; never `<http://…>` autolinks, MDX
   parses those as JSX and the build fails. Verify every UI claim against the actual
   screen, not against `ir.ui.menu`: the web client filters menus by `group_ids` and a
   raw tree walk does not, so a menu path that "exists" in the model may not be what a
   real user sees. Pin the browser viewport before capturing a chapter's screenshots so
   they match each other. The agent still cannot log in (entering a password is
   off-limits); the author signs in once and the session carries the rest of the
   chapter. The author's own manual re-execution stays the acceptance gate, a *review*
   step, not a precondition for the images.
