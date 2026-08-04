import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, resolve, sep } from 'node:path';
// Keep in sync with next.config.mjs and lib/shared.ts.
const basePath = process.env.BASE_PATH ?? '';

const root = resolve('out');
const port = Number(process.env.PORT ?? 3000);
const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.woff2': 'font/woff2',
  '.xml': 'application/xml; charset=utf-8',
};

createServer(async (request, response) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url ?? '/', 'http://localhost').pathname);
  } catch {
    response.writeHead(400).end('Bad request');
    return;
  }

  if (basePath && pathname === '/') {
    response.writeHead(307, { Location: `${basePath}/` }).end();
    return;
  }
  if (basePath && pathname === basePath) {
    response.writeHead(308, { Location: `${basePath}/` }).end();
    return;
  }
  if (basePath && !pathname.startsWith(`${basePath}/`)) {
    response.writeHead(404).end('Not found');
    return;
  }

  const requestPath = basePath ? pathname.slice(basePath.length) : pathname;
  const candidate = resolve(root, `.${requestPath}`);
  if (candidate !== root && !candidate.startsWith(`${root}${sep}`)) {
    response.writeHead(403).end('Forbidden');
    return;
  }

  try {
    const info = await stat(candidate);
    const file = info.isDirectory() ? join(candidate, 'index.html') : candidate;
    const fileInfo = info.isDirectory() ? await stat(file) : info;
    response.writeHead(200, {
      'Content-Length': fileInfo.size,
      'Content-Type': contentTypes[extname(file)] ?? 'application/octet-stream',
    });
    createReadStream(file).pipe(response);
  } catch {
    response.writeHead(404).end('Not found');
  }
}).listen(port, '127.0.0.1', () => {
  console.log(`Odoolings export: http://127.0.0.1:${port}${basePath}/`);
});
