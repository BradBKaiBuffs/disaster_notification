from django.urls import path
from forecasting.views import forecasting_view

urlpatterns = [
    path("", forecasting_view, name="forecasting"),
]