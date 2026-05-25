from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0009_fatoexecucaocarga_erros_avisos"),
    ]

    operations = [
        migrations.AddField(
            model_name="fatoexecucaocarga",
            name="tipo_processo",
            field=models.CharField(default="COMPLETA", max_length=20),
        ),
    ]
