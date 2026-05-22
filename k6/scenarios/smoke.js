/**
 * Smoke Test — executar logo após cada deploy para garantir que todos os
 * endpoints estão respondendo corretamente em produção.
 *
 * Uso:
 *   k6 run scenarios/smoke.js
 *   k6 run --out experimental-prometheus-rw scenarios/smoke.js
 */
import { sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';
import { SMOKE_OPTIONS } from '../config.js';
import { login, authHeaders } from '../auth.js';
import { testAllEndpoints } from '../endpoints.js';

export const options = SMOKE_OPTIONS;

export function setup() {
  return { token: login() };
}

export default function ({ token }) {
  testAllEndpoints(authHeaders(token));
  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
