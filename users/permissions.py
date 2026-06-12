from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission


def _get_permissao(user):
    try:
        return user.usuario_perfil.perfil.permissoes
    except Exception:
        return None


class _ProfilePermission(BasePermission):
    """Base class: checks authentication then validates profile membership."""

    allowed_profiles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        permissao = _get_permissao(request.user)
        if permissao is None:
            raise PermissionDenied("Perfil de usuário não encontrado. Acesso negado.")
        if permissao not in self.allowed_profiles:
            raise PermissionDenied(
                "Acesso negado. Seu perfil não tem permissão para acessar este recurso."
            )
        return True


class CanAccessUsers(_ProfilePermission):
    allowed_profiles = ["super_admin"]


class CanAccessDashboard(_ProfilePermission):
    allowed_profiles = ["super_admin", "financeiro", "projetos"]


class CanAccessBudget(_ProfilePermission):
    allowed_profiles = ["super_admin", "financeiro"]


class CanAccessCosts(_ProfilePermission):
    allowed_profiles = ["super_admin", "financeiro", "compras"]


class CanAccessMaterials(_ProfilePermission):
    allowed_profiles = [
        "super_admin",
        "financeiro",
        "compras",
        "almoxarifado",
        "projetos",
    ]


class CanAccessTechnicalHours(_ProfilePermission):
    allowed_profiles = ["super_admin", "financeiro", "projetos"]


class CanAccessAudit(_ProfilePermission):
    allowed_profiles = [
        "super_admin",
        "financeiro",
        "compras",
        "almoxarifado",
        "projetos",
    ]


class CanAccessConsolidated(_ProfilePermission):
    allowed_profiles = ["super_admin", "financeiro", "projetos"]


class CanAccessImports(_ProfilePermission):
    allowed_profiles = [
        "super_admin",
        "financeiro",
        "compras",
        "almoxarifado",
        "projetos",
    ]


class CanAccessMonitoring(_ProfilePermission):
    allowed_profiles = [
        "super_admin",
        "financeiro",
        "compras",
        "almoxarifado",
        "projetos",
    ]
