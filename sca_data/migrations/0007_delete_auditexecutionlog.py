from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0006_alter_goldbudgetsnapshot_gerente_programa_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AuditExecutionLog",
        ),
    ]
