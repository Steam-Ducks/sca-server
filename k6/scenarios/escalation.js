/**
 * Escalation Test — três patamares de carga para identificar o comportamento
 * da API em cada nível e encontrar o ponto de degradação/ruptura.
 *
 * Patamar 1 →  100 VUs  (carga normal)
 * Patamar 2 → 1 000 VUs  (carga alta)
 * Patamar 3 → 20 000 VUs (carga extrema / ponto de ruptura)
 *
 * Uso:
 *   k6 run scenarios/escalation.js
 *   k6 run --out experimental-prometheus-rw scenarios/escalation.js
 *
 * Atenção: 20k VUs exige uma máquina com bastante RAM/CPU ou k6 distribuído.
 */
import { sleep } from 'k6';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';
import { ESCALATION_OPTIONS } from '../config.js';
import { login, authHeaders } from '../auth.js';
import { testHealth, testDashboard, testMaterials } from '../endpoints.js';

export const options = ESCALATION_OPTIONS;

export function setup() {
  return { token: login() };
}

export default function ({ token }) {
  const headers = authHeaders(token);
  testHealth(headers);
  testDashboard(headers);
  testMaterials(headers);
  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
