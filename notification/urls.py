from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification, name='notification'),
    path('dashboard/', views.dashboard, name='dashboard'),
]