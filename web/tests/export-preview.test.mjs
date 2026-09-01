import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

/**
 * Every docs page that is NOT a stub is expected in the sitemap, so derive the
 * count instead of hard-coding it. A literal number here goes stale the moment a
 * stub becomes a written chapter, which is exactly how the chapter renumber
 * (D13) slipped past this test.
 */
function completeDocsPageCount(dir = 'content/docs') {
  let total = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      total += completeDocsPageCount(full);
    } else if (entry.name.endsWith('.mdx')) {
      if (!readFileSync(full, 'utf8').includes('title="Stub"')) total += 1;
    }
  }
  return total;
}

/**
 * Finds one stub page's route, if any stub still exists. All 50 planned
 * chapters shipped as of ch50 (2026-08-12), so this currently returns null;
 * written that way rather than deleted so the noindex/sitemap-exclusion
 * checks below re-engage automatically the moment a new chapter is planned
 * and stubbed, instead of needing to be hand-restored.
 */
function findStubRoute(dir = 'content/docs', base = '/docs') {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const found = findStubRoute(full, `${base}/${entry.name}`);
      if (found) return found;
    } else if (entry.name.endsWith('.mdx')) {
      if (readFileSync(full, 'utf8').includes('title="Stub"')) {
        return `${base}/${entry.name.replace(/\.mdx$/, '')}/`;
      }
    }
  }
  return null;
}

/** Every exported docs route, read off the sitemap the build just produced. */
function docsRoutes(sitemapBody) {
  return [...sitemapBody.matchAll(/<loc>https:\/\/odoolings\.ronit\.io([^<]*)<\/loc>/g)]
    .map((m) => m[1] || '/');
}

const port = 49173;
const origin = `http://127.0.0.1:${port}`;
const server = spawn(process.execPath, ['scripts/serve-export.mjs'], {
  env: { ...process.env, PORT: String(port) },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let stderr = '';
server.stderr.setEncoding('utf8');
server.stderr.on('data', (chunk) => {
  stderr += chunk;
});

async function waitForServer() {
  for (let attempt = 0; attempt < 30; attempt++) {
    try {
      const response = await fetch(`${origin}/`, { redirect: 'manual' });
      return response;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }
  throw new Error(`export preview did not start${stderr ? `: ${stderr}` : ''}`);
}

try {
  const home = await waitForServer();
  assert.equal(home.status, 200, 'the custom-domain root must render without redirecting');
  const homeBody = await home.text();
  assert.match(homeBody, /<title>Odoolings: Free Odoo 19 Development Tutorial<\/title>/);
  assert.match(homeBody, /Learn Odoo 19 development for free by building a real module/);
  assert.match(homeBody, /type="application\/ld\+json"/);
  assert.match(homeBody, /"@type":"Course"/);
  assert.match(homeBody, /Free Odoo 19 development tutorial/);

  const lessonRoute = '/docs/00-orientation/01-what-odoo-is/';
  const lesson = await fetch(`${origin}${lessonRoute}`);
  assert.equal(lesson.status, 200, `${lessonRoute} should resolve from the domain root`);
  const lessonBody = await lesson.text();
  assert.match(lessonBody, /rel="canonical" href="https:\/\/odoolings\.ronit\.io\/docs\/00-orientation\/01-what-odoo-is\/"/);
  assert.match(lessonBody, /"@type":"LearningResource"/);

  // All 50 planned chapters are written as of ch50; findStubRoute() returns
  // null until a future chapter is planned and stubbed again, at which point
  // this block re-engages on its own.
  const stubRoute = findStubRoute();
  if (stubRoute) {
    const stub = await fetch(`${origin}${stubRoute}`);
    assert.equal(stub.status, 200, 'planned lessons should remain navigable');
    const stubBody = await stub.text();
    assert.match(stubBody, /name="robots" content="[^"]*noindex[^"]*follow/);
  }

  const sitemap = await fetch(`${origin}/sitemap.xml`);
  assert.equal(sitemap.status, 200, '/sitemap.xml should resolve from the domain root');
  const sitemapBody = await sitemap.text();
  // The last chapter, whatever it is numbered today. Hard-coding the number here is
  // what made the D13 renumber fail in CI rather than locally, so match the slug and
  // let the number float.
  assert.match(sitemapBody, /\/docs\/09-integrator-craft\/\d+-career-map\/<\/loc>/);
  if (stubRoute) {
    assert.doesNotMatch(sitemapBody, new RegExp(stubRoute.replace(/\/$/, '')));
  }
  const expectedLocs = 1 + completeDocsPageCount();
  assert.equal(
    (sitemapBody.match(/<loc>/g) ?? []).length,
    expectedLocs,
    `sitemap should list home plus every complete docs page (${expectedLocs - 1} of them)`,
  );

  for (const route of [
    '/docs/00-orientation/01-what-odoo-is/',
    '/manifest.webmanifest',
    '/robots.txt',
    '/sitemap.xml',
    '/api/search',
  ]) {
    const response = await fetch(`${origin}${route}`);
    assert.equal(response.status, 200, `${route} should resolve from the domain root`);
  }

  /**
   * Every image on every page must be a plain file, and must actually be there.
   *
   * Fumadocs maps markdown `![]()` to next/image, so without
   * `images: { unoptimized: true }` the export still BUILDS but points every image
   * at `/_next/image/?url=...`, an optimizer that does not exist on static hosting.
   * The result is 404s in production and correct images in `npm run dev`, which is
   * the worst way for this to fail. Verified before the guard existed: that URL
   * returned 404 while the build reported success.
   */
  for (const route of docsRoutes(sitemapBody)) {
    const body = await (await fetch(`${origin}${route}`)).text();
    assert.doesNotMatch(
      body,
      /\/_next\/image/,
      `${route} references the image optimizer, which 404s on static hosting. ` +
        'Set images: { unoptimized: true } in next.config.mjs.',
    );
    for (const src of body.matchAll(/<img[^>]+src="(\/[^"]+)"/g)) {
      const asset = await fetch(`${origin}${src[1]}`);
      assert.equal(asset.status, 200, `${route} references a missing image: ${src[1]}`);
    }
  }

  console.log('export-preview.test.mjs: root-domain routes passed');
} finally {
  if (server.exitCode === null) {
    server.kill('SIGTERM');
    await once(server, 'exit');
  }
}
