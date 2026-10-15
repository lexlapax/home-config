import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { devices, planChange } from './planner.mjs';

const assets = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['app.js', 'text/javascript; charset=utf-8']],
  ['/style.css', ['style.css', 'text/css; charset=utf-8']],
]);

export function createServer() {
  return http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'");
    const json = (status, value) => {
      res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(value));
    };
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && url.pathname === '/api/devices') return json(200, { mode: 'preview', liveChanges: false, devices });
      if (req.method === 'POST' && url.pathname === '/api/plans') {
        if (!req.headers['content-type']?.startsWith('application/json')) return json(415, { error: 'Send a JSON request.' });
        const origin = req.headers.origin;
        if (origin && !['http://127.0.0.1:3000', 'http://localhost:3000'].includes(origin)) return json(403, { error: 'Request origin is not allowed.' });
        let body = '';
        for await (const chunk of req) {
          body += chunk.toString();
          if (Buffer.byteLength(body) > 4096) return json(413, { error: 'Request is too large.' });
        }
        try { return json(200, planChange(JSON.parse(body))); }
        catch (error) { return json(400, { error: error instanceof SyntaxError ? 'Invalid JSON request.' : error.message }); }
      }
      if (req.method === 'GET' && assets.has(url.pathname)) {
        const [filename, type] = assets.get(url.pathname);
        const content = await readFile(new URL(`./public/${filename}`, import.meta.url));
        res.writeHead(200, { 'Content-Type': type });
        return res.end(content);
      }
      return json(404, { error: 'Not found. Live network changes are not available in this preview.' });
    } catch {
      return json(500, { error: 'The request could not be completed.' });
    }
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  createServer().listen(3000, '127.0.0.1', () => console.log('Device Networks preview: http://127.0.0.1:3000 — sample devices only'));
}
