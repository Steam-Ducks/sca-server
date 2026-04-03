from rest_framework import generics

from sca_data.models import SilverPedidoCompra
from materials.serializers import MaterialsTableSerializer


class MaterialsTableView(generics.ListAPIView):
    serializer_class = MaterialsTableSerializer

    def get_queryset(self):
        return (
            SilverPedidoCompra.objects.select_related(
                "solicitacao__material",
                "solicitacao__projeto__programa",
                "fornecedor",
            )
            .filter(solicitacao__isnull=False)
            .order_by("-valor_total")
        )
