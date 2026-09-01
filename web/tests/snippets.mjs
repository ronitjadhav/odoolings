// node tests/snippets.mjs
//
// Three ways a code snippet can be wrong in a way no reader can see coming, all
// three found in ch32/ch33 by a reader working through the book rather than by
// review. They share a shape: the module upgrades cleanly and the work is
// simply absent, so there is no error to search for.
//
// 1. An XML snippet presented as a whole file, with a bare <record> root and no
//    <?xml?>/<odoo> wrapper. Copy it and Odoo cannot load it.
// 2. A data file the chapter tells you to create but never tells you to add to
//    the manifest's "data" list. It never loads, and nothing says so.
// 3. A field defined with a trailing comma, which makes it a one-element tuple
//    rather than a Field. Odoo builds models from class attributes that are
//    Field instances, skips anything else without comment, and reports success.
// 4. The first file written into a subdirectory the module does not have yet,
//    with no `mkdir` anywhere before it. A reader in an editor never notices; one
//    working from the shell gets `no such file or directory` and no way to know
//    the chapter, not their typing, was at fault.
//
// Fragments (an insertion into a file whose wrapper is shown elsewhere in the
// same chapter) are legitimate and are listed in FRAGMENT_ALLOWLIST below. Add
// to it only when the surrounding prose makes clear the reader is editing an
// existing file, never to silence a real finding.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = 'content/docs';

function walk(dir) {
  return readdirSync(dir).flatMap((e) => {
    const p = join(dir, e);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith('.mdx') ? [p] : [];
  });
}

const files = walk(ROOT);
const docs = files.map((f) => ({ file: f, text: readFileSync(f, 'utf8') }));

// `${chapter basename}::${snippet path}` for snippets that are deliberately partial.
const FRAGMENT_ALLOWLIST = new Set([
  '31-the-three-inheritance-types.mdx::views/librefleet_menus.xml',
  '34-data-files.mdx::data/service_type_master.xml',
  '35-cron-server-automated-actions.mdx::data/maintenance_reminder_cron.xml',
  '36-qweb-pdf-reports.mdx::report/service_order_report.xml',
  '37-controllers-portal.mdx::security/librefleet_security.xml',
  '40-extending-the-web-client.mdx::views/service_order_views.xml',
]);

const bareRoots = [];
const unregistered = [];
const tupleFields = [];

// 1. XML snippets that claim to be a file but do not open like one.
for (const { file, text } of docs) {
  const base = file.split('/').pop();
  const re = /```xml title="addons\/librefleet\/([^"]+)"\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text))) {
    const [, path, body] = m;
    if (FRAGMENT_ALLOWLIST.has(`${base}::${path}`)) continue;
    const first = (body.split('\n').find((l) => l.trim()) || '').trimStart();
    if (!first.startsWith('<?xml') && !first.startsWith('<odoo')) {
      bareRoots.push({ file, path, line: text.slice(0, m.index).split('\n').length });
    }
  }
}

// 2. Data files created by a chapter but never named in a manifest "data" list.
const created = new Map();
for (const { file, text } of docs) {
  const re =
    /```(?:xml|text|csv)[^\n]*title="addons\/librefleet\/((?:views|data|report|security|wizards)\/[^"]+)"/g;
  let m;
  while ((m = re.exec(text))) if (!created.has(m[1])) created.set(m[1], file);
}
const allText = docs.map((d) => d.text).join('\n');
for (const [path, file] of created) {
  // Named inside any python snippet that looks like a manifest data list, or on
  // its own quoted line, which is how chapters show a partial data list.
  const quoted = new RegExp(`^\\s*"${path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}",\\s*$`, 'm');
  if (!quoted.test(allText)) unregistered.push({ file, path });
}

// 3. `name = fields.X(...),` which silently defines a tuple, not a field.
for (const { file, text } of docs) {
  const re = /```python[^\n]*\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text))) {
    const body = m[1];
    const lines = body.split('\n');
    lines.forEach((line, i) => {
      // A field assignment whose statement ends in "),". Multi-line calls end on
      // a later line, so walk forward to the line that closes the call.
      if (!/^\s*\w+\s*=\s*fields\.\w+\(/.test(line)) return;
      let depth = 0;
      for (let j = i; j < lines.length; j++) {
        for (const ch of lines[j]) {
          if (ch === '(') depth++;
          else if (ch === ')') depth--;
        }
        if (depth === 0) {
          if (/\),\s*$/.test(lines[j])) {
            tupleFields.push({
              file,
              line: text.slice(0, m.index).split('\n').length + i + 1,
              text: line.trim(),
            });
          }
          return;
        }
      }
    });
  }
}

// 4. First write into a directory no earlier chapter has created.
const CHAPTER_NUM = (p) => Number((p.split('/').pop().match(/^(\d+)/) || [0, 1e9])[1]);
const ordered = [...docs].sort((a, b) => CHAPTER_NUM(a.file) - CHAPTER_NUM(b.file));
const madeDirs = new Set(['.']);
const unmadeDirs = [];
for (const { file, text } of ordered) {
  // Every mkdir in this chapter counts, wherever it sits relative to the write.
  for (const m of text.matchAll(/mkdir[^\n]*?addons\/librefleet\/(\S+)/g)) {
    // `mkdir -p a/{b,c}` is one command making several directories.
    const raw = m[1].replace(/[`'"]/g, '');
    const brace = raw.match(/^(.*?)\{(.+)\}$/);
    const paths = brace ? brace[2].split(',').map((s) => brace[1] + s) : [raw];
    for (const p of paths) {
      const parts = p.split('/');
      for (let i = 1; i <= parts.length; i++) madeDirs.add(parts.slice(0, i).join('/'));
    }
  }
  // Files named by a title= attribute or by prose immediately introducing them.
  const written = [
    ...text.matchAll(/title="addons\/librefleet\/([^"]+)"/g),
    ...text.matchAll(/`(?:addons\/librefleet\/)?((?:models|views|data|demo|report|security|controllers|wizards|tests|i18n|static)\/[^`]+\.\w+)`/g),
  ];
  for (const m of written) {
    const dir = m[1].split('/').slice(0, -1).join('/');
    if (!dir || madeDirs.has(dir)) continue;
    madeDirs.add(dir);
    unmadeDirs.push({ file, dir });
  }
}

let failed = false;

if (unmadeDirs.length) {
  failed = true;
  console.error(`\n${unmadeDirs.length} director(ies) written into before anything creates them:\n`);
  for (const b of unmadeDirs) console.error(`  ${b.file}  first writes ${b.dir}/ with no mkdir`);
  console.error('\n  Add a `$ mkdir -p addons/librefleet/<dir>` console block before the');
  console.error('  first file, the way chapters 9 and 39 do.');
}

if (bareRoots.length) {
  failed = true;
  console.error(
    `\n${bareRoots.length} XML snippet(s) shown as a whole file but missing the <?xml>/<odoo> root:\n`,
  );
  for (const b of bareRoots) console.error(`  ${b.file}:${b.line}  ${b.path}`);
  console.error('\n  If it is meant as a fragment, say so in the prose and add it to');
  console.error('  FRAGMENT_ALLOWLIST in this file.');
}

if (unregistered.length) {
  failed = true;
  console.error(`\n${unregistered.length} data file(s) created but never added to a manifest:\n`);
  for (const b of unregistered) console.error(`  ${b.path}  (created in ${b.file})`);
}

if (tupleFields.length) {
  failed = true;
  console.error(`\n${tupleFields.length} field(s) defined with a trailing comma (a tuple, not a Field):\n`);
  for (const b of tupleFields) console.error(`  ${b.file}:${b.line}  ${b.text}`);
}

if (failed) process.exit(1);
console.log(
  `snippets: ${created.size} data files all registered, every XML file snippet has a root, ` +
    `no tuple fields, every directory created before first use.`,
);
