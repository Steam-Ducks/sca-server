from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0011_merge_20260525_1442"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="fatoexecucaocarga",
            options={"managed": True},
        ),
        migrations.AlterField(
            model_name="fatoexecucaocarga",
            name="id",
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name="fatoexecucaocarga",
            name="tipo_processo",
            field=models.CharField(default="COMPLETA", max_length=20),
        ),
    ]
