import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL } from './config.js';

const AUTH_ENDPOINT = __ENV.K6_AUTH_ENDPOINT || `${BASE_URL}/api/auth/login/`;

export function login() {
  const username = __ENV.K6_AUTH_USERNAME;
  const password = __ENV.K6_AUTH_PASSWORD;

  if (!username || !password) {
    throw new Error('[auth] K6_AUTH_USERNAME e K6_AUTH_PASSWORD são obrigatórios');
  }

  const res = http.post(
    AUTH_ENDPOINT,
    JSON.stringify({ username, password }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'auth_login' },
    }
  );

  check(res, {
    'login retorna 200': (r) => r.status === 200,
    'login retorna token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return !!(body.access || body.token);
      } catch {
        return false;
      }
    },
  });

  if (res.status !== 200) {
    throw new Error(`[auth] Login falhou com status ${res.status}: ${res.body}`);
  }

  const body = JSON.parse(res.body);
  const token = body.access || body.token;

  if (!token) {
    throw new Error('[auth] Login retornou 200 mas sem token na resposta');
  }

  return token;
}

export function authHeaders(token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}
