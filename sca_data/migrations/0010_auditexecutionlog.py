from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0009_fatoexecucaocarga_erros_avisos"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditExecutionLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("run_id", models.UUIDField()),
                ("operation", models.CharField(max_length=20)),
                ("status", models.CharField(max_length=20)),
                ("table_schema", models.CharField(blank=True, max_length=100, null=True)),
                ("table_name", models.CharField(blank=True, max_length=100, null=True)),
                ("affected_rows", models.IntegerField(blank=True, null=True)),
                ("started_at", models.DateTimeField()),
                ("finalized_at", models.DateTimeField(blank=True, null=True)),
                ("operation_duration", models.IntegerField(blank=True, null=True)),
                ("operation_metadata", models.JSONField(blank=True, null=True)),
            ],
            options={
                "db_table": 'audit"."execution_logs',
                "managed": False,
            },
        ),
    ]
