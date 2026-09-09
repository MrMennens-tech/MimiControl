import { defineConfig, type Plugin } from 'vitest/config';
import react from '@vitejs/plugin-react';

/**
 * Strikt Content-Security-Policy voor de gebouwde app: alleen bestanden uit de
 * app zelf, plus `blob:` en `data:` voor lokaal geüploade media. Zo kan de app
 * niets naar buiten sturen en niets van buiten laden.
 */
const CSP = [
  "default-src 'self'",
  "img-src 'self' data: blob:",
  "media-src 'self' data: blob:",
  "style-src 'self' 'unsafe-inline'",
  "script-src 'self'",
  "connect-src 'self'",
  "font-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'none'",
].join('; ');

/**
 * Voegt het CSP alleen bij de productiebuild toe. In de ontwikkelmodus voegt
 * Vite een klein inline script toe voor het verversen van componenten; dat
 * zou een strikt `script-src 'self'` tegenhouden.
 */
function cspAlleenInProductie(): Plugin {
  return {
    name: 'csp-alleen-in-productie',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace(
        '<!--CSP-->',
        `<meta http-equiv="Content-Security-Policy" content="${CSP}" />`,
      );
    },
  };
}

// Relatieve base zodat de gebouwde app ook vanaf een submap of USB-stick werkt.
export default defineConfig({
  base: './',
  plugins: [react(), cspAlleenInProductie()],
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
