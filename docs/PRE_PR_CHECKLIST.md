# Pre-PR Checklist

Use esta checklist antes de abrir ou atualizar um PR para `develop`.
Ela espelha os checks principais que rodam no GitHub Actions.

## 1. Lint e formatacao

O job `CI - Feature Branch / Lint & Format` roda:

```bash
ruff check .
black --check .
```

No ambiente local do repo, rode:

```bash
./venv/bin/python -m ruff check .
./venv/bin/python -m black --check .
```

Se o Black falhar com `would reformat`, corrija com:

```bash
./venv/bin/python -m black .
```

Depois rode novamente:

```bash
./venv/bin/python -m ruff check .
./venv/bin/python -m black --check .
git diff --check
```

Importante: se `Lint & Format` falhar no CI, os jobs dependentes podem aparecer como
`skipped`. Corrija primeiro o lint/formatacao e faca novo push.

## 2. Auto merge

O job `CI - Feature Branch / Auto Merge PR` precisa respeitar as politicas da
branch base. Use `gh pr merge --auto` no workflow para deixar o GitHub concluir
o merge somente depois que todos os requisitos obrigatorios forem satisfeitos.

Sem `--auto`, o GitHub CLI pode falhar com:

```text
the base branch policy prohibits the merge
```

## 3. Testes unitarios

O job de unit tests roda a suite sem testes de integracao:

```bash
./venv/bin/python -m pytest -m "not integration" -q
```

Quando a mudanca for pequena, rode tambem os testes diretamente relacionados ao
modulo alterado antes da suite completa.

## 4. Testes de integracao

O CI roda os testes de integracao com PostgreSQL real e os schemas `silver`,
`gold` e `audit`.

Localmente, rode quando a mudanca tocar banco, models, migrations, queries ou
fluxos que dependem de dados reais:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=test_db
export DB_USER=test_user
export DB_PASSWORD=test_password

./venv/bin/python manage.py migrate
./venv/bin/python -m pytest -m integration --reuse-db -v
```

## 5. Checks de banco

Antes de PRs com migrations ou alteracoes em models, rode:

```bash
./venv/bin/python scripts/check_destructive_migrations.py --changed-only
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py migrate --noinput
./venv/bin/python scripts/check_db_compatibility.py
```

## 6. Smoke e carga

O CI tambem sobe a aplicacao e roda:

```bash
./venv/bin/python tests/smoke/smoke_test.py
k6 run tests/load/load_test.js
```

Esses checks exigem app, banco e variaveis de ambiente preparados. Rode
localmente quando a mudanca tocar rotas, autenticacao, configuracao, performance
ou comportamento de ponta a ponta.

## 7. Antes do commit final

Checklist curta:

```bash
./venv/bin/python -m ruff check .
./venv/bin/python -m black --check .
git diff --check
./venv/bin/python -m pytest -m "not integration" -q
```

Se algum comando automatico alterar arquivos, revise o diff e inclua as
mudancas no commit.
