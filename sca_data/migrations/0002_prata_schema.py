from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data", "0001_initial"),
    ]

    operations = [

        # -------------------------
        # SCHEMA
        # -------------------------
        migrations.RunSQL(
            sql="CREATE SCHEMA IF NOT EXISTS silver;",
            reverse_sql="DROP SCHEMA IF EXISTS silver CASCADE;",
        ),

        # -------------------------
        # PROGRAMAS
        # -------------------------
        migrations.CreateModel(
            name="silver_programa",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("codigo_programa", models.CharField(max_length=100)),
                ("nome_programa", models.CharField(max_length=100)),
                ("gerente_programa", models.CharField(max_length=100, null=True, blank=True)),
                ("gerente_tecnico", models.CharField(max_length=100, null=True, blank=True)),
                ("data_inicio", models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."programas"',
            },
        ),

        # -------------------------
        # MATERIAIS
        # -------------------------
        migrations.CreateModel(
            name="silver_material",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("codigo_material", models.CharField(max_length=50)),
                ("descricao", models.CharField(max_length=100, null=True, blank=True)),
                ("categoria", models.CharField(max_length=100, null=True, blank=True)),
                ("fabricante", models.CharField(max_length=100, null=True, blank=True)),
                ("custo_estimado", models.FloatField(null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."materiais"',
            },
        ),

        # -------------------------
        # FORNECEDORES
        # -------------------------
        migrations.CreateModel(
            name="silver_fornecedor",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("codigo_fornecedor", models.CharField(max_length=50)),
                ("razao_social", models.CharField(max_length=100, null=True, blank=True)),
                ("cidade", models.CharField(max_length=100, null=True, blank=True)),
                ("estado", models.CharField(max_length=2, null=True, blank=True)),
                ("categoria", models.CharField(max_length=100, null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."fornecedores"',
            },
        ),

        # -------------------------
        # PROJETOS
        # -------------------------
        migrations.CreateModel(
            name="silver_projeto",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("codigo_projeto", models.CharField(max_length=50)),
                ("nome_projeto", models.CharField(max_length=100, null=True, blank=True)),
                ("programa_id", models.BigIntegerField(null=True, blank=True)),
                ("responsavel", models.CharField(max_length=100, null=True, blank=True)),
                ("custo_hora", models.FloatField(null=True, blank=True)),
                ("data_inicio", models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."projetos"',
            },
        ),

        # -------------------------
        # TAREFAS PROJETO
        # -------------------------
        migrations.CreateModel(
            name="silver_tarefa_projeto",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("codigo_tarefa", models.CharField(max_length=50)),
                ("projeto_id", models.BigIntegerField()),
                ("titulo", models.CharField(max_length=100, null=True, blank=True)),
                ("responsavel", models.CharField(max_length=100, null=True, blank=True)),
                ("estimativa_horas", models.IntegerField(null=True, blank=True)),
                ("data_inicio", models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."tarefas_projeto"',
            },
        ),

        # -------------------------
        # TEMPO TAREFAS
        # -------------------------
        migrations.CreateModel(
            name="silver_tempo_tarefa",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("tarefa_id", models.BigIntegerField()),
                ("usuario", models.CharField(max_length=100, null=True, blank=True)),
                ("data", models.DateField()),
                ("horas_trabalhadas", models.FloatField()),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."tempo_tarefas"',
            },
        ),

        # -------------------------
        # SOLICITAÇÕES DE COMPRA
        # -------------------------
        migrations.CreateModel(
            name="silver_solicitacao_compra",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("numero_solicitacao", models.CharField(max_length=50)),
                ("projeto_id", models.BigIntegerField()),
                ("material_id", models.BigIntegerField()),
                ("quantidade", models.BigIntegerField()),
                ("data_solicitacao", models.DateField(null=True, blank=True)),
                ("prioridade", models.CharField(max_length=50, null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."solicitacoes_compra"',
            },
        ),

        # -------------------------
        # PEDIDOS DE COMPRA
        # -------------------------
        migrations.CreateModel(
            name="silver_pedido_compra",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("numero_pedido", models.CharField(max_length=50)),
                ("solicitacao_id", models.BigIntegerField(null=True, blank=True)),
                ("fornecedor_id", models.BigIntegerField()),
                ("data_pedido", models.DateField(null=True, blank=True)),
                ("data_previsao_entrega", models.DateField(null=True, blank=True)),
                ("valor_total", models.FloatField(null=True, blank=True)),
                ("status", models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."pedidos_compra"',
            },
        ),

        # -------------------------
        # COMPRAS POR PROJETO
        # -------------------------
        migrations.CreateModel(
            name="silver_compras_projeto",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("pedido_compra_id", models.BigIntegerField()),
                ("projeto_id", models.BigIntegerField()),
                ("valor_alocado", models.FloatField(null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."compras_projeto"',
            },
        ),

        # -------------------------
        # EMPENHO DE MATERIAIS
        # -------------------------
        migrations.CreateModel(
            name="silver_empenho_material",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("projeto_id", models.BigIntegerField()),
                ("material_id", models.BigIntegerField()),
                ("quantidade_empenhada", models.BigIntegerField()),
                ("data_empenho", models.DateField(null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."empenho_materiais"',
            },
        ),

        # -------------------------
        # ESTOQUE DE MATERIAIS
        # -------------------------
        migrations.CreateModel(
            name="silver_estoque_materiais_projeto",
            fields=[
                ("id", models.BigIntegerField(primary_key=True)),
                ("projeto_id", models.BigIntegerField()),
                ("material_id", models.BigIntegerField()),
                ("quantidade", models.BigIntegerField()),
                ("localizacao", models.CharField(max_length=100, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": '"silver"."estoque_materiais_projeto"',
            },
        ),
    ]