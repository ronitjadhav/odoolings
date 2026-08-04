import { execFileSync } from 'node:child_process';
import { rmSync } from 'node:fs';
import { resolve } from 'node:path';

const buildDir = resolve('tests/.build');

try {
  execFileSync(
    process.execPath,
    [
      resolve('node_modules/typescript/bin/tsc'),
      'lib/progress.ts',
      '--ignoreConfig',
      '--outDir',
      'tests/.build',
      '--module',
      'commonjs',
      '--target',
      'es2020',
      '--skipLibCheck',
    ],
    { stdio: 'inherit' },
  );
  execFileSync(process.execPath, ['tests/progress.test.mjs'], {
    stdio: 'inherit',
    env: { ...process.env, TZ: 'Europe/Berlin' },
  });
} finally {
  rmSync(buildDir, { recursive: true, force: true });
}
