import datetime

from sca_data.models import FatoExecucaoCarga


def get_execucoes_carga(status=None, data_inicio=None, data_fim=None):
    qs = FatoExecucaoCarga.objects.all()
    if status:
        qs = qs.filter(status=status)
    if data_inicio:
        if isinstance(data_inicio, str):
            data_inicio = datetime.date.fromisoformat(data_inicio)
        qs = qs.filter(iniciado_em__date__gte=data_inicio)
    if data_fim:
        if isinstance(data_fim, str):
            data_fim = datetime.date.fromisoformat(data_fim)
        qs = qs.filter(iniciado_em__date__lte=data_fim)
    return qs.order_by("-iniciado_em")
