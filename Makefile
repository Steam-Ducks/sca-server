PYTHON  = python
MANAGE  = $(PYTHON) manage.py

.PHONY: help setup ingest-bronze migrate transform-silver \
        test test-cov up up-full down ingest-docker

# ─── AJUDA ──────────────────────────────────────────────────────────────────

help: ## Mostra os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ─── ETL LOCAL ───────────────────────────────────────────────────────────────
# Requer que o PostgreSQL esteja acessível em localhost:5432 com as
# credenciais do .env. No Docker use os targets ingest-docker / setup-docker.

ingest-bronze: ## Cria schema bronze e ingere dados da API remota
	$(PYTHON) -m sca_data.db.bronze.ingestion

migrate: ## Cria schema silver + tabelas via Django migrations
	$(MANAGE) migrate

transform-silver: ## Transforma dados bronze → silver
	$(PYTHON) -m sca_data.db.silver.ingestion_silver

setup: ingest-bronze migrate transform-silver ## Setup completo: bronze → migrate → silver

# ─── TESTES ──────────────────────────────────────────────────────────────────

test: ## Roda todos os testes unitários
	pytest sca_data/tests/ -v

test-cov: ## Roda testes com relatório de cobertura
	coverage run -m pytest sca_data/tests/ -v
	coverage report -m

# ─── DOCKER ──────────────────────────────────────────────────────────────────

up: ## Sobe backend + postgres + prometheus + grafana
	docker-compose up --build

up-full: ## Sobe stack completa incluindo ELK (requer acesso à rede Elastic)
	docker-compose --profile observability up --build

down: ## Para e remove os containers
	docker-compose down

ingest-docker: ## Roda ingestão bronze + silver dentro do container em execução
	docker exec backend_app python -m sca_data.db.bronze.ingestion
	docker exec backend_app python -m sca_data.db.silver.ingestion_silver

setup-docker: ## Setup completo dentro do Docker (após 'make up')
	docker exec backend_app python -m sca_data.db.bronze.ingestion
	docker exec backend_app python manage.py migrate
	docker exec backend_app python -m sca_data.db.silver.ingestion_silver
