from django.urls import path, include
from . import views
from .views import dashboard, subscribe, user_alerts

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path("subscribe/", subscribe, name="subscribe"),
    path('alerts/', views.user_alerts, name='user_alerts'),
    path('accounts/', include('django.contrib.auth.urls')),
]