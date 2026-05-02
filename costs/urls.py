from django.urls import path
from costs.views import GoldCostsTableView

urlpatterns = [
    path("costs/", GoldCostsTableView.as_view(), name="costs"),
]
