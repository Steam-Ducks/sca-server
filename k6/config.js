export const BASE_URL = __ENV.K6_BASE_URL || 'http://localhost:8000';

const STATUS_THRESHOLD = { 'http_req_duration{name:status}': ['p(95)<10000'] };

export const SMOKE_OPTIONS = {
  scenarios: {
    smoke: {
      executor: 'shared-iterations',
      vus: 1,
      iterations: 1,
      maxDuration: '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<5000'],
    ...STATUS_THRESHOLD,
  },
};

export const LOAD_OPTIONS = {
  scenarios: {
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '10m', target: 100 },
        { duration: '2m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000', 'p(99)<4000'],
    ...STATUS_THRESHOLD,
  },
};

export const STRESS_OPTIONS = {
  scenarios: {
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '5m', target: 20 },
        { duration: '2m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '3m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<5000'],
    ...STATUS_THRESHOLD,
  },
};

export const SOAK_OPTIONS = {
  scenarios: {
    soak: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 5 },
        { duration: '30m', target: 5 },
        { duration: '2m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<3000'],
    ...STATUS_THRESHOLD,
  },
};

export const ESCALATION_OPTIONS = {
  scenarios: {
    escalation: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '5m', target: 1000 },
        { duration: '5m', target: 1000 },
        { duration: '10m', target: 20000 },
        { duration: '5m', target: 20000 },
        { duration: '3m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.10'],
    http_req_duration: ['p(95)<15000'],
    ...STATUS_THRESHOLD,
  },
};
