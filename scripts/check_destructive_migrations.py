"""
Detecta operações destrutivas em arquivos de migration Django.

Padrões verificados:
  - RunSQL com DROP TABLE / DROP COLUMN / TRUNCATE / DELETE sem WHERE
  - DeleteModel, RemoveField, AlterField (narrowing de tipo ou NOT NULL)
  - RenameField / RenameModel sem backward compatibility

Retorna exit code 1 se encontrar risco CRÍTICO, 0 caso contrário.
Avisos (WARN) não travam o pipeline.
"""

import ast
import re
import sys
from pathlib import Path

# ─── Padrões SQL destrutivos ─────────────────────────────────────────────────

CRITICAL_SQL = [
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+COLUMN\b", "DROP COLUMN"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE sem WHERE"),
]

WARN_SQL = [
    (r"\bDROP\s+INDEX\b", "DROP INDEX"),
    (r"\bDROP\s+SCHEMA\b", "DROP SCHEMA"),
    (r"\bALTER\s+TABLE\b.*\bDROP\b", "ALTER TABLE ... DROP"),
]

# Operações Django ORM que indicam risco
CRITICAL_OPS = {"DeleteModel", "RemoveField"}
WARN_OPS = {"RenameField", "RenameModel", "AlterField"}

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _classify_run_sql(sql_str: str) -> tuple[list[str], list[str]]:
    """Retorna (criticos, avisos) encontrados no SQL."""
    sql_upper = sql_str.upper()
    crits, warns = [], []
    for pattern, label in CRITICAL_SQL:
        if re.search(pattern, sql_upper):
            crits.append(label)
    for pattern, label in WARN_SQL:
        if re.search(pattern, sql_upper):
            warns.append(label)
    return crits, warns


def _extract_run_sql_strings(node: ast.Call) -> list[str]:
    """Extrai argumento 'sql' de RunSQL(sql=...) ou RunSQL('...')."""
    strings = []
    # posicional
    if node.args:
        arg = node.args[0]
        if isinstance(arg, ast.Constant):
            strings.append(arg.value)
    # keyword
    for kw in node.keywords:
        if kw.arg == "sql" and isinstance(kw.value, ast.Constant):
            strings.append(kw.value.value)
    return strings


def analyze_file(path: Path) -> tuple[list[str], list[str]]:
    """Analisa um arquivo de migration e retorna (criticos, avisos)."""
    crits, warns = [], []
    source = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        warns.append(f"SyntaxError ao parsear: {e}")
        return crits, warns

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        if func_name == "RunSQL":
            for sql_str in _extract_run_sql_strings(node):
                c, w = _classify_run_sql(sql_str)
                crits.extend(c)
                warns.extend(w)

        elif func_name in CRITICAL_OPS:
            crits.append(func_name)

        elif func_name in WARN_OPS:
            warns.append(func_name)

    return crits, warns


# ─── Main ────────────────────────────────────────────────────────────────────


def collect_migration_files(root: Path) -> list[Path]:
    files = []
    for p in root.rglob("*.py"):
        parts = p.parts
        if "migrations" in parts and p.name != "__init__.py":
            files.append(p)
    return sorted(files)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    files = collect_migration_files(root)

    if not files:
        print("Nenhum arquivo de migration encontrado.")
        return 0

    total_crits = 0
    total_warns = 0

    print("=" * 60)
    print("  DETECÇÃO DE MIGRATIONS DESTRUTIVAS — sca-server")
    print("=" * 60)

    # Se rodando no CI, verifica apenas arquivos alterados no PR
    changed_only = "--changed-only" in sys.argv
    if changed_only:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/develop...HEAD"],
            capture_output=True,
            text=True,
        )
        changed = set(result.stdout.strip().splitlines())
        files = [f for f in files if str(f.relative_to(root)).replace("\\", "/") in changed]
        print(f"  Modo: apenas arquivos alterados no PR ({len(files)} migrations)\n")
    else:
        print(f"  Modo: todas as migrations ({len(files)} arquivos)\n")

    for f in files:
        rel = f.relative_to(root)
        crits, warns = analyze_file(f)

        if crits:
            total_crits += len(crits)
            print(f"  CRITICO  {rel}")
            for c in crits:
                print(f"           └─ {c}")

        if warns:
            total_warns += len(warns)
            if not crits:
                print(f"  AVISO    {rel}")
            for w in warns:
                print(f"           └─ {w} (revisar compatibilidade backward)")

    print("\n" + "=" * 60)
    if total_crits == 0 and total_warns == 0:
        print("  Nenhuma operação destrutiva detectada.")
        print("=" * 60)
        return 0

    print(f"  RESUMO: {total_crits} crítico(s) | {total_warns} aviso(s)")
    print("=" * 60)

    if total_crits > 0:
        print(
            "\n  Migrations com operações CRÍTICAS requerem aprovação manual."
            "\n  Verifique se existe migration de rollback e se o deploy"
            "\n  está agendado com janela de manutenção."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
