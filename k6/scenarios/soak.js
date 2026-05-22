/**
 * Soak Test — carga moderada sustentada por 30 minutos para detectar
 * memory leaks, degradação progressiva de performance e vazamentos de conexão.
 *
 * Uso:
 *   k6 run scenarios/soak.js
 *   k6 run --out experimental-prometheus-rw scenarios/soak.js
 */
import { sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';
import { SOAK_OPTIONS } from '../config.js';
import { login, authHeaders } from '../auth.js';
import { testAllEndpoints } from '../endpoints.js';

export const options = SOAK_OPTIONS;

export function setup() {
  return { token: login() };
}

export default function ({ token }) {
  testAllEndpoints(authHeaders(token));
  sleep(2);
}

export function handleSummary(data) {
  return {
    'k6-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
