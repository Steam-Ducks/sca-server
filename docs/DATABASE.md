# Database — sca-server

Reference document for the development team. Covers everything you need to know to work with the project's database correctly and safely.

---

## Objetivo

Este documento estabelece as regras, fluxos e boas práticas para trabalhar com o banco de dados do `sca-server`. O objetivo é garantir que toda mudança de schema seja rastreável, todo deploy seja seguro e nenhum dado seja perdido por acidente.

---

## Overview

### Ambientes

| Ambiente | Banco | Host | SSL |
|---|---|---|---|
| Local (dev) | PostgreSQL 16 via Docker | localhost:5432 | Não |
| CI (GitHub Actions) | PostgreSQL 16 via service container | localhost:5432 | Não |
| Produção | DigitalOcean Managed PostgreSQL | *.db.ondigitalocean.com:25060 | Obrigatório |

### Schemas

O banco usa 3 schemas além do `public`:

| Schema | Finalidade |
|---|---|
| `public` | Tabelas de negócio (usuários, dashboard, orçamento, etc.) |
| `silver` | Dados brutos processados (camada de ingestão) |
| `gold` | Dados agregados para dashboards |
| `audit` | Logs de execução de carga |

Os schemas `silver`, `gold` e `audit` são criados automaticamente pela migration `sca_data/migrations/0001_silver_schema.py` — não é necessário criá-los manualmente.

### Ferramenta de Migration

O projeto usa o sistema nativo de migrations do Django. Não há Flyway, Liquibase ou Alembic. Cada mudança em um model Django gera um arquivo Python versionado na pasta `migrations/` do app correspondente.

### Pipeline de Segurança (visão geral)

```
PR aberto
    │
    ▼
[1] Destructive Migration Check   ← bloqueia se encontrar DROP, TRUNCATE, DeleteModel
    │
    ▼
[2] Migration Lint                ← aplica todas as migrations em PostgreSQL 16 real
    │
    ▼
[3] Schema Snapshot               ← apenas na main: exporta snapshot para rastreabilidade
```

---

## Configuração

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.12

### Passo a Passo (ambiente local)

```bash
# 1. Copie o arquivo de variáveis de ambiente
cp .env.example .env
# Edite o .env se necessário (as configurações padrão já funcionam com Docker)

# 2. Suba apenas o banco de dados
docker compose up postgres -d

# 3. Instale as dependências Python
pip install -r requirements.txt

# 4. Aplique todas as migrations
python manage.py migrate

# 5. Popule o banco com dados de desenvolvimento
SEED_ENABLED=true python manage.py seed_db

# 6. Suba a aplicação completa (opcional)
docker compose up -d
```

Após o `migrate`, o banco já terá os schemas `silver`, `gold` e `audit` criados e os perfis do sistema (Financeiro, Compras, etc.) populados pela `0002_seed_data.py`.

### Variáveis de Ambiente por Ambiente

| Variável | Dev (local) | Staging | Produção |
|---|---|---|---|
| `DB_HOST` | `postgres` (Docker) | host DO staging | host DO produção |
| `DB_PORT` | `5432` | `25060` | `25060` |
| `DB_NAME` | `app_db` | `sca_staging` | `defaultdb` |
| `DB_USER` | `app_user` | `doadmin` | `doadmin` |
| `DB_PASSWORD` | `app_password` | `${SECRET}` | `${SECRET}` |
| `DB_SSL_MODE` | não definido | `require` | `require` |
| `SEED_ENABLED` | `true` | `true` | não definir |
| `DEBUG` | `True` | `False` | `False` |

### Arquivos de Referência

| Arquivo | Uso |
|---|---|
| `.env.example` | Template para o ambiente local (dev) |
| `.env.staging.example` | Template para staging |
| `.env` | Arquivo real (está no `.gitignore` — nunca commitar) |

**Regra de ouro:** Nenhuma credencial real vai para o Git. Use sempre placeholders (`${DB_PASSWORD}`) nos arquivos de exemplo e configure os valores reais diretamente no servidor ou nos GitHub Actions Secrets.

### Workflow de Migrations

Sempre que você alterar um model Django, siga este fluxo:

```bash
# 1. Faça a alteração no model (ex: users/models.py)

# 2. Gere a migration
python manage.py makemigrations

# 3. Revise o arquivo gerado antes de aplicar
#    Verifique se o que foi gerado corresponde ao que você esperava

# 4. Aplique no banco local
python manage.py migrate

# 5. Confirme que está tudo OK
python manage.py check
```

### Seed de Dados

O projeto tem dois tipos de seed com finalidades diferentes:

**Seed de sistema (`0002_seed_data.py`)** — roda automaticamente junto com o `migrate` em todos os ambientes, incluindo produção. Contém perfis de negócio e o usuário administrador inicial. Não é dado de teste — é configuração de negócio.

> Após o primeiro deploy em produção, altere a senha do superadmin imediatamente:
> ```bash
> python manage.py changepassword superadmin
> ```

**Seed de desenvolvimento (`manage.py seed_db`)** — popula o banco com dados fictícios realistas (3 programas, 8 projetos, 3 fornecedores, 8 tarefas). Só funciona com `SEED_ENABLED=true` — em produção, o comando recusa com erro explícito.

```bash
# Rodar seed de desenvolvimento
SEED_ENABLED=true python manage.py seed_db

# Rodar seed limpando os dados anteriores primeiro
SEED_ENABLED=true python manage.py seed_db --flush
```

| Situação | O que usar |
|---|---|
| Ambiente local do zero | `migrate` + `seed_db` |
| CI (testes de integração) | apenas `migrate` (sem seed) |
| Staging após reset | `migrate` + `seed_db` |
| Produção (primeiro deploy) | apenas `migrate` |
| Produção (deploys seguintes) | apenas `migrate` |

---

## Segurança

### Migrations Destrutivas

Qualquer operação que apaga dados ou estrutura de forma irreversível é considerada destrutiva:

| Operação Django | SQL Equivalente | Risco |
|---|---|---|
| `DeleteModel` | `DROP TABLE` | Crítico |
| `RemoveField` | `ALTER TABLE ... DROP COLUMN` | Crítico |
| `RunSQL("TRUNCATE ...")` | `TRUNCATE TABLE` | Crítico |
| `RunSQL("DROP ...")` | `DROP TABLE / DROP COLUMN` | Crítico |
| `RunSQL("DELETE FROM ...")` | `DELETE sem WHERE` | Crítico |
| `RunSQL("DELETE FROM ... WHERE ...")` | `DELETE com WHERE` | Aceitável |
| `RenameField` | `ALTER TABLE ... RENAME COLUMN` | Atenção |
| `RenameModel` | `ALTER TABLE ... RENAME TO` | Atenção |

O job **Destructive Migration Check** analisa automaticamente toda migration alterada no PR via análise AST (Abstract Syntax Tree). Se encontrar operação crítica, o pipeline para com exit code 1 e o PR não pode ser mergeado.

**Como proceder quando realmente precisar de uma operação destrutiva:**

1. Alinhe com o tech lead antes de criar a migration
2. Documente o motivo no card da tarefa
3. Verifique se há dados que serão perdidos — consulte o banco de dev/staging
4. Crie uma migration de rollback manual se necessário
5. Agende uma janela de manutenção para o deploy em produção
6. O tech lead aprova o merge manualmente após validar o plano

**Padrão recomendado — Depreciação em fases:**

```
Sprint N:   Marcar o campo como null=True, blank=True (não destrutivo)
            Remover o código que usa o campo
            Fazer deploy e confirmar que nada quebrou

Sprint N+1: Criar a migration de RemoveField
            Fazer deploy com backup e janela de manutenção
```

### Deploy e Produção

Quando um commit chega na branch `main`, o pipeline roda automaticamente:

```
[1] Carrega as variáveis do .env do servidor de produção
[2] pg_dump → salva backup completo do banco ANTES de qualquer mudança
[3] git pull → atualiza o código no servidor
[4] python manage.py migrate → aplica as migrations novas
    └── SE FALHAR:
        pg_restore → restaura o backup do passo [2]
        notifica o Slack com link para o log de erro
        pipeline para — deploy não acontece
[5] docker compose up --build → sobe a nova versão da aplicação
[6] notifica o Slack com resultado (✅ ou ❌)
```

**Proibido em produção:**

```bash
# PROIBIDO — migrations manuais fora do pipeline
python manage.py migrate  # no servidor, fora do CI/CD

# PROIBIDO — acesso direto ao banco sem autorização
psql -h prod-host -U doadmin -d defaultdb

# PROIBIDO — alterar dados por SQL direto
UPDATE users_user SET is_superuser = true WHERE id = 1;
```

**Quando o acesso direto for necessário** (emergência, investigação), deve ser:

- Solicitado ao tech lead com justificativa
- Feito via SSH no servidor — nunca expondo a porta 25060 diretamente
- Registrado — anote o que foi consultado/alterado e por quê
- Somente leitura por padrão. Qualquer escrita exige autorização explícita

### Backup e Restore

| Tipo | Local | Retenção |
|---|---|---|
| Pré-deploy | `/home/deploy/backups/pre_deploy_TIMESTAMP.dump` (servidor) | Manual |
| Backup diário | `/home/deploy/backups/sca_backup_TIMESTAMP.dump` (servidor) | 30 dias |

O backup diário roda automaticamente todo dia às 03:00 UTC (00:00 horário de Brasília).

```bash
# Backup manual (no servidor de produção, com .env carregado)
source .env
./scripts/db_backup.sh

# Restore (requer autorização do tech lead)
# 1. Liste os backups disponíveis
ls -lh /home/deploy/backups/sca_backup_*.dump

# 2. Execute o restore
source .env
CONFIRM_RESTORE=yes ./scripts/db_restore.sh /home/deploy/backups/sca_backup_20260525_030000.dump

# 3. Valide após o restore
python manage.py check
python manage.py showmigrations
```

O `CONFIRM_RESTORE=yes` é obrigatório para evitar restore acidental.

---

## FAQ / Use Cases

**"Não consigo conectar ao banco local"**
```bash
# Verifique se o container está rodando
docker compose ps

# Se não estiver, suba
docker compose up postgres -d

# Verifique as variáveis do .env
cat .env | grep DB_
```

**"Migration falhou com 'schema not found'"**

Os schemas `silver`, `gold` e `audit` são criados pela primeira migration do `sca_data`. Se aparecer `schema "silver" does not exist`, as migrations não foram aplicadas na ordem correta:
```bash
python manage.py migrate sca_data zero  # desfaz as migrations do sca_data
python manage.py migrate                # reaplicatudo na ordem correta
```

**"O CI está falhando com 'pending migrations'"**

Você alterou um model mas esqueceu de gerar a migration:
```bash
python manage.py makemigrations
git add nome_do_app/migrations/XXXX_descricao.py
```

**"O CI detectou uma migration destrutiva mas eu preciso mergear"**

Consulte o tech lead → documente o impacto no card → o tech lead mergeia manualmente após validar o plano de deploy → agende o deploy para horário de baixo uso.

**"Quero resetar meu banco local do zero"**
```bash
docker compose down -v           # para o banco e remove o volume
docker compose up postgres -d    # sobe o banco vazio
python manage.py migrate
SEED_ENABLED=true python manage.py seed_db
```

**"Como vejo o schema atual do banco?"**
```bash
python scripts/export_schema_snapshot.py
cat schema_snapshot.json
```

**"manage.py seed_db retornou erro de model não encontrado"**

As migrations precisam estar aplicadas antes do seed:
```bash
python manage.py migrate
SEED_ENABLED=true python manage.py seed_db
```

**"Como rodar os testes de integração localmente?"**
```bash
docker compose up postgres -d
python manage.py migrate --settings=config.settings_integration
pytest -m integration --ds=config.settings_integration --reuse-db -v
```

---

## Considerações

### O que bloqueia um PR relacionado ao banco

| Situação | Job que falha |
|---|---|
| Alterou model sem gerar migration | Migration Lint |
| Migration com DROP, TRUNCATE, DeleteModel, RemoveField | Destructive Check |
| Migration com SQL inválido | Integration Tests |
| Model e banco fora de sincronia | DB Compatibility Check |
| Arquivo `.py` fora do padrão black/ruff | Lint |

### Como verificar localmente antes de abrir PR

```bash
# Verificar se há migrations faltando
python manage.py makemigrations --check --dry-run

# Rodar o check de migrations destrutivas
python scripts/check_destructive_migrations.py

# Rodar o check de compatibilidade model ↔ banco
python scripts/check_db_compatibility.py

# Formatar código (obrigatório antes do commit)
python -m black .
python -m ruff check .
```

### Regras que nunca devem ser quebradas

- Nunca edite migrations já aplicadas em `develop` ou `main`
- Nunca delete arquivos de migration do repositório
- Nunca aplique migrations manualmente direto no banco de produção
- Nunca comite o arquivo `.env` com credenciais reais
- Nunca rode seed em produção
- Todo `RunSQL` deve ter `reverse_sql` correspondente

### Referência Rápida — Comandos do Dia a Dia

```bash
# Subir o banco local
docker compose up postgres -d

# Aplicar migrations
python manage.py migrate

# Gerar migration após alterar model
python manage.py makemigrations

# Ver estado das migrations
python manage.py showmigrations

# Verificar migrations pendentes
python manage.py makemigrations --check --dry-run

# Seed de desenvolvimento
SEED_ENABLED=true python manage.py seed_db

# Seed com limpeza prévia
SEED_ENABLED=true python manage.py seed_db --flush

# Verificar migrations destrutivas (roda antes do PR)
python scripts/check_destructive_migrations.py

# Verificar compatibilidade model ↔ banco
python scripts/check_db_compatibility.py

# Exportar snapshot do schema
python scripts/export_schema_snapshot.py

# Backup manual (produção)
source .env && ./scripts/db_backup.sh

# Restore (produção — requer autorização)
source .env && CONFIRM_RESTORE=yes ./scripts/db_restore.sh /caminho/backup.dump
```
