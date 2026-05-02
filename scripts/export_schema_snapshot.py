import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.db import connection  # noqa: E402


def fetch_tables(cursor):
    cursor.execute(
        """
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """
    )
    return [row[0] for row in cursor.fetchall()]


def fetch_columns(cursor, table):
    cursor.execute(
        """
        SELECT column_name, data_type, character_maximum_length,
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
    """,
        [table],
    )
    return [
        {
            "name": row[0],
            "type": row[1],
            "max_length": row[2],
            "nullable": row[3] == "YES",
            "default": row[4],
        }
        for row in cursor.fetchall()
    ]


def fetch_constraints(cursor, table):
    cursor.execute(
        """
        SELECT tc.constraint_name, tc.constraint_type,
               kcu.column_name,
               ccu.table_name AS foreign_table,
               ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.table_name = %s AND tc.table_schema = 'public'
        ORDER BY tc.constraint_type, tc.constraint_name
    """,
        [table],
    )
    return [
        {
            "name": row[0],
            "type": row[1],
            "column": row[2],
            "foreign_table": row[3],
            "foreign_column": row[4],
        }
        for row in cursor.fetchall()
    ]


def fetch_indexes(cursor, table):
    cursor.execute(
        """
        SELECT i.relname, ix.indisunique,
               array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum))
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i  ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = %s AND t.relkind = 'r'
        GROUP BY i.relname, ix.indisunique
        ORDER BY i.relname
    """,
        [table],
    )
    return [
        {"name": row[0], "unique": row[1], "columns": list(row[2])}
        for row in cursor.fetchall()
    ]


def fetch_applied_migrations(cursor):
    try:
        cursor.execute(
            """
            SELECT app, name, applied FROM django_migrations ORDER BY applied
        """
        )
        return [
            {"app": row[0], "name": row[1], "applied_at": row[2].isoformat()}
            for row in cursor.fetchall()
        ]
    except Exception:
        return []


def main():
    print("=" * 50)
    print("  SCHEMA SNAPSHOT — sca-server")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "tables": {},
        "applied_migrations": [],
    }

    with connection.cursor() as cursor:
        tables = fetch_tables(cursor)
        print(f"\nTabelas encontradas: {len(tables)}")

        for table in tables:
            print(f"  → {table}")
            snapshot["tables"][table] = {
                "columns": fetch_columns(cursor, table),
                "constraints": fetch_constraints(cursor, table),
                "indexes": fetch_indexes(cursor, table),
            }

        snapshot["applied_migrations"] = fetch_applied_migrations(cursor)

    with open("schema_snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print("\n✅ Snapshot salvo em: schema_snapshot.json")
    print(
        f"   {len(tables)} tabelas | {len(snapshot['applied_migrations'])} migrações registradas"
    )


if __name__ == "__main__":
    main()
