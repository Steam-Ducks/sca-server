from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("sca_data"), 
    ]

    operations = [

        migrations.RunSQL(
            sql="CREATE SCHEMA IF NOT EXISTS silver;",
            reverse_sql="DROP SCHEMA IF EXISTS silver CASCADE;",
        ),

        migrations.CreateModel(
            name="SilverPrograma",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_programa",   models.CharField(max_length=100)),
                ("nome_programa",     models.CharField(max_length=100)),
                ("gerente_programa",  models.CharField(max_length=100, null=True, blank=True)),
                ("gerente_tecnico",   models.CharField(max_length=100, null=True, blank=True)),
                ("data_inicio",       models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status",            models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."programas',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverMaterial",
            fields=[
                ("id",               models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_material",  models.CharField(max_length=50)),
                ("descricao",        models.CharField(max_length=100, null=True, blank=True)),
                ("categoria",        models.CharField(max_length=100, null=True, blank=True)),
                ("fabricante",       models.CharField(max_length=100, null=True, blank=True)),
                ("custo_estimado",   models.FloatField(null=True, blank=True)),
                ("status",           models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."materiais',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverFornecedor",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_fornecedor", models.CharField(max_length=50)),
                ("razao_social",      models.CharField(max_length=100, null=True, blank=True)),
                ("cidade",            models.CharField(max_length=100, null=True, blank=True)),
                ("estado",            models.CharField(max_length=2, null=True, blank=True)),
                ("categoria",         models.CharField(max_length=100, null=True, blank=True)),
                ("status",            models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."fornecedores',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_projeto",    models.CharField(max_length=50)),
                ("nome_projeto",      models.CharField(max_length=100, null=True, blank=True)),
                ("programa",          models.ForeignKey(
                                          "SilverPrograma",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          db_column="programa_id",
                                          null=True,
                                          blank=True,
                                          related_name="projetos",
                                      )),
                ("responsavel",       models.CharField(max_length=100, null=True, blank=True)),
                ("custo_hora",        models.FloatField(null=True, blank=True)),
                ("data_inicio",       models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status",            models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."projetos',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverTarefaProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_tarefa",     models.CharField(max_length=50)),
                ("projeto",           models.ForeignKey(
                                          "SilverProjeto",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          db_column="projeto_id",
                                          related_name="tarefas",
                                      )),
                ("titulo",            models.CharField(max_length=100, null=True, blank=True)),
                ("responsavel",       models.CharField(max_length=100, null=True, blank=True)),
                ("estimativa_horas",  models.IntegerField(null=True, blank=True)),
                ("data_inicio",       models.DateField(null=True, blank=True)),
                ("data_fim_prevista", models.DateField(null=True, blank=True)),
                ("status",            models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."tarefas_projeto',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverTempoTarefa",
            fields=[
                ("id",                 models.BigIntegerField(primary_key=True, serialize=False)),
                ("tarefa",             models.ForeignKey(
                                           "SilverTarefaProjeto",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           db_column="tarefa_id",
                                           related_name="tempos",
                                       )),
                ("usuario",            models.CharField(max_length=100, null=True, blank=True)),
                ("data",               models.DateField()),
                ("horas_trabalhadas",  models.FloatField()),
                ("silver_ingested_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."tempo_tarefas',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverSolicitacaoCompra",
            fields=[
                ("id",                 models.BigIntegerField(primary_key=True, serialize=False)),
                ("numero_solicitacao", models.CharField(max_length=50)),
                ("projeto",            models.ForeignKey(
                                           "SilverProjeto",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           db_column="projeto_id",
                                       )),
                ("material",           models.ForeignKey(
                                           "SilverMaterial",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           db_column="material_id",
                                       )),
                ("quantidade",         models.BigIntegerField()),
                ("data_solicitacao",   models.DateField(null=True, blank=True)),
                ("prioridade",         models.CharField(max_length=50, null=True, blank=True)),
                ("status",             models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."solicitacoes_compra',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverPedidoCompra",
            fields=[
                ("id",                    models.BigIntegerField(primary_key=True, serialize=False)),
                ("numero_pedido",         models.CharField(max_length=50)),
                ("solicitacao",           models.ForeignKey(
                                              "SilverSolicitacaoCompra",
                                              on_delete=django.db.models.deletion.DO_NOTHING,
                                              db_column="solicitacao_id",
                                              null=True,
                                              blank=True,
                                          )),
                ("fornecedor",            models.ForeignKey(
                                              "SilverFornecedor",
                                              on_delete=django.db.models.deletion.DO_NOTHING,
                                              db_column="fornecedor_id",
                                          )),
                ("data_pedido",           models.DateField(null=True, blank=True)),
                ("data_previsao_entrega", models.DateField(null=True, blank=True)),
                ("valor_total",           models.FloatField(null=True, blank=True)),
                ("status",                models.CharField(max_length=50, null=True, blank=True)),
                ("silver_ingested_at",    models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."pedidos_compra',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverComprasProjeto",
            fields=[
                ("id",               models.BigIntegerField(primary_key=True, serialize=False)),
                ("pedido_compra",    models.ForeignKey(
                                         "SilverPedidoCompra",
                                         on_delete=django.db.models.deletion.DO_NOTHING,
                                         db_column="pedido_compra_id",
                                     )),
                ("projeto",          models.ForeignKey(
                                         "SilverProjeto",
                                         on_delete=django.db.models.deletion.DO_NOTHING,
                                         db_column="projeto_id",
                                     )),
                ("valor_alocado",    models.FloatField(null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."compras_projeto',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverEmpenhoMaterial",
            fields=[
                ("id",                   models.BigIntegerField(primary_key=True, serialize=False)),
                ("projeto",              models.ForeignKey(
                                             "SilverProjeto",
                                             on_delete=django.db.models.deletion.DO_NOTHING,
                                             db_column="projeto_id",
                                         )),
                ("material",             models.ForeignKey(
                                             "SilverMaterial",
                                             on_delete=django.db.models.deletion.DO_NOTHING,
                                             db_column="material_id",
                                         )),
                ("quantidade_empenhada", models.BigIntegerField()),
                ("data_empenho",         models.DateField(null=True, blank=True)),
                ("silver_ingested_at",   models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."empenho_materiais',
                "managed": True,
            },
        ),

        migrations.CreateModel(
            name="SilverEstoqueMateriaisProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("projeto",           models.ForeignKey(
                                          "SilverProjeto",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          db_column="projeto_id",
                                      )),
                ("material",          models.ForeignKey(
                                          "SilverMaterial",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          db_column="material_id",
                                      )),
                ("quantidade",        models.BigIntegerField()),
                ("localizacao",       models.CharField(max_length=100, null=True, blank=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "db_table": 'silver"."estoque_materiais_projeto',
                "managed": True,
            },
        ),
    ]
