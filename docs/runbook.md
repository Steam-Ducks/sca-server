# Runbook — SCA Monitoramento

Guia operacional para investigação e resolução de alertas. Cada alerta dispara um email automático para `marianaoliveiry18@gmail.com`.

## Acesso rápido

| Recurso | URL |
|---|---|
| Grafana Cloud | https://mariinetic.grafana.net/dashboards |
| Visão Geral | https://mariinetic.grafana.net/d/sca-overview |
| Infraestrutura | https://mariinetic.grafana.net/d/sca-infra |
| Capacity Planning | https://mariinetic.grafana.net/d/sca-capacity |
| Aplicação | https://mariinetic.grafana.net/d/sca-app |
| Quality Gate | https://mariinetic.grafana.net/d/sca-quality-gate |
| Prometheus | http://143.198.2.189:9090 |

```bash
# SSH no VPS
ssh deploy@143.198.2.189
```

---

## Alertas Críticos

### `AppForaDoAr`
**O que significa:** A aplicação de produção não responde há mais de 1 minuto.

**Investigar:**
```bash
docker ps | grep backend_app
docker logs backend_app --tail=50
docker inspect --format='{{.State.Health.Status}}' backend_app
```

**Resolver:**
```bash
# Reiniciar o container
cd /home/deploy/sca-server
docker compose -f docker-compose.prod.yml restart backend

# Se não subir, rebuild
docker compose -f docker-compose.prod.yml up -d --build backend
```

**Escalar se:** container não subir após 2 tentativas ou logs mostrarem erro de banco.

---

### `DiscoEnchendoEm7Dias`
**O que significa:** No ritmo atual de crescimento, o disco vai encher em menos de 7 dias.

**Investigar:**
```bash
df -h /
du -sh /var/lib/docker/*
docker system df
```

**Resolver:**
```bash
# Limpar imagens e containers não usados
docker system prune -af --volumes

# Ver os maiores diretórios
du -sh /home/deploy/sca-server/logs/*
```

**Escalar se:** Após limpeza ainda < 7 dias. Expandir volume no DigitalOcean (Volumes → Resize).

---

### `ErrorRateAlto`
**O que significa:** Mais de 1% das requisições estão retornando 5xx nos últimos 5 minutos.

**Investigar:**
```bash
docker logs backend_app --tail=100 | grep ERROR
```

Verificar no dashboard [Aplicação](https://mariinetic.grafana.net/d/sca-app) qual endpoint está gerando erro (painel "Respostas por status code").

**Resolver:**
- Erro de banco → checar `docker logs sca_postgres_exporter`
- Erro de código → verificar último deploy em `git log --oneline -5`
- Rollback se necessário:
```bash
cd /home/deploy/sca-server
git checkout <sha-anterior>
docker compose -f docker-compose.prod.yml up -d --build backend
```

---

## Alertas de Aviso

### `DiscoEnchendoEm30Dias`
**O que significa:** Disco vai encher em menos de 30 dias no ritmo atual.

**Ação:** Sem urgência imediata. Monitorar tendência no dashboard [Capacity Planning](https://mariinetic.grafana.net/d/sca-capacity). Planejar expansão ou limpeza de logs/backups antes de 15 dias.

---

### `RAMAltaContínua`
**O que significa:** RAM acima de 85% por mais de 15 minutos.

**Investigar:**
```bash
free -h
docker stats --no-stream
```

**Resolver:**
```bash
# Ver qual container está consumindo mais
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Reiniciar container com leak suspeito
docker compose -f docker-compose.prod.yml restart <serviço>
```

---

### `CPUAltaContínua`
**O que significa:** CPU acima de 80% por mais de 10 minutos.

**Investigar:**
```bash
top -b -n 1 | head -20
docker stats --no-stream
```

Se for carga legítima (k6 test, backup, cron): aguardar normalizar.
Se for inesperado: verificar processo anômalo e reiniciar container suspeito.

---

### `LatenciaAltaP95`
**O que significa:** 95% das requisições levam mais de 2000ms para responder.

**Investigar:**
- Dashboard [Visão Geral](https://mariinetic.grafana.net/d/sca-overview) → painel "Latência ao longo do tempo"
- Ver se coincide com CPU ou RAM alta
- Verificar conexões ao banco:

```bash
docker logs backend_app --tail=50 | grep -i slow
```

**Resolver:** Geralmente correlacionado com RAM/CPU alta. Resolver o recurso raiz normaliza a latência.

---

## Inspeção Semanal

### `InspecaoSemanalSCA` / `DiscoCapacityAviso` / `RAMCapacityAviso` / `CPUCapacityAviso`
**O que significa:** Relatório automático semanal de capacidade. Recebido toda semana enquanto os limites de aviso estiverem ativos.

**Ação:** Revisar o dashboard [Capacity Planning](https://mariinetic.grafana.net/d/sca-capacity):
- Linha sólida vs linha tracejada (previsão 90 dias para disco)
- "Dias até 85% de uso" — se < 90 dias, planejar expansão
- "Fator de crescimento 30d" — se > 1.5x, avaliar upgrade do Droplet

Nenhuma ação imediata necessária se as previsões estão dentro do prazo.

---

## Referência rápida de containers

| Container | Função | Porta |
|---|---|---|
| `backend_app` | API Django (prod) | 8000 |
| `sca_staging_backend` | API Django (staging) | 8001 |
| `prometheus` | Coleta de métricas | 9090 |
| `sca_alertmanager` | Envio de alertas | 9093 |
| `grafana` | Dashboards locais | 3000 |
| `sca_node_exporter` | Métricas do servidor | 9100 |
| `postgres_exporter` | Métricas do PostgreSQL | 9187 |

```bash
# Ver todos os containers
docker ps

# Logs de qualquer container
docker logs <container> --tail=100 -f

# Reiniciar um serviço
docker compose -f docker-compose.prod.yml restart <serviço>
```
