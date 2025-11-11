from django.urls import path
from . import views, include

urlpatterns = [
    path('', views.notification, name='notification'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/', include('api.urls')),
]