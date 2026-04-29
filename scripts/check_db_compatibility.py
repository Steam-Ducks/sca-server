import json
import os
import sys
from datetime import datetime

# Insere o root do projeto no path para que 'config.settings' seja encontrado
# tanto no Docker (/app) quanto no CI (caminho do runner)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
django.setup()

from django.db import connection  # noqa: E402
from django.apps import apps  # noqa: E402
from django.db.migrations.executor import MigrationExecutor  # noqa: E402


def ok(msg):
    print(f"  ✅ {msg}")
    return {"status": "ok", "message": msg}

def warn(msg):
    print(f"  ⚠️  {msg}")
    return {"status": "warn", "message": msg}

def fail(msg):
    print(f"  ❌ {msg}")
    return {"status": "fail", "message": msg}


def check_connection():
    print("\n[1/5] Testando conexão com o banco...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return ok("Conexão com PostgreSQL estabelecida")
    except Exception as e:
        return fail(f"Falha na conexão: {e}")


def check_postgres_version():
    print("\n[2/5] Verificando versão do PostgreSQL...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version;")
            raw_version = cursor.fetchone()[0]
            cursor.execute("SELECT current_setting('server_version_num')::int")
            version_num = cursor.fetchone()[0]
        if version_num >= 140000:
            return ok(f"PostgreSQL {raw_version} (mínimo: 14.x)")
        else:
            return fail(f"PostgreSQL {raw_version} abaixo do mínimo exigido (14.x)")
    except Exception as e:
        return fail(f"Não foi possível verificar versão: {e}")


def check_pending_migrations():
    print("\n[3/5] Verificando migrações pendentes...")
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if not plan:
            return ok("Nenhuma migração pendente")
        else:
            pending = [str(m) for m, _ in plan]
            return fail(f"Migrações pendentes: {pending}")
    except Exception as e:
        return fail(f"Erro ao verificar migrações: {e}")


def check_model_table_consistency():
    print("\n[4/5] Verificando consistência models ↔ tabelas...")
    issues = []
    checked = 0

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_schema || '.' || table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        existing_tables |= {row[0] for row in cursor.fetchall()}

    for model in apps.get_models():
        table_name = model._meta.db_table
        checked += 1

        normalized = table_name.replace('"', '')
        found = (
            table_name in existing_tables or
            normalized in existing_tables or
            any(t.endswith('.' + normalized.split('.')[-1]) for t in existing_tables)
        )

        if not found:
            issues.append(f"Tabela ausente: '{table_name}' (model: {model.__name__})")
            continue

        model_columns = {
            field.column
            for field in model._meta.get_fields()
            if hasattr(field, "column") and not field.many_to_many
        }

        parts = normalized.split('.')
        if len(parts) == 2:
            schema, tbl = parts
        else:
            schema, tbl = 'public', parts[0]

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND table_schema = %s
            """, [tbl, schema])
            db_columns = {row[0] for row in cursor.fetchall()}

        missing = model_columns - db_columns
        if missing:
            issues.append(f"Colunas ausentes em '{table_name}': {missing}")

    if not issues:
        return ok(f"{checked} models verificados — todos consistentes com o banco")
    else:
        return fail(f"{len(issues)} inconsistência(s): {issues}")


def check_psycopg_driver():
    print("\n[5/5] Verificando driver psycopg...")
    try:
        import psycopg
        version = psycopg.__version__
        major = int(version.split(".")[0])
        if major >= 3:
            return ok(f"psycopg {version} (versão 3+)")
        else:
            return warn(f"psycopg {version} — recomendado atualizar para v3")
    except ImportError:
        return fail("psycopg3 não encontrado")


def main():
    print("=" * 55)
    print("  DB COMPATIBILITY CHECK — sca-server")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    results = {"timestamp": datetime.now().isoformat(), "checks": {}}

    checks = [
        ("connection",         check_connection),
        ("postgres_version",   check_postgres_version),
        ("pending_migrations", check_pending_migrations),
        ("model_consistency",  check_model_table_consistency),
        ("psycopg_driver",     check_psycopg_driver),
    ]

    has_failure = False
    for key, fn in checks:
        result = fn()
        results["checks"][key] = result
        if result["status"] == "fail":
            has_failure = True

    passed = sum(1 for v in results["checks"].values() if v["status"] == "ok")
    warned = sum(1 for v in results["checks"].values() if v["status"] == "warn")
    failed = sum(1 for v in results["checks"].values() if v["status"] == "fail")

    results["summary"] = {
        "total": len(checks),
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "compatible": not has_failure,
    }

    print("\n" + "=" * 55)
    print(f"  RESUMO: {passed}/{len(checks)} OK  |  {warned} avisos  |  {failed} falhas")
    print("=" * 55)

    with open("db_compatibility_report.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n📄 Relatório salvo em: db_compatibility_report.json")

    if has_failure:
        print("\n❌ Compatibilidade: FALHOU")
        sys.exit(1)
    else:
        print("\n✅ Compatibilidade: OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
