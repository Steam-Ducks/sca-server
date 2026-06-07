# k6 — Testes de Carga

Testes de carga e monitoramento pós-deploy para a API SCA.

## Pré-requisitos

```bash
# macOS
brew install k6

# Ubuntu/Debian
sudo apt-get install k6

# Windows (winget)
winget install k6 --source winget
```

## Variáveis de ambiente

| Variável             | Padrão                       | Descrição                          |
|----------------------|------------------------------|------------------------------------|
| `K6_BASE_URL`        | `http://localhost:8000`      | URL base da API                    |
| `K6_AUTH_USERNAME`   | _(vazio)_                    | Usuário para login JWT             |
| `K6_AUTH_PASSWORD`   | _(vazio)_                    | Senha para login JWT               |
| `K6_AUTH_ENDPOINT`   | `{BASE_URL}/api/auth/login/` | Endpoint de autenticação           |

Se `K6_AUTH_USERNAME` e `K6_AUTH_PASSWORD` não forem fornecidos, os testes rodam sem autenticação.

---

## Cenários disponíveis

### Smoke Test — pós-deploy
Verifica que todos os endpoints respondem após um deploy. Roda em ~1 minuto.

```bash
# Sem autenticação
K6_BASE_URL=https://api.seudominio.com k6 run scenarios/smoke.js

# Com autenticação
K6_BASE_URL=https://api.seudominio.com \
  K6_AUTH_USERNAME=admin \
  K6_AUTH_PASSWORD=senha \
  k6 run scenarios/smoke.js
```

### Load Test — carga típica
Simula 10 usuários simultâneos por 10 minutos. Threshold: p95 < 2s, erro < 1%.

```bash
K6_BASE_URL=https://api.seudominio.com k6 run scenarios/load.js
```

### Stress Test — limite da API
Sobe progressivamente de 20 a 100 VUs para encontrar o ponto de saturação.

```bash
K6_BASE_URL=https://api.seudominio.com k6 run scenarios/stress.js
```

### Soak Test — estabilidade (30 min)
5 VUs por 30 minutos para detectar memory leaks e degradação progressiva.

```bash
K6_BASE_URL=https://api.seudominio.com k6 run scenarios/soak.js
```

---

## Enviando métricas para o Grafana Cloud

Aponte o remote write direto para o Grafana Cloud para que os resultados apareçam em `mariinetic.grafana.net`:

```bash
K6_BASE_URL=https://api.seudominio.com \
  K6_PROMETHEUS_RW_SERVER_URL=https://prometheus-prod-40-prod-sa-east-1.grafana.net/api/prom/push \
  K6_PROMETHEUS_RW_USERNAME=3046984 \
  K6_PROMETHEUS_RW_PASSWORD=<GF_CLOUD_METRICS_API_KEY> \
  K6_PROMETHEUS_RW_TREND_STATS="p(50),p(95),p(99),max" \
  k6 run --out experimental-prometheus-rw scenarios/smoke.js
```

### Local (sem Grafana Cloud)

Se quiser ver no Grafana local (`http://localhost:3000`), use o Prometheus local:

```bash
K6_BASE_URL=https://api.seudominio.com \
  K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
  K6_PROMETHEUS_RW_TREND_STATS="p(50),p(95),p(99),max" \
  k6 run --out experimental-prometheus-rw scenarios/smoke.js
```

### Métricas principais do k6 no Grafana

| Métrica                        | Descrição                            |
|-------------------------------|--------------------------------------|
| `k6_http_req_duration_p95`    | Latência p95 por endpoint            |
| `k6_http_req_failed_rate`     | Taxa de erros HTTP                   |
| `k6_vus`                      | Usuários virtuais ativos             |
| `k6_http_reqs_rate`           | Requisições por segundo              |
| `k6_http_req_waiting_p95`     | Tempo de espera pelo servidor (TTFB) |

---

## Estrutura dos arquivos

```
k6/
├── config.js        # Thresholds e opções de cada cenário
├── auth.js          # Helper de autenticação JWT
├── endpoints.js     # Funções de teste por grupo de endpoints
└── scenarios/
    ├── smoke.js     # 1 VU, 1 iteração — verificação pós-deploy
    ├── load.js      # 10 VUs, 14 min — carga típica
    ├── stress.js    # 20→100 VUs — encontrar limite
    └── soak.js      # 5 VUs, 34 min — estabilidade
```

---

## GitHub Actions

O workflow `.github/workflows/post-deploy-smoke.yml` roda automaticamente o smoke test
após cada deploy bem-sucedido no branch `develop`.

Secrets necessários no repositório:
- `PROD_API_URL` — URL base da API em produção
- `K6_AUTH_USERNAME` — usuário para autenticação
- `K6_AUTH_PASSWORD` — senha para autenticação
