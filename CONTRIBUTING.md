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
