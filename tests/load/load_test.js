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
const AUTH_USERNAME = __ENV.AUTH_USERNAME || '';
const AUTH_PASSWORD = __ENV.AUTH_PASSWORD || '';

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

export function setup() {
  if (!AUTH_USERNAME || !AUTH_PASSWORD) return {};
  const res = http.post(`${BASE_URL}/api/auth/login/`, JSON.stringify({
    username: AUTH_USERNAME,
    password: AUTH_PASSWORD,
  }), { headers: { 'Content-Type': 'application/json' } });
  const token = res.json('access') || res.json('token');
  return { token };
}

function hit(url, name, token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = http.get(url, { headers, tags: { name } });
  const ok = check(res, {
    [`${name}: status 2xx`]: (r) => r.status >= 200 && r.status < 300,
    [`${name}: tempo < 2s`]:  (r) => r.timings.duration < 2000,
  });
  errorRate.add(!ok);
}

export default function (data) {
  const token = data ? data.token : null;
  group('health', () => {
    hit(`${BASE_URL}/api/health/`, 'health', token);
    hit(`${BASE_URL}/api/status/`, 'status', token);
  });

  group('dashboard', () => {
    hit(`${BASE_URL}/api/dashboard/kpis/`,     'dashboard/kpis',     token);
    hit(`${BASE_URL}/api/dashboard/projects/`, 'dashboard/projects', token);
    hit(`${BASE_URL}/api/dashboard/summary/`,  'dashboard/summary',  token);
  });

  group('materials', () => {
    hit(`${BASE_URL}/api/compras/`,              'compras',              token);
    hit(`${BASE_URL}/api/materials/indicators/`, 'materials/indicators', token);
  });

  group('horas-tecnicas', () => {
    hit(`${BASE_URL}/api/horas-tecnicas/`,      'horas-tecnicas',      token);
    hit(`${BASE_URL}/api/horas-tecnicas/kpis/`, 'horas-tecnicas/kpis', token);
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-ci-load-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: '  ', enableColors: true }),
  };
}
