from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0002_alter_silvercomprasprojeto_silver_ingested_at_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SCHEMA IF NOT EXISTS gold;",
            reverse_sql="DROP SCHEMA IF EXISTS gold CASCADE;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE gold."indicators_materiais" (
                    id              SERIAL PRIMARY KEY,
                    categoria       VARCHAR(100),
                    custo_total     FLOAT,
                    total_itens     BIGINT,
                    custo_medio     FLOAT,
                    gold_updated_at TIMESTAMPTZ
                );
            """,
            reverse_sql='DROP TABLE IF EXISTS gold."indicators_materiais";',
        ),
    ]
