from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = []

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
                ("gerente_programa",  models.CharField(blank=True, max_length=100, null=True)),
                ("gerente_tecnico",   models.CharField(blank=True, max_length=100, null=True)),
                ("data_inicio",       models.DateField(blank=True, null=True)),
                ("data_fim_prevista", models.DateField(blank=True, null=True)),
                ("status",            models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."programas'},
        ),

        migrations.CreateModel(
            name="SilverMaterial",
            fields=[
                ("id",               models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_material",  models.CharField(max_length=50)),
                ("descricao",        models.CharField(blank=True, max_length=100, null=True)),
                ("categoria",        models.CharField(blank=True, max_length=100, null=True)),
                ("fabricante",       models.CharField(blank=True, max_length=100, null=True)),
                ("custo_estimado",   models.FloatField(blank=True, null=True)),
                ("status",           models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."materiais'},
        ),

        migrations.CreateModel(
            name="SilverFornecedor",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_fornecedor", models.CharField(max_length=50)),
                ("razao_social",      models.CharField(blank=True, max_length=100, null=True)),
                ("cidade",            models.CharField(blank=True, max_length=100, null=True)),
                ("estado",            models.CharField(blank=True, max_length=2, null=True)),
                ("categoria",         models.CharField(blank=True, max_length=100, null=True)),
                ("status",            models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."fornecedores'},
        ),

        migrations.CreateModel(
            name="SilverProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_projeto",    models.CharField(max_length=50)),
                ("nome_projeto",      models.CharField(blank=True, max_length=100, null=True)),
                ("programa",          models.ForeignKey(
                                          blank=True,
                                          db_column="programa_id",
                                          null=True,
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          related_name="projetos",
                                          to="sca_data.silverprograma",
                                      )),
                ("responsavel",       models.CharField(blank=True, max_length=100, null=True)),
                ("custo_hora",        models.FloatField(blank=True, null=True)),
                ("data_inicio",       models.DateField(blank=True, null=True)),
                ("data_fim_prevista", models.DateField(blank=True, null=True)),
                ("status",            models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."projetos'},
        ),

        migrations.CreateModel(
            name="SilverTarefaProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("codigo_tarefa",     models.CharField(max_length=50)),
                ("projeto",           models.ForeignKey(
                                          db_column="projeto_id",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          related_name="tarefas",
                                          to="sca_data.silverprojeto",
                                      )),
                ("titulo",            models.CharField(blank=True, max_length=100, null=True)),
                ("responsavel",       models.CharField(blank=True, max_length=100, null=True)),
                ("estimativa_horas",  models.IntegerField(blank=True, null=True)),
                ("data_inicio",       models.DateField(blank=True, null=True)),
                ("data_fim_prevista", models.DateField(blank=True, null=True)),
                ("status",            models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."tarefas_projeto'},
        ),

        migrations.CreateModel(
            name="SilverTempoTarefa",
            fields=[
                ("id",                 models.BigIntegerField(primary_key=True, serialize=False)),
                ("tarefa",             models.ForeignKey(
                                           db_column="tarefa_id",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           related_name="tempos",
                                           to="sca_data.silvertarefaprojeto",
                                       )),
                ("usuario",            models.CharField(blank=True, max_length=100, null=True)),
                ("data",               models.DateField()),
                ("horas_trabalhadas",  models.FloatField()),
                ("silver_ingested_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."tempo_tarefas'},
        ),

        migrations.CreateModel(
            name="SilverSolicitacaoCompra",
            fields=[
                ("id",                 models.BigIntegerField(primary_key=True, serialize=False)),
                ("numero_solicitacao", models.CharField(max_length=50)),
                ("projeto",            models.ForeignKey(
                                           db_column="projeto_id",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           to="sca_data.silverprojeto",
                                       )),
                ("material",           models.ForeignKey(
                                           db_column="material_id",
                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                           to="sca_data.silvermaterial",
                                       )),
                ("quantidade",         models.BigIntegerField()),
                ("data_solicitacao",   models.DateField(blank=True, null=True)),
                ("prioridade",         models.CharField(blank=True, max_length=50, null=True)),
                ("status",             models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."solicitacoes_compra'},
        ),

        migrations.CreateModel(
            name="SilverPedidoCompra",
            fields=[
                ("id",                    models.BigIntegerField(primary_key=True, serialize=False)),
                ("numero_pedido",         models.CharField(max_length=50)),
                ("solicitacao",           models.ForeignKey(
                                              blank=True,
                                              db_column="solicitacao_id",
                                              null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING,
                                              to="sca_data.silversolicitacaocompra",
                                          )),
                ("fornecedor",            models.ForeignKey(
                                              db_column="fornecedor_id",
                                              on_delete=django.db.models.deletion.DO_NOTHING,
                                              to="sca_data.silverfornecedor",
                                          )),
                ("data_pedido",           models.DateField(blank=True, null=True)),
                ("data_previsao_entrega", models.DateField(blank=True, null=True)),
                ("valor_total",           models.FloatField(blank=True, null=True)),
                ("status",                models.CharField(blank=True, max_length=50, null=True)),
                ("silver_ingested_at",    models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."pedidos_compra'},
        ),

        migrations.CreateModel(
            name="SilverComprasProjeto",
            fields=[
                ("id",               models.BigIntegerField(primary_key=True, serialize=False)),
                ("pedido_compra",    models.ForeignKey(
                                         db_column="pedido_compra_id",
                                         on_delete=django.db.models.deletion.DO_NOTHING,
                                         to="sca_data.silverpedidocompra",
                                     )),
                ("projeto",          models.ForeignKey(
                                         db_column="projeto_id",
                                         on_delete=django.db.models.deletion.DO_NOTHING,
                                         to="sca_data.silverprojeto",
                                     )),
                ("valor_alocado",    models.FloatField(blank=True, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."compras_projeto'},
        ),

        migrations.CreateModel(
            name="SilverEmpenhoMaterial",
            fields=[
                ("id",                   models.BigIntegerField(primary_key=True, serialize=False)),
                ("projeto",              models.ForeignKey(
                                             db_column="projeto_id",
                                             on_delete=django.db.models.deletion.DO_NOTHING,
                                             to="sca_data.silverprojeto",
                                         )),
                ("material",             models.ForeignKey(
                                             db_column="material_id",
                                             on_delete=django.db.models.deletion.DO_NOTHING,
                                             to="sca_data.silvermaterial",
                                         )),
                ("quantidade_empenhada", models.BigIntegerField()),
                ("data_empenho",         models.DateField(blank=True, null=True)),
                ("silver_ingested_at",   models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."empenho_materiais'},
        ),

        migrations.CreateModel(
            name="SilverEstoqueMateriaisProjeto",
            fields=[
                ("id",                models.BigIntegerField(primary_key=True, serialize=False)),
                ("projeto",           models.ForeignKey(
                                          db_column="projeto_id",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          to="sca_data.silverprojeto",
                                      )),
                ("material",          models.ForeignKey(
                                          db_column="material_id",
                                          on_delete=django.db.models.deletion.DO_NOTHING,
                                          to="sca_data.silvermaterial",
                                      )),
                ("quantidade",        models.BigIntegerField()),
                ("localizacao",       models.CharField(blank=True, max_length=100, null=True)),
                ("silver_ingested_at",models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": 'silver"."estoque_materiais_projeto'},
        ),
    ]
