from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications, name='notifications'),
    path('dashboard/', views.dashboard, name='dashboard'),
]