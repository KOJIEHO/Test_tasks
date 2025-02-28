from django.urls import path
from .views import CashMachineView

urlpatterns = [
    path('cash_machine/', CashMachineView.as_view(), name='cash_machine'),
]