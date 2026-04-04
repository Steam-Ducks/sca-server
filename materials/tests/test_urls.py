from django.urls import resolve, reverse

from materials.views import MaterialsTableView


def test_materials_table_url_resolve():
    url = reverse("materials-table")
    resolver = resolve(url)

    assert resolver.func.view_class == MaterialsTableView
