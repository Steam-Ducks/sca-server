import http from 'k6/http';
import { check, group } from 'k6';
import { BASE_URL } from './config.js';

function currentPeriod() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  return `${y}-${m}`;
}

function prevPeriod() {
  const d = new Date();
  d.setMonth(d.getMonth() - 1);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  return `${y}-${m}`;
}

function expectOk(res, name) {
  check(res, {
    [`${name}: status 2xx`]: (r) => r.status >= 200 && r.status < 300,
    [`${name}: tempo < 3s`]: (r) => r.timings.duration < 3000,
  });
}

export function testHealth(headers) {
  group('health', () => {
    expectOk(http.get(`${BASE_URL}/api/health/`, { headers }), 'health');
    expectOk(http.get(`${BASE_URL}/api/status/`, { headers }), 'status');
  });
}

export function testDashboard(headers) {
  group('dashboard', () => {
    expectOk(http.get(`${BASE_URL}/api/dashboard/kpis/`, { headers }), 'dashboard/kpis');
    expectOk(http.get(`${BASE_URL}/api/dashboard/projects/`, { headers }), 'dashboard/projects');
    expectOk(http.get(`${BASE_URL}/api/dashboard/summary/`, { headers }), 'dashboard/summary');
    expectOk(http.get(`${BASE_URL}/api/dashboard/composition/`, { headers }), 'dashboard/composition');
    expectOk(http.get(`${BASE_URL}/api/dashboard/top-projects/`, { headers }), 'dashboard/top-projects');
    expectOk(http.get(`${BASE_URL}/api/dashboard/cost-evolution/`, { headers }), 'dashboard/cost-evolution');
  });
}

export function testMaterials(headers) {
  const periodo = prevPeriod();
  group('materials', () => {
    expectOk(http.get(`${BASE_URL}/api/compras/`, { headers }), 'compras');
    expectOk(http.get(`${BASE_URL}/api/compras/periodo/${periodo}/`, { headers }), `compras/periodo`);
    expectOk(http.get(`${BASE_URL}/api/materials/indicators/`, { headers }), 'materials/indicators');
    expectOk(http.get(`${BASE_URL}/api/top-materials/`, { headers }), 'top-materials');
    expectOk(http.get(`${BASE_URL}/api/cost-by-project/`, { headers }), 'cost-by-project');
    expectOk(http.get(`${BASE_URL}/api/materials/filter-options/`, { headers }), 'materials/filter-options');
  });
}

export function testTechnicalHours(headers) {
  const periodo = prevPeriod();
  group('technical-hours', () => {
    expectOk(http.get(`${BASE_URL}/api/horas-tecnicas/`, { headers }), 'horas-tecnicas');
    expectOk(http.get(`${BASE_URL}/api/horas-tecnicas/periodo/${periodo}/`, { headers }), 'horas-tecnicas/periodo');
    expectOk(http.get(`${BASE_URL}/api/horas-tecnicas/kpis/`, { headers }), 'horas-tecnicas/kpis');
    expectOk(http.get(`${BASE_URL}/api/horas-tecnicas/temporal/`, { headers }), 'horas-tecnicas/temporal');
  });
}

export function testBudget(headers) {
  group('budget', () => {
    expectOk(http.get(`${BASE_URL}/api/budget/`, { headers }), 'budget');
    expectOk(http.get(`${BASE_URL}/api/budget/indicators/`, { headers }), 'budget/indicators');
  });
}

export function testCosts(headers) {
  group('costs', () => {
    expectOk(http.get(`${BASE_URL}/api/costs/`, { headers }), 'costs');
  });
}

export function testConsolidated(headers) {
  const periodo = prevPeriod();
  group('consolidated', () => {
    expectOk(http.get(`${BASE_URL}/api/consolidated/`, { headers }), 'consolidated');
    expectOk(http.get(`${BASE_URL}/api/consolidated/periodo/${periodo}/`, { headers }), 'consolidated/periodo');
  });
}

export function testAllEndpoints(headers) {
  testHealth(headers);
  testDashboard(headers);
  testMaterials(headers);
  testTechnicalHours(headers);
  testBudget(headers);
  testCosts(headers);
  testConsolidated(headers);
}
