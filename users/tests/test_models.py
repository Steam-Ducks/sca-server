import pytest

from users.models import Perfil, User, UsuarioPerfil


@pytest.mark.django_db
def test_user_str_returns_username():
    user = User.objects.create_user(
        username="maria", name="Maria", email="maria@email.com", password="senha123"
    )
    assert str(user) == "maria"


@pytest.mark.django_db
def test_user_password_is_hashed():
    user = User.objects.create_user(username="joao", password="senha123")
    assert user.password != "senha123"
    assert user.check_password("senha123")


@pytest.mark.django_db
def test_user_invalid_password_fails_check():
    user = User.objects.create_user(username="ana", password="correta")
    assert not user.check_password("errada")


@pytest.mark.django_db
def test_perfil_str_returns_nome():
    perfil, _ = Perfil.objects.get_or_create(
        nome="Financeiro",
        defaults={"descricao": "Acesso financeiro", "permissoes": "financeiro"},
    )
    assert str(perfil) == "Financeiro"


@pytest.mark.django_db
def test_perfil_nome_is_unique():
    Perfil.objects.get_or_create(
        nome="Compras", defaults={"descricao": "", "permissoes": "compras"}
    )
    with pytest.raises(Exception):
        Perfil.objects.create(nome="Compras", descricao="outro", permissoes="compras")


@pytest.mark.django_db
def test_usuario_perfil_str():
    user = User.objects.create_user(username="pedro", password="senha")
    perfil, _ = Perfil.objects.get_or_create(
        nome="Projetos",
        defaults={"descricao": "", "permissoes": "projetos"},
    )
    up = UsuarioPerfil.objects.create(usuario=user, perfil=perfil)
    assert str(up) == "pedro → Projetos"


@pytest.mark.django_db
def test_usuario_perfil_is_one_to_one():
    user = User.objects.create_user(username="lucas", password="senha")
    perfil, _ = Perfil.objects.get_or_create(
        nome="Almoxarifado",
        defaults={"descricao": "", "permissoes": "almoxarifado"},
    )
    UsuarioPerfil.objects.create(usuario=user, perfil=perfil)
    with pytest.raises(Exception):
        UsuarioPerfil.objects.create(usuario=user, perfil=perfil)
