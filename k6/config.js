export const BASE_URL = __ENV.K6_BASE_URL || 'http://localhost:8000';

export const SMOKE_OPTIONS = {
  vus: 1,
  iterations: 1,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<5000'],
  },
};

export const LOAD_OPTIONS = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '10m', target: 10 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000', 'p(99)<4000'],
  },
};

export const STRESS_OPTIONS = {
  stages: [
    { duration: '2m', target: 20 },
    { duration: '5m', target: 20 },
    { duration: '2m', target: 50 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '3m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<5000'],
  },
};

export const SOAK_OPTIONS = {
  stages: [
    { duration: '2m', target: 5 },
    { duration: '30m', target: 5 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<3000'],
  },
};
