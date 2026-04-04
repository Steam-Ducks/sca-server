from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SilverFornecedor",
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
                ("codigo_fornecedor", models.CharField(max_length=50, unique=True)),
                ("razao_social", models.CharField(max_length=255)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="SilverMaterial",
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
                ("codigo_material", models.CharField(max_length=50, unique=True)),
                ("descricao", models.CharField(max_length=255)),
                ("categoria", models.CharField(max_length=100)),
                (
                    "custo_estimado",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("silver_ingested_at", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="SilverPrograma",
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
                ("codigo_programa", models.CharField(max_length=50, unique=True)),
                ("nome_programa", models.CharField(max_length=255)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="SilverProjeto",
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
                ("codigo_projeto", models.CharField(max_length=50, unique=True)),
                ("nome_projeto", models.CharField(max_length=255)),
                ("silver_ingested_at", models.DateTimeField()),
                (
                    "programa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projetos",
                        to="sca_data.silverprograma",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SilverSolicitacaoCompra",
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
                ("numero_solicitacao", models.CharField(max_length=50, unique=True)),
                ("quantidade", models.PositiveIntegerField()),
                ("silver_ingested_at", models.DateTimeField()),
                (
                    "material",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solicitacoes",
                        to="sca_data.silvermaterial",
                    ),
                ),
                (
                    "projeto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solicitacoes",
                        to="sca_data.silverprojeto",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SilverPedidoCompra",
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
                ("numero_pedido", models.CharField(max_length=50, unique=True)),
                ("data_pedido", models.DateField(blank=True, null=True)),
                ("valor_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("silver_ingested_at", models.DateTimeField()),
                (
                    "fornecedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pedidos",
                        to="sca_data.silverfornecedor",
                    ),
                ),
                (
                    "solicitacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pedidos",
                        to="sca_data.silversolicitacaocompra",
                    ),
                ),
            ],
        ),
    ]
