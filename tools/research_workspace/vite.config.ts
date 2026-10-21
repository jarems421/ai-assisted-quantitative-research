import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '127.0.0.1',
    fs: { strict: true, allow: [process.cwd()], deny: ['**/.git/**', '**/.env*', '**/data/**'] },
    headers: { 'Content-Security-Policy': "default-src 'self'; connect-src 'self' ws://127.0.0.1:*; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'" },
  },
  preview: { host: '127.0.0.1' },
});
