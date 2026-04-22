from rest_framework import serializers

from sca_data.models import SilverPedidoCompra


class MaterialsTableSerializer(serializers.ModelSerializer):
    valor_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, coerce_to_string=False
    )
    material = serializers.SerializerMethodField()
    projeto = serializers.SerializerMethodField()
    programa = serializers.SerializerMethodField()
    quantidade = serializers.SerializerMethodField()
    valor_unitario = serializers.SerializerMethodField()
    periodo = serializers.SerializerMethodField()
    fornecedor = serializers.SerializerMethodField()
    categoria = serializers.SerializerMethodField()

    class Meta:
        model = SilverPedidoCompra
        fields = [
            "id",
            "material",
            "projeto",
            "programa",
            "quantidade",
            "valor_unitario",
            "valor_total",
            "periodo",
            "fornecedor",
            "categoria",
        ]

    def get_material(self, obj):
        if obj.solicitacao and obj.solicitacao.material:
            return obj.solicitacao.material.descricao
        return None

    def get_projeto(self, obj):
        if obj.solicitacao and obj.solicitacao.projeto:
            return obj.solicitacao.projeto.nome_projeto
        return None

    def get_programa(self, obj):
        if (
            obj.solicitacao
            and obj.solicitacao.projeto
            and obj.solicitacao.projeto.programa
        ):
            return obj.solicitacao.projeto.programa.nome_programa
        return None

    def get_quantidade(self, obj):
        if obj.solicitacao:
            return obj.solicitacao.quantidade
        return None

    def get_valor_unitario(self, obj):
        if obj.solicitacao and obj.solicitacao.material:
            return obj.solicitacao.material.custo_estimado
        return None

    def get_periodo(self, obj):
        return getattr(obj, "data_pedido", None)

    def get_fornecedor(self, obj):
        if obj.fornecedor:
            return obj.fornecedor.razao_social
        return None

    def get_categoria(self, obj):
        if obj.solicitacao and obj.solicitacao.material:
            return obj.solicitacao.material.categoria
        return None


class MaterialsIndicatorsSerializer(serializers.Serializer):
    custo_total = serializers.FloatField(allow_null=True)
    total_itens = serializers.IntegerField()
    custo_medio = serializers.FloatField(allow_null=True)
