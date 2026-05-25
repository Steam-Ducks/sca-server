/**
 * Load Test — simula a carga típica de usuários simultâneos em produção.
 * Rampa de 0→10 VUs em 2 min, sustentado por 10 min, rampa de saída em 2 min.
 *
 * Thresholds: p95 < 2s, taxa de erro < 1%
 *
 * Uso:
 *   k6 run scenarios/load.js
 *   k6 run --out experimental-prometheus-rw scenarios/load.js
 */
import { sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';
import { LOAD_OPTIONS } from '../config.js';
import { login, authHeaders } from '../auth.js';
import { testAllEndpoints } from '../endpoints.js';

export const options = LOAD_OPTIONS;

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
