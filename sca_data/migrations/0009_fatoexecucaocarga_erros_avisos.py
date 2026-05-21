from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0008_fatoexecucaocarga"),
    ]

    operations = [
        migrations.AddField(
            model_name="fatoexecucaocarga",
            name="erros",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="fatoexecucaocarga",
            name="avisos",
            field=models.IntegerField(default=0),
        ),
    ]
