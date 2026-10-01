// Offline API responses plus Angular dev server for collaborative/manual inspection.
// This server never contacts the backend or an answer provider.
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { responses } from './fixtures.ts';

const api = createServer((request, response) => {
  response.setHeader('Content-Type', 'application/json');
  if (request.url === '/api/health' && request.method === 'GET') {
    response.end(JSON.stringify({ status: 'ok', mode: 'openai' }));
    return;
  }
  if (request.url !== '/api/ask' || request.method !== 'POST') {
    response.writeHead(404).end(JSON.stringify({ detail: 'Mock endpoint not found' }));
    return;
  }
  let body = '';
  request.on('data', (chunk) => {
    body += chunk;
  });
  request.on('end', () => {
    let question;
    try {
      question = JSON.parse(body).question;
    } catch {
      response.writeHead(400).end(JSON.stringify({ detail: 'Invalid JSON' }));
      return;
    }
    if (
      typeof question !== 'string' ||
      question.trim().length < 3 ||
      question.trim().length > 2000
    ) {
      response.writeHead(422).end(JSON.stringify({ detail: 'Use 3–2,000 characters.' }));
      return;
    }
    const query = question.toLowerCase();
    setTimeout(
      () => {
        if (query.includes('error')) {
          response
            .writeHead(504)
            .end(JSON.stringify({ detail: 'OpenAI timed out. Please try again.' }));
          return;
        }
        const result = query.includes('no matches')
          ? responses.noMatches
          : query.includes('insufficient')
            ? responses.insufficient
            : query.includes('preview')
              ? responses.preview
              : responses.answered;
        response.end(JSON.stringify(result));
      },
      query.includes('slow') ? 8000 : 500,
    );
  });
});

api.listen(4301, '127.0.0.1', () => {
  console.log(
    'OFFLINE MOCK API on 4301. Questions: preview, no matches, insufficient, error, slow; otherwise answered.',
  );
});
const angular = spawn(
  process.execPath,
  [
    'node_modules/@angular/cli/bin/ng.js',
    'serve',
    '--host',
    '127.0.0.1',
    '--port',
    '4300',
    '--proxy-config',
    'testing/proxy.mock.json',
  ],
  { stdio: 'inherit' },
);
function stop() {
  angular.kill();
  api.close();
}
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
angular.on('exit', (code) => {
  api.close();
  process.exitCode = code ?? 1;
});
api.on('error', (error) => {
  console.error(error);
  angular.kill();
  process.exitCode = 1;
});
