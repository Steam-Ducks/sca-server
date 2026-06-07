/**
 * Load test de CI — 5 VUs por ~2 min contra app local com settings_test.
 * Sem auth: AllowAny está ativo via DJANGO_SETTINGS_MODULE=config.settings_test.
 *
 * Thresholds: p95 < 2000 ms, taxa de erro < 1%
 *
 * Uso local:
 *   k6 run tests/load/load_test.js
 *   k6 run tests/load/load_test.js --env BASE_URL=http://meu-servidor:8000
 */
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

const errorRate = new Rate('errors');
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m',  target: 5 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    errors:            ['rate<0.01'],
    http_req_failed:   ['rate<0.01'],
  },
};

function hit(url, name) {
  const res = http.get(url, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name },
  });
  const ok = check(res, {
    [`${name}: status 2xx`]: (r) => r.status >= 200 && r.status < 300,
    [`${name}: tempo < 2s`]:  (r) => r.timings.duration < 2000,
  });
  errorRate.add(!ok);
}

export default function () {
  group('health', () => {
    hit(`${BASE_URL}/api/health/`, 'health');
    hit(`${BASE_URL}/api/status/`, 'status');
  });

  group('dashboard', () => {
    hit(`${BASE_URL}/api/dashboard/kpis/`,     'dashboard/kpis');
    hit(`${BASE_URL}/api/dashboard/projects/`, 'dashboard/projects');
    hit(`${BASE_URL}/api/dashboard/summary/`,  'dashboard/summary');
  });

  group('materials', () => {
    hit(`${BASE_URL}/api/compras/`,              'compras');
    hit(`${BASE_URL}/api/materials/indicators/`, 'materials/indicators');
  });

  group('horas-tecnicas', () => {
    hit(`${BASE_URL}/api/horas-tecnicas/`,      'horas-tecnicas');
    hit(`${BASE_URL}/api/horas-tecnicas/kpis/`, 'horas-tecnicas/kpis');
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-ci-load-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
