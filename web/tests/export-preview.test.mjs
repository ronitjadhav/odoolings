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
  assert.match(await home.text(), /<title>Odoolings<\/title>/);

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
