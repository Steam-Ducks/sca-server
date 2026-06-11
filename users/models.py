from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    name = models.CharField(max_length=255, blank=True)

    REQUIRED_FIELDS = ["email", "name"]

    def __str__(self):
        return self.username


class Perfil(models.Model):
    class Permissao(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        FINANCEIRO = "financeiro", "Financeiro"
        COMPRAS = "compras", "Compras"
        ALMOXARIFADO = "almoxarifado", "Almoxarifado"
        PROJETOS = "projetos", "Projetos"

    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    permissoes = models.CharField(max_length=50, choices=Permissao.choices)

    def __str__(self):
        return self.nome


class UsuarioPerfil(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="usuario_perfil",
    )
    perfil = models.ForeignKey(
        Perfil,
        on_delete=models.PROTECT,
        related_name="usuarios",
    )

    def __str__(self):
        return f"{self.usuario.username} → {self.perfil.nome}"
