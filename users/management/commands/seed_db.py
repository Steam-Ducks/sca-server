"""
Management command: python manage.py seed_db

Popula o banco com dados de teste para desenvolvimento local.

NUNCA roda em produção: requer SEED_ENABLED=true explícito.
O seed da migration 0002_seed_data.py cria usuários de sistema (perfis
de negócio necessários em todos os ambientes). Este command adiciona
dados de teste adicionais — projetos fictícios, planilhas de exemplo —
que só fazem sentido em dev/staging.

Uso:
    SEED_ENABLED=true python manage.py seed_db
    SEED_ENABLED=true python manage.py seed_db --flush   # limpa antes de semear
"""

import os
from datetime import date

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

# Dados de desenvolvimento — senhas fracas intencionais, nunca vão para prod
_DEV_USERS = [
    {
        "username": "dev_admin",
        "name": "Dev Admin",
        "email": "dev_admin@dev.local",
        "password": "dev_only_123",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "dev_viewer",
        "name": "Dev Viewer",
        "email": "dev_viewer@dev.local",
        "password": "dev_only_123",
        "is_staff": False,
        "is_superuser": False,
    },
]

_PROGRAMAS = [
    {
        "id": 1,
        "codigo_programa": "MANSUP",
        "nome_programa": "Manufatura Supervisionada",
        "gerente_programa": "Ana Lima",
        "gerente_tecnico": "Carlos Souza",
        "data_inicio": date(2024, 1, 15),
        "data_fim_prevista": date(2025, 12, 31),
        "status": "Em andamento",
    },
    {
        "id": 2,
        "codigo_programa": "MAX1.2AC",
        "nome_programa": "MAX 1.2 AC",
        "gerente_programa": "Roberto Alves",
        "gerente_tecnico": "Mariana Costa",
        "data_inicio": date(2024, 3, 1),
        "data_fim_prevista": date(2026, 6, 30),
        "status": "Em andamento",
    },
    {
        "id": 3,
        "codigo_programa": "INNOV3",
        "nome_programa": "Inovação Tecnológica 3",
        "gerente_programa": "Fernanda Reis",
        "gerente_tecnico": "Paulo Melo",
        "data_inicio": date(2023, 6, 1),
        "data_fim_prevista": date(2024, 12, 31),
        "status": "Concluído",
    },
]

_PROJETOS = [
    # Programa MANSUP
    {
        "id": 1,
        "codigo_projeto": "MANSUP-001",
        "nome_projeto": "Conversor DC-DC Isolado",
        "programa_id": 1,
        "responsavel": "Bruno Ferreira",
        "custo_hora": 120.0,
        "data_inicio": date(2024, 2, 1),
        "data_fim_prevista": date(2025, 2, 1),
        "status": "Em andamento",
    },
    {
        "id": 2,
        "codigo_projeto": "MANSUP-002",
        "nome_projeto": "Sistema de Controle PID",
        "programa_id": 1,
        "responsavel": "Camila Torres",
        "custo_hora": 95.0,
        "data_inicio": date(2024, 3, 15),
        "data_fim_prevista": date(2025, 3, 15),
        "status": "Em andamento",
    },
    {
        "id": 3,
        "codigo_projeto": "MANSUP-003",
        "nome_projeto": "Plataforma de Telemetria",
        "programa_id": 1,
        "responsavel": "Diego Nunes",
        "custo_hora": 110.0,
        "data_inicio": date(2024, 4, 1),
        "data_fim_prevista": date(2024, 12, 31),
        "status": "Concluído",
    },
    # Programa MAX1.2AC
    {
        "id": 4,
        "codigo_projeto": "MAX-001",
        "nome_projeto": "Módulo de Potência AC",
        "programa_id": 2,
        "responsavel": "Elena Barbosa",
        "custo_hora": 130.0,
        "data_inicio": date(2024, 3, 1),
        "data_fim_prevista": date(2025, 9, 1),
        "status": "Em andamento",
    },
    {
        "id": 5,
        "codigo_projeto": "MAX-002",
        "nome_projeto": "Driver de Gate IGBT",
        "programa_id": 2,
        "responsavel": "Felipe Santos",
        "custo_hora": 115.0,
        "data_inicio": date(2024, 5, 1),
        "data_fim_prevista": date(2025, 5, 1),
        "status": "Em andamento",
    },
    {
        "id": 6,
        "codigo_projeto": "MAX-003",
        "nome_projeto": "Filtro EMI Ativo",
        "programa_id": 2,
        "responsavel": "Gisele Martins",
        "custo_hora": 100.0,
        "data_inicio": date(2024, 6, 1),
        "data_fim_prevista": date(2025, 6, 1),
        "status": "Em andamento",
    },
    # Programa INNOV3
    {
        "id": 7,
        "codigo_projeto": "INNOV3-001",
        "nome_projeto": "Sensor de Corrente Hall",
        "programa_id": 3,
        "responsavel": "Hugo Pereira",
        "custo_hora": 90.0,
        "data_inicio": date(2023, 6, 1),
        "data_fim_prevista": date(2024, 6, 1),
        "status": "Concluído",
    },
    {
        "id": 8,
        "codigo_projeto": "INNOV3-002",
        "nome_projeto": "PCB de Alta Frequência",
        "programa_id": 3,
        "responsavel": "Isabela Cruz",
        "custo_hora": 105.0,
        "data_inicio": date(2023, 8, 1),
        "data_fim_prevista": date(2024, 10, 31),
        "status": "Concluído",
    },
]

_FORNECEDORES = [
    {
        "id": 1,
        "codigo_fornecedor": "FORN-001",
        "razao_social": "Eletro Componentes Ltda",
        "cidade": "São Paulo",
        "estado": "SP",
        "categoria": "Eletrônicos",
        "status": "Ativo",
    },
    {
        "id": 2,
        "codigo_fornecedor": "FORN-002",
        "razao_social": "Semicondutores do Sul SA",
        "cidade": "Florianópolis",
        "estado": "SC",
        "categoria": "Semicondutores",
        "status": "Ativo",
    },
    {
        "id": 3,
        "codigo_fornecedor": "FORN-003",
        "razao_social": "Power Parts Brasil Ltda",
        "cidade": "Campinas",
        "estado": "SP",
        "categoria": "Componentes de Potência",
        "status": "Ativo",
    },
]

_TAREFAS = [
    {"id": 1, "codigo_tarefa": "T-001", "projeto_id": 1, "titulo": "Especificação técnica", "responsavel": "Bruno Ferreira", "estimativa_horas": 40, "data_inicio": date(2024, 2, 1), "data_fim_prevista": date(2024, 2, 15), "status": "Concluída"},
    {"id": 2, "codigo_tarefa": "T-002", "projeto_id": 1, "titulo": "Desenvolvimento do firmware", "responsavel": "Bruno Ferreira", "estimativa_horas": 120, "data_inicio": date(2024, 2, 16), "data_fim_prevista": date(2024, 5, 31), "status": "Em andamento"},
    {"id": 3, "codigo_tarefa": "T-003", "projeto_id": 2, "titulo": "Modelagem matemática", "responsavel": "Camila Torres", "estimativa_horas": 60, "data_inicio": date(2024, 3, 15), "data_fim_prevista": date(2024, 4, 30), "status": "Concluída"},
    {"id": 4, "codigo_tarefa": "T-004", "projeto_id": 2, "titulo": "Implementação algoritmo PID", "responsavel": "Camila Torres", "estimativa_horas": 80, "data_inicio": date(2024, 5, 1), "data_fim_prevista": date(2024, 8, 31), "status": "Em andamento"},
    {"id": 5, "codigo_tarefa": "T-005", "projeto_id": 4, "titulo": "Design do esquemático", "responsavel": "Elena Barbosa", "estimativa_horas": 50, "data_inicio": date(2024, 3, 1), "data_fim_prevista": date(2024, 4, 15), "status": "Concluída"},
    {"id": 6, "codigo_tarefa": "T-006", "projeto_id": 4, "titulo": "Testes de carga", "responsavel": "Elena Barbosa", "estimativa_horas": 90, "data_inicio": date(2024, 5, 1), "data_fim_prevista": date(2024, 9, 30), "status": "Em andamento"},
    {"id": 7, "codigo_tarefa": "T-007", "projeto_id": 5, "titulo": "Simulação SPICE", "responsavel": "Felipe Santos", "estimativa_horas": 40, "data_inicio": date(2024, 5, 1), "data_fim_prevista": date(2024, 6, 30), "status": "Concluída"},
    {"id": 8, "codigo_tarefa": "T-008", "projeto_id": 7, "titulo": "Calibração do sensor", "responsavel": "Hugo Pereira", "estimativa_horas": 30, "data_inicio": date(2023, 6, 1), "data_fim_prevista": date(2023, 8, 31), "status": "Concluída"},
]

_TEMPOS = [
    # Tarefa T-001
    {"id": 1,  "tarefa_id": 1, "usuario": "Bruno Ferreira",  "data": date(2024, 2, 5),  "horas_trabalhadas": 8.0},
    {"id": 2,  "tarefa_id": 1, "usuario": "Bruno Ferreira",  "data": date(2024, 2, 8),  "horas_trabalhadas": 8.0},
    {"id": 3,  "tarefa_id": 1, "usuario": "Bruno Ferreira",  "data": date(2024, 2, 12), "horas_trabalhadas": 6.0},
    # Tarefa T-002
    {"id": 4,  "tarefa_id": 2, "usuario": "Bruno Ferreira",  "data": date(2024, 3, 4),  "horas_trabalhadas": 8.0},
    {"id": 5,  "tarefa_id": 2, "usuario": "Bruno Ferreira",  "data": date(2024, 3, 11), "horas_trabalhadas": 8.0},
    {"id": 6,  "tarefa_id": 2, "usuario": "Bruno Ferreira",  "data": date(2024, 4, 2),  "horas_trabalhadas": 8.0},
    {"id": 7,  "tarefa_id": 2, "usuario": "Bruno Ferreira",  "data": date(2024, 5, 6),  "horas_trabalhadas": 8.0},
    # Tarefa T-003
    {"id": 8,  "tarefa_id": 3, "usuario": "Camila Torres",   "data": date(2024, 3, 18), "horas_trabalhadas": 8.0},
    {"id": 9,  "tarefa_id": 3, "usuario": "Camila Torres",   "data": date(2024, 4, 1),  "horas_trabalhadas": 8.0},
    # Tarefa T-004
    {"id": 10, "tarefa_id": 4, "usuario": "Camila Torres",   "data": date(2024, 5, 6),  "horas_trabalhadas": 8.0},
    {"id": 11, "tarefa_id": 4, "usuario": "Camila Torres",   "data": date(2024, 6, 3),  "horas_trabalhadas": 8.0},
    {"id": 12, "tarefa_id": 4, "usuario": "Camila Torres",   "data": date(2024, 7, 1),  "horas_trabalhadas": 8.0},
    # Tarefa T-005
    {"id": 13, "tarefa_id": 5, "usuario": "Elena Barbosa",   "data": date(2024, 3, 4),  "horas_trabalhadas": 8.0},
    {"id": 14, "tarefa_id": 5, "usuario": "Elena Barbosa",   "data": date(2024, 3, 11), "horas_trabalhadas": 8.0},
    # Tarefa T-006
    {"id": 15, "tarefa_id": 6, "usuario": "Elena Barbosa",   "data": date(2024, 5, 6),  "horas_trabalhadas": 8.0},
    {"id": 16, "tarefa_id": 6, "usuario": "Elena Barbosa",   "data": date(2024, 6, 3),  "horas_trabalhadas": 8.0},
    {"id": 17, "tarefa_id": 6, "usuario": "Elena Barbosa",   "data": date(2024, 7, 8),  "horas_trabalhadas": 8.0},
    {"id": 18, "tarefa_id": 6, "usuario": "Elena Barbosa",   "data": date(2024, 8, 5),  "horas_trabalhadas": 8.0},
    # Tarefa T-007
    {"id": 19, "tarefa_id": 7, "usuario": "Felipe Santos",   "data": date(2024, 5, 7),  "horas_trabalhadas": 8.0},
    {"id": 20, "tarefa_id": 7, "usuario": "Felipe Santos",   "data": date(2024, 6, 4),  "horas_trabalhadas": 8.0},
    # Tarefa T-008
    {"id": 21, "tarefa_id": 8, "usuario": "Hugo Pereira",    "data": date(2023, 6, 5),  "horas_trabalhadas": 8.0},
    {"id": 22, "tarefa_id": 8, "usuario": "Hugo Pereira",    "data": date(2023, 7, 3),  "horas_trabalhadas": 8.0},
]

_PEDIDOS_COMPRA = [
    {"id": 1, "numero_pedido": "PC-2024-001", "solicitacao_id": None, "fornecedor_id": 1, "data_pedido": date(2024, 2, 20), "data_previsao_entrega": date(2024, 3, 20), "valor_total": 45000.0, "status": "Recebido"},
    {"id": 2, "numero_pedido": "PC-2024-002", "solicitacao_id": None, "fornecedor_id": 2, "data_pedido": date(2024, 3, 10), "data_previsao_entrega": date(2024, 4, 10), "valor_total": 32000.0, "status": "Recebido"},
    {"id": 3, "numero_pedido": "PC-2024-003", "solicitacao_id": None, "fornecedor_id": 3, "data_pedido": date(2024, 4, 5), "data_previsao_entrega": date(2024, 5, 5), "valor_total": 78000.0, "status": "Em trânsito"},
    {"id": 4, "numero_pedido": "PC-2024-004", "solicitacao_id": None, "fornecedor_id": 1, "data_pedido": date(2024, 5, 15), "data_previsao_entrega": date(2024, 6, 15), "valor_total": 55000.0, "status": "Recebido"},
    {"id": 5, "numero_pedido": "PC-2024-005", "solicitacao_id": None, "fornecedor_id": 2, "data_pedido": date(2024, 6, 1), "data_previsao_entrega": date(2024, 7, 1), "valor_total": 29000.0, "status": "Recebido"},
    {"id": 6, "numero_pedido": "PC-2024-006", "solicitacao_id": None, "fornecedor_id": 3, "data_pedido": date(2024, 7, 10), "data_previsao_entrega": date(2024, 8, 10), "valor_total": 91000.0, "status": "Em processamento"},
    {"id": 7, "numero_pedido": "PC-2023-001", "solicitacao_id": None, "fornecedor_id": 1, "data_pedido": date(2023, 7, 1), "data_previsao_entrega": date(2023, 8, 1), "valor_total": 18000.0, "status": "Recebido"},
    {"id": 8, "numero_pedido": "PC-2023-002", "solicitacao_id": None, "fornecedor_id": 2, "data_pedido": date(2023, 9, 1), "data_previsao_entrega": date(2023, 10, 1), "valor_total": 22000.0, "status": "Recebido"},
]

_COMPRAS_PROJETO = [
    # MANSUP-001
    {"id": 1,  "pedido_compra_id": 1, "projeto_id": 1, "valor_alocado": 25000.0},
    {"id": 2,  "pedido_compra_id": 2, "projeto_id": 1, "valor_alocado": 18000.0},
    # MANSUP-002
    {"id": 3,  "pedido_compra_id": 1, "projeto_id": 2, "valor_alocado": 20000.0},
    {"id": 4,  "pedido_compra_id": 3, "projeto_id": 2, "valor_alocado": 35000.0},
    # MANSUP-003
    {"id": 5,  "pedido_compra_id": 2, "projeto_id": 3, "valor_alocado": 14000.0},
    # MAX-001
    {"id": 6,  "pedido_compra_id": 3, "projeto_id": 4, "valor_alocado": 43000.0},
    {"id": 7,  "pedido_compra_id": 4, "projeto_id": 4, "valor_alocado": 55000.0},
    # MAX-002
    {"id": 8,  "pedido_compra_id": 5, "projeto_id": 5, "valor_alocado": 29000.0},
    {"id": 9,  "pedido_compra_id": 6, "projeto_id": 5, "valor_alocado": 41000.0},
    # MAX-003
    {"id": 10, "pedido_compra_id": 6, "projeto_id": 6, "valor_alocado": 50000.0},
    # INNOV3-001
    {"id": 11, "pedido_compra_id": 7, "projeto_id": 7, "valor_alocado": 18000.0},
    # INNOV3-002
    {"id": 12, "pedido_compra_id": 8, "projeto_id": 8, "valor_alocado": 22000.0},
]


def _seed_model(model_cls, records, now, label, stdout):
    count = 0
    for r in records:
        data = dict(r)
        data["silver_ingested_at"] = now
        _, created = model_cls.objects.get_or_create(id=data["id"], defaults=data)
        if created:
            count += 1
    stdout.write(f"  {count} {label} criado(s).")
    return count


def _import_models():
    from users.models import User
    from sca_data.models import (
        SilverPrograma,
        SilverProjeto,
        SilverFornecedor,
        SilverTarefaProjeto,
        SilverTempoTarefa,
        SilverPedidoCompra,
        SilverComprasProjeto,
    )
    return User, SilverPrograma, SilverProjeto, SilverFornecedor, SilverTarefaProjeto, SilverTempoTarefa, SilverPedidoCompra, SilverComprasProjeto


class Command(BaseCommand):
    help = "Popula o banco com dados de teste (apenas dev/staging, requer SEED_ENABLED=true)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove os dados de seed existentes antes de inserir",
        )

    def handle(self, *_args, **options):
        if os.environ.get("SEED_ENABLED", "").lower() != "true":
            raise CommandError(
                "Seed bloqueado em produção.\n"
                "Para rodar em dev/staging, defina SEED_ENABLED=true no .env"
            )

        models = _import_models()
        user_cls, prog_cls, proj_cls, forn_cls, tarefa_cls, tempo_cls, pedido_cls, compra_cls = models

        self.stdout.write("Iniciando seed de dados de desenvolvimento...")

        with transaction.atomic():
            if options["flush"]:
                self._flush(user_cls, prog_cls, proj_cls, forn_cls, tarefa_cls, tempo_cls, pedido_cls, compra_cls)

            created_users = self._seed_users(user_cls)
            now = timezone.now()

            counts = {
                "programa(s)":   _seed_model(prog_cls,   _PROGRAMAS,       now, "programa(s)",          self.stdout),
                "fornecedor(s)": _seed_model(forn_cls,   _FORNECEDORES,    now, "fornecedor(es)",       self.stdout),
                "projeto(s)":    _seed_model(proj_cls,   _PROJETOS,        now, "projeto(s)",           self.stdout),
                "tarefa(s)":     _seed_model(tarefa_cls, _TAREFAS,         now, "tarefa(s)",            self.stdout),
                "tempo(s)":      _seed_model(tempo_cls,  _TEMPOS,          now, "registro(s) de tempo", self.stdout),
                "pedido(s)":     _seed_model(pedido_cls, _PEDIDOS_COMPRA,  now, "pedido(s) de compra",  self.stdout),
                "compra(s)":     _seed_model(compra_cls, _COMPRAS_PROJETO, now, "alocação(ões)",        self.stdout),
            }

        summary = ", ".join(f"{v} {k}" for k, v in counts.items())
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeed concluído: {created_users} user(s), {summary}.\n"
                "LEMBRETE: estes dados são exclusivos para dev/staging."
            )
        )

    def _flush(self, user_cls, prog_cls, proj_cls, forn_cls, tarefa_cls, tempo_cls, pedido_cls, compra_cls):
        dev_usernames = [u["username"] for u in _DEV_USERS]
        deleted, _ = user_cls.objects.filter(username__in=dev_usernames).delete()
        self.stdout.write(f"  {deleted} usuário(s) de dev removidos.")
        compra_cls.objects.filter(id__in=[r["id"] for r in _COMPRAS_PROJETO]).delete()
        pedido_cls.objects.filter(id__in=[r["id"] for r in _PEDIDOS_COMPRA]).delete()
        tempo_cls.objects.filter(id__in=[r["id"] for r in _TEMPOS]).delete()
        tarefa_cls.objects.filter(id__in=[r["id"] for r in _TAREFAS]).delete()
        proj_cls.objects.filter(id__in=[r["id"] for r in _PROJETOS]).delete()
        forn_cls.objects.filter(id__in=[r["id"] for r in _FORNECEDORES]).delete()
        prog_cls.objects.filter(id__in=[r["id"] for r in _PROGRAMAS]).delete()
        self.stdout.write("  Dados Silver de dev removidos.")

    def _seed_users(self, user_cls):
        count = 0
        for u in _DEV_USERS:
            data = dict(u)
            data["password"] = make_password(data["password"])
            _, was_created = user_cls.objects.get_or_create(username=data["username"], defaults=data)
            if was_created:
                count += 1
                self.stdout.write(f"  Criado user: {data['username']}")
            else:
                self.stdout.write(f"  Já existe user: {data['username']} (ignorado)")
        return count
