from django.urls import path, include
from . import views
from .views import dashboard, subscribe

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path("subscribe/", subscribe, name="subscribe"),
    path('accounts/', include('django.contrib.auth.urls')),
]