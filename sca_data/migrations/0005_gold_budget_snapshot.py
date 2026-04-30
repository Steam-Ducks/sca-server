from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0004_auditexecutionlog_goldcosts_goldindicadoresmateriais"),
    ]

    operations = [
        migrations.CreateModel(
            name="GoldBudgetSnapshot",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("projeto_id", models.BigIntegerField(blank=True, null=True)),
                (
                    "nome_projeto",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "nome_programa",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "gerente_programa",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "responsavel_projeto",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("budget", models.FloatField(blank=True, null=True)),
                ("custo_materiais", models.FloatField(blank=True, null=True)),
                ("custo_horas", models.FloatField(blank=True, null=True)),
                ("custo_real", models.FloatField(blank=True, null=True)),
                ("desvio_percent", models.FloatField(blank=True, null=True)),
                (
                    "saude_financeira",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("projecao_estouro", models.FloatField(blank=True, null=True)),
                ("periodo", models.CharField(blank=True, max_length=7, null=True)),
                ("status", models.CharField(blank=True, max_length=50, null=True)),
                ("gold_updated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": 'gold"."budget_snapshot',
            },
        ),
    ]
