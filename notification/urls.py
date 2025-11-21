from django.urls import path, include
from .views import dashboard_view, subscribe_view, user_alerts_view, delete_subscription_view, upload_csv_view, get_counties_for_state, test_email_view, test_sms_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('user_alerts/', user_alerts_view, name="user_alerts"),
    path('delete_subscription/<int:sub_id>/', delete_subscription_view, name='delete_subscription'),
    path("upload_csv/", upload_csv_view, name="upload_csv"),
    path("ajax/get-counties/", get_counties_for_state, name="get_counties"),
    path("test_email/", test_email_view, name="test_email"),
    path("test_sms/", test_sms_view, name="test_sms"),
]