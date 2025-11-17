from django.urls import path, include
from . import views
from .views import dashboard, subscribe, user_alerts, delete_subscription

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subscribe/', subscribe, name='subscribe'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('user_alerts/', views.user_alerts, name="user_alerts"),
    path('delete_subscription/<int:sub_id>/', delete_subscription, name='delete_subscription'),
]