import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';

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

  const stubRoute = '/docs/04-business-logic/25-cron-server-automated-actions/';
  const stub = await fetch(`${origin}${stubRoute}`);
  assert.equal(stub.status, 200, 'planned lessons should remain navigable');
  const stubBody = await stub.text();
  assert.match(stubBody, /name="robots" content="[^"]*noindex[^"]*follow/);

  const sitemap = await fetch(`${origin}/sitemap.xml`);
  assert.equal(sitemap.status, 200, '/sitemap.xml should resolve from the domain root');
  const sitemapBody = await sitemap.text();
  assert.match(sitemapBody, /\/docs\/04-business-logic\/24-data-files\/<\/loc>/);
  assert.doesNotMatch(sitemapBody, /\/docs\/04-business-logic\/25-cron-server-automated-actions/);
  assert.equal((sitemapBody.match(/<loc>/g) ?? []).length, 30, 'sitemap should list home plus 29 complete docs pages');

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

  console.log('export-preview.test.mjs: root-domain routes passed');
} finally {
  if (server.exitCode === null) {
    server.kill('SIGTERM');
    await once(server, 'exit');
  }
}
