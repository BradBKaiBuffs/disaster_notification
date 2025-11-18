from django.urls import path, include
from . import views
from .views import dashboard_view, subscribe_view, user_alerts_view, delete_subscription_view, upload_csv_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('user_alerts/', user_alerts_view, name="user_alerts"),
    path('delete_subscription/<int:sub_id>/', delete_subscription_view, name='delete_subscription'),
    path("upload_csv/", upload_csv_view, name="upload_csv"),
]