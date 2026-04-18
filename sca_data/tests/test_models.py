import django.db.models as dj_models

from sca_data.models import (SilverComprasProjeto, SilverEmpenhoMaterial,
                             SilverEstoqueMateriaisProjeto, SilverFornecedor,
                             SilverMaterial, SilverPedidoCompra,
                             SilverPrograma, SilverProjeto,
                             SilverSolicitacaoCompra, SilverTarefaProjeto,
                             SilverTempoTarefa)


def _get_field(model, name):
    return model._meta.get_field(name)


class TestSilverPrograma:
    def test_db_table(self):
        assert SilverPrograma._meta.db_table == 'silver"."programas'

    def test_id_is_primary_key(self):
        field = _get_field(SilverPrograma, "id")
        assert field.primary_key is True
        assert isinstance(field, dj_models.BigIntegerField)

    def test_codigo_programa_max_length(self):
        assert _get_field(SilverPrograma, "codigo_programa").max_length == 100

    def test_nome_programa_max_length(self):
        assert _get_field(SilverPrograma, "nome_programa").max_length == 100

    def test_status_max_length(self):
        assert _get_field(SilverPrograma, "status").max_length == 50

    def test_optional_fields_allow_null(self):
        for fname in (
            "gerente_programa",
            "gerente_tecnico",
            "data_inicio",
            "data_fim_prevista",
            "status",
        ):
            field = _get_field(SilverPrograma, fname)
            assert field.null is True, f"{fname} should allow null"

    def test_silver_ingested_at_is_datetimefield(self):
        assert isinstance(
            _get_field(SilverPrograma, "silver_ingested_at"), dj_models.DateTimeField
        )


class TestSilverMaterial:
    def test_db_table(self):
        assert SilverMaterial._meta.db_table == 'silver"."materiais'

    def test_codigo_material_max_length(self):
        assert _get_field(SilverMaterial, "codigo_material").max_length == 50

    def test_custo_estimado_is_floatfield(self):
        field = _get_field(SilverMaterial, "custo_estimado")
        assert isinstance(field, dj_models.FloatField)
        assert field.null is True


class TestSilverFornecedor:
    def test_db_table(self):
        assert SilverFornecedor._meta.db_table == 'silver"."fornecedores'

    def test_estado_max_length(self):
        assert _get_field(SilverFornecedor, "estado").max_length == 2

    def test_codigo_fornecedor_max_length(self):
        assert _get_field(SilverFornecedor, "codigo_fornecedor").max_length == 50


class TestSilverProjeto:
    def test_db_table(self):
        assert SilverProjeto._meta.db_table == 'silver"."projetos'

    def test_programa_fk_to_silver_programa(self):
        field = _get_field(SilverProjeto, "programa")
        assert isinstance(field, dj_models.ForeignKey)
        assert field.related_model is SilverPrograma

    def test_programa_fk_is_nullable(self):
        field = _get_field(SilverProjeto, "programa")
        assert field.null is True

    def test_programa_fk_db_column(self):
        field = _get_field(SilverProjeto, "programa")
        assert field.column == "programa_id"

    def test_programa_fk_do_nothing(self):
        field = _get_field(SilverProjeto, "programa")
        assert field.remote_field.on_delete.__name__ == "DO_NOTHING"

    def test_related_name_projetos(self):
        field = _get_field(SilverProjeto, "programa")
        assert field.remote_field.related_name == "projetos"

    def test_custo_hora_is_floatfield(self):
        assert isinstance(_get_field(SilverProjeto, "custo_hora"), dj_models.FloatField)


class TestSilverTarefaProjeto:
    def test_db_table(self):
        assert SilverTarefaProjeto._meta.db_table == 'silver"."tarefas_projeto'

    def test_projeto_fk_to_silver_projeto(self):
        field = _get_field(SilverTarefaProjeto, "projeto")
        assert isinstance(field, dj_models.ForeignKey)
        assert field.related_model is SilverProjeto

    def test_projeto_fk_db_column(self):
        assert _get_field(SilverTarefaProjeto, "projeto").column == "projeto_id"

    def test_related_name_tarefas(self):
        field = _get_field(SilverTarefaProjeto, "projeto")
        assert field.remote_field.related_name == "tarefas"

    def test_estimativa_horas_is_integerfield(self):
        assert isinstance(
            _get_field(SilverTarefaProjeto, "estimativa_horas"), dj_models.IntegerField
        )

    def test_codigo_tarefa_max_length(self):
        assert _get_field(SilverTarefaProjeto, "codigo_tarefa").max_length == 50


class TestSilverTempoTarefa:
    def test_db_table(self):
        assert SilverTempoTarefa._meta.db_table == 'silver"."tempo_tarefas'

    def test_tarefa_fk_to_silver_tarefa_projeto(self):
        field = _get_field(SilverTempoTarefa, "tarefa")
        assert field.related_model is SilverTarefaProjeto

    def test_tarefa_fk_db_column(self):
        assert _get_field(SilverTempoTarefa, "tarefa").column == "tarefa_id"

    def test_related_name_tempos(self):
        field = _get_field(SilverTempoTarefa, "tarefa")
        assert field.remote_field.related_name == "tempos"

    def test_horas_trabalhadas_is_floatfield(self):
        assert isinstance(
            _get_field(SilverTempoTarefa, "horas_trabalhadas"), dj_models.FloatField
        )

    def test_horas_trabalhadas_not_nullable(self):
        assert _get_field(SilverTempoTarefa, "horas_trabalhadas").null is False


class TestSilverSolicitacaoCompra:
    def test_db_table(self):
        assert SilverSolicitacaoCompra._meta.db_table == 'silver"."solicitacoes_compra'

    def test_projeto_fk(self):
        field = _get_field(SilverSolicitacaoCompra, "projeto")
        assert field.related_model is SilverProjeto

    def test_material_fk(self):
        field = _get_field(SilverSolicitacaoCompra, "material")
        assert field.related_model is SilverMaterial

    def test_quantidade_is_bigintegerfield(self):
        assert isinstance(
            _get_field(SilverSolicitacaoCompra, "quantidade"), dj_models.BigIntegerField
        )

    def test_numero_solicitacao_max_length(self):
        assert (
            _get_field(SilverSolicitacaoCompra, "numero_solicitacao").max_length == 50
        )


class TestSilverPedidoCompra:
    def test_db_table(self):
        assert SilverPedidoCompra._meta.db_table == 'silver"."pedidos_compra'

    def test_solicitacao_fk_is_nullable(self):
        field = _get_field(SilverPedidoCompra, "solicitacao")
        assert field.null is True

    def test_fornecedor_fk(self):
        field = _get_field(SilverPedidoCompra, "fornecedor")
        assert field.related_model is SilverFornecedor

    def test_valor_total_is_floatfield(self):
        assert isinstance(
            _get_field(SilverPedidoCompra, "valor_total"), dj_models.FloatField
        )

    def test_numero_pedido_max_length(self):
        assert _get_field(SilverPedidoCompra, "numero_pedido").max_length == 50


class TestSilverComprasProjeto:
    def test_db_table(self):
        assert SilverComprasProjeto._meta.db_table == 'silver"."compras_projeto'

    def test_pedido_compra_fk(self):
        field = _get_field(SilverComprasProjeto, "pedido_compra")
        assert field.related_model is SilverPedidoCompra

    def test_projeto_fk(self):
        field = _get_field(SilverComprasProjeto, "projeto")
        assert field.related_model is SilverProjeto

    def test_valor_alocado_is_floatfield(self):
        assert isinstance(
            _get_field(SilverComprasProjeto, "valor_alocado"), dj_models.FloatField
        )


class TestSilverEmpenhoMaterial:
    def test_db_table(self):
        assert SilverEmpenhoMaterial._meta.db_table == 'silver"."empenho_materiais'

    def test_projeto_fk(self):
        field = _get_field(SilverEmpenhoMaterial, "projeto")
        assert field.related_model is SilverProjeto

    def test_material_fk(self):
        field = _get_field(SilverEmpenhoMaterial, "material")
        assert field.related_model is SilverMaterial

    def test_quantidade_empenhada_is_bigintegerfield(self):
        assert isinstance(
            _get_field(SilverEmpenhoMaterial, "quantidade_empenhada"),
            dj_models.BigIntegerField,
        )


class TestSilverEstoqueMateriaisProjeto:
    def test_db_table(self):
        assert (
            SilverEstoqueMateriaisProjeto._meta.db_table
            == 'silver"."estoque_materiais_projeto'
        )

    def test_projeto_fk(self):
        field = _get_field(SilverEstoqueMateriaisProjeto, "projeto")
        assert field.related_model is SilverProjeto

    def test_material_fk(self):
        field = _get_field(SilverEstoqueMateriaisProjeto, "material")
        assert field.related_model is SilverMaterial

    def test_quantidade_is_bigintegerfield(self):
        assert isinstance(
            _get_field(SilverEstoqueMateriaisProjeto, "quantidade"),
            dj_models.BigIntegerField,
        )

    def test_localizacao_max_length(self):
        assert (
            _get_field(SilverEstoqueMateriaisProjeto, "localizacao").max_length == 100
        )
