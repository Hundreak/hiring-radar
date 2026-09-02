import {defineConfig, globalIgnores} from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
    'src/auth/**',
    'src/ai/**',
    'src/jobs/**',
    'src/landing/**',
    'src/layout/**',
    'src/matches/**',
    'src/profile/**',
    'src/saved/**',
    'src/theme/**',
    'src/ui/**',
  ]),
]);