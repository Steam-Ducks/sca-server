from django.contrib.auth.hashers import make_password
from django.db import migrations

_PERFIS = [
    {
        "nome": "Super Admin",
        "descricao": "Acesso total ao sistema",
        "permissoes": "super_admin",
    },
    {
        "nome": "Financeiro",
        "descricao": "Acesso às informações financeiras e orçamento",
        "permissoes": "financeiro",
    },
    {
        "nome": "Compras",
        "descricao": "Acesso à gestão de materiais e compras",
        "permissoes": "compras",
    },
    {
        "nome": "Almoxarifado",
        "descricao": "Acesso ao controle de estoque e materiais",
        "permissoes": "almoxarifado",
    },
    {
        "nome": "Projetos",
        "descricao": "Acesso à gestão de projetos e horas técnicas",
        "permissoes": "projetos",
    },
]

_USUARIOS = [
    {
        "username": "superadmin",
        "name": "Super Admin",
        "email": "superadmin@sca.com",
        "password": "superadmin123",
        "is_staff": True,
        "is_superuser": True,
        "perfil": "Super Admin",
    },
    {
        "username": "financeiro",
        "name": "Usuário Financeiro",
        "email": "financeiro@sca.com",
        "password": "financeiro123",
        "is_staff": False,
        "is_superuser": False,
        "perfil": "Financeiro",
    },
    {
        "username": "compras",
        "name": "Usuário Compras",
        "email": "compras@sca.com",
        "password": "compras123",
        "is_staff": False,
        "is_superuser": False,
        "perfil": "Compras",
    },
    {
        "username": "almoxarifado",
        "name": "Usuário Almoxarifado",
        "email": "almoxarifado@sca.com",
        "password": "almoxarifado123",
        "is_staff": False,
        "is_superuser": False,
        "perfil": "Almoxarifado",
    },
    {
        "username": "projetos",
        "name": "Usuário Projetos",
        "email": "projetos@sca.com",
        "password": "projetos123",
        "is_staff": False,
        "is_superuser": False,
        "perfil": "Projetos",
    },
]


def seed(apps, schema_editor):
    User = apps.get_model("users", "User")
    Perfil = apps.get_model("users", "Perfil")
    UsuarioPerfil = apps.get_model("users", "UsuarioPerfil")

    perfis = {p["nome"]: Perfil.objects.create(**p) for p in _PERFIS}

    for u in _USUARIOS:
        data = dict(u)
        perfil_nome = data.pop("perfil")
        data["password"] = make_password(data["password"])
        user = User.objects.create(**data)
        UsuarioPerfil.objects.create(usuario=user, perfil=perfis[perfil_nome])


def unseed(apps, schema_editor):
    User = apps.get_model("users", "User")
    Perfil = apps.get_model("users", "Perfil")
    User.objects.filter(username__in=[u["username"] for u in _USUARIOS]).delete()
    Perfil.objects.filter(nome__in=[p["nome"] for p in _PERFIS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
