from django.db import models


class SilverPrograma(models.Model):
    id = models.BigIntegerField(primary_key=True)
    codigo_programa = models.CharField(max_length=100)
    nome_programa = models.CharField(max_length=100)
    gerente_programa = models.CharField(max_length=100, null=True, blank=True)
    gerente_tecnico = models.CharField(max_length=100, null=True, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."programas'


class SilverMaterial(models.Model):
    id = models.BigIntegerField(primary_key=True)
    codigo_material = models.CharField(max_length=50)
    descricao = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    fabricante = models.CharField(max_length=100, null=True, blank=True)
    custo_estimado = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."materiais'


class SilverFornecedor(models.Model):
    id = models.BigIntegerField(primary_key=True)
    codigo_fornecedor = models.CharField(max_length=50)
    razao_social = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."fornecedores'


class SilverProjeto(models.Model):
    id = models.BigIntegerField(primary_key=True)
    codigo_projeto = models.CharField(max_length=50)
    nome_projeto = models.CharField(max_length=100, null=True, blank=True)

    programa = models.ForeignKey(
        SilverPrograma,
        on_delete=models.DO_NOTHING,
        db_column="programa_id",
        null=True,
        blank=True,
        related_name="projetos",
    )

    responsavel = models.CharField(max_length=100, null=True, blank=True)
    custo_hora = models.FloatField(null=True, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."projetos'


class SilverTarefaProjeto(models.Model):
    id = models.BigIntegerField(primary_key=True)
    codigo_tarefa = models.CharField(max_length=50)

    projeto = models.ForeignKey(
        SilverProjeto,
        on_delete=models.DO_NOTHING,
        db_column="projeto_id",
        related_name="tarefas",
    )

    titulo = models.CharField(max_length=100, null=True, blank=True)
    responsavel = models.CharField(max_length=100, null=True, blank=True)
    estimativa_horas = models.IntegerField(null=True, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."tarefas_projeto'


class SilverTempoTarefa(models.Model):
    id = models.BigIntegerField(primary_key=True)

    tarefa = models.ForeignKey(
        SilverTarefaProjeto,
        on_delete=models.DO_NOTHING,
        db_column="tarefa_id",
        related_name="tempos",
    )

    usuario = models.CharField(max_length=100, null=True, blank=True)
    data = models.DateField()
    horas_trabalhadas = models.FloatField()
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."tempo_tarefas'


class SilverSolicitacaoCompra(models.Model):
    id = models.BigIntegerField(primary_key=True)
    numero_solicitacao = models.CharField(max_length=50)

    projeto = models.ForeignKey(
        SilverProjeto, on_delete=models.DO_NOTHING, db_column="projeto_id"
    )

    material = models.ForeignKey(
        SilverMaterial, on_delete=models.DO_NOTHING, db_column="material_id"
    )

    quantidade = models.BigIntegerField()
    data_solicitacao = models.DateField(null=True, blank=True)
    prioridade = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."solicitacoes_compra'


class SilverPedidoCompra(models.Model):
    id = models.BigIntegerField(primary_key=True)
    numero_pedido = models.CharField(max_length=50)

    solicitacao = models.ForeignKey(
        SilverSolicitacaoCompra,
        on_delete=models.DO_NOTHING,
        db_column="solicitacao_id",
        null=True,
        blank=True,
    )

    fornecedor = models.ForeignKey(
        SilverFornecedor, on_delete=models.DO_NOTHING, db_column="fornecedor_id"
    )

    data_pedido = models.DateField(null=True, blank=True)
    data_previsao_entrega = models.DateField(null=True, blank=True)
    valor_total = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."pedidos_compra'


class SilverComprasProjeto(models.Model):
    id = models.BigIntegerField(primary_key=True)

    pedido_compra = models.ForeignKey(
        SilverPedidoCompra, on_delete=models.DO_NOTHING, db_column="pedido_compra_id"
    )

    projeto = models.ForeignKey(
        SilverProjeto, on_delete=models.DO_NOTHING, db_column="projeto_id"
    )

    valor_alocado = models.FloatField(null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."compras_projeto'


class SilverEmpenhoMaterial(models.Model):
    id = models.BigIntegerField(primary_key=True)

    projeto = models.ForeignKey(
        SilverProjeto, on_delete=models.DO_NOTHING, db_column="projeto_id"
    )

    material = models.ForeignKey(
        SilverMaterial, on_delete=models.DO_NOTHING, db_column="material_id"
    )

    quantidade_empenhada = models.BigIntegerField()
    data_empenho = models.DateField(null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."empenho_materiais'


class SilverEstoqueMateriaisProjeto(models.Model):
    id = models.BigIntegerField(primary_key=True)

    projeto = models.ForeignKey(
        SilverProjeto, on_delete=models.DO_NOTHING, db_column="projeto_id"
    )

    material = models.ForeignKey(
        SilverMaterial, on_delete=models.DO_NOTHING, db_column="material_id"
    )

    quantidade = models.BigIntegerField()
    localizacao = models.CharField(max_length=100, null=True, blank=True)
    silver_ingested_at = models.DateTimeField()

    class Meta:
        app_label = "sca_data"
        db_table = 'silver"."estoque_materiais_projeto'


class GoldIndicadoresMateriais(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    custo_total = models.FloatField(null=True, blank=True)
    total_itens = models.BigIntegerField(null=True, blank=True)
    custo_medio = models.FloatField(null=True, blank=True)
    gold_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "sca_data"
        db_table = 'gold"."indicadores_materiais'
        managed = False
