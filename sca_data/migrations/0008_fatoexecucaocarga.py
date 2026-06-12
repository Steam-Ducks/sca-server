from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0007_delete_auditexecutionlog"),
    ]

    operations = [
        migrations.RunSQL("CREATE SCHEMA IF NOT EXISTS audit;"),
        migrations.CreateModel(
            name="FatoExecucaoCarga",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("run_id", models.UUIDField()),
                ("fonte", models.CharField(max_length=50)),
                ("tabela", models.CharField(max_length=100)),
                ("status", models.CharField(max_length=20)),
                ("linhas_processadas", models.IntegerField(blank=True, null=True)),
                ("detalhes_falha", models.TextField(blank=True, null=True)),
                ("iniciado_em", models.DateTimeField()),
                ("finalizado_em", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": 'audit"."fato_execucao_carga',
                "managed": True,
            },
        ),
    ]
