/**
 * Stress Test — aumenta a carga progressivamente para encontrar o ponto de
 * ruptura da API. Foca nos endpoints mais pesados (dashboard e materials).
 *
 * Fases: 20→50→100 VUs com patamares de 5 min cada.
 *
 * Uso:
 *   k6 run scenarios/stress.js
 *   k6 run --out experimental-prometheus-rw scenarios/stress.js
 */
import { sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';
import { STRESS_OPTIONS } from '../config.js';
import { login, authHeaders } from '../auth.js';
import { testHealth, testDashboard, testMaterials, testTechnicalHours } from '../endpoints.js';

export const options = STRESS_OPTIONS;

export function setup() {
  return { token: login() };
}

export default function ({ token }) {
  const headers = authHeaders(token);
  testHealth(headers);
  testDashboard(headers);
  testMaterials(headers);
  testTechnicalHours(headers);
  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
