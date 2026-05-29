from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Perfil, User, UsuarioPerfil


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Informações adicionais", {"fields": ("name",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Informações adicionais", {"fields": ("name",)}),
    )


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["nome", "permissoes", "descricao"]


@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ["usuario", "perfil"]
