from django.db import models


class SilverPrograma(models.Model):
    codigo_programa = models.CharField(max_length=50, unique=True)
    nome_programa = models.CharField(max_length=255)
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.nome_programa


class SilverProjeto(models.Model):
    codigo_projeto = models.CharField(max_length=50, unique=True)
    nome_projeto = models.CharField(max_length=255)
    programa = models.ForeignKey(
        SilverPrograma,
        on_delete=models.CASCADE,
        related_name="projetos",
    )
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.nome_projeto


class SilverMaterial(models.Model):
    codigo_material = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100)
    custo_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.descricao


class SilverFornecedor(models.Model):
    codigo_fornecedor = models.CharField(max_length=50, unique=True)
    razao_social = models.CharField(max_length=255)
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.razao_social


class SilverSolicitacaoCompra(models.Model):
    numero_solicitacao = models.CharField(max_length=50, unique=True)
    projeto = models.ForeignKey(
        SilverProjeto,
        on_delete=models.CASCADE,
        related_name="solicitacoes",
    )
    material = models.ForeignKey(
        SilverMaterial,
        on_delete=models.CASCADE,
        related_name="solicitacoes",
    )
    quantidade = models.PositiveIntegerField()
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.numero_solicitacao


class SilverPedidoCompra(models.Model):
    numero_pedido = models.CharField(max_length=50, unique=True)
    solicitacao = models.ForeignKey(
        SilverSolicitacaoCompra,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    fornecedor = models.ForeignKey(
        SilverFornecedor,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    data_pedido = models.DateField(null=True, blank=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    silver_ingested_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.numero_pedido
