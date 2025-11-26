from django.urls import path, include
from notification.views import dashboard_view, subscribe_view, user_alerts_view, delete_subscription_view, upload_csv_view, grab_counties_for_state, test_email_view, test_sms_view, test_alert_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('user_alerts/', user_alerts_view, name="user_alerts"),
    path('delete_subscription/<int:sub_id>/', delete_subscription_view, name='delete_subscription'),
    # not being used anymore
    path("upload_csv/", upload_csv_view, name="upload_csv"),
    path("ajax/get-counties/", grab_counties_for_state, name="grab_counties"),
    # test groups
    path("test_email/", test_email_view, name="test_email"),
    path("test_sms/", test_sms_view, name="test_sms"),
    path("test_alert/", test_alert_view, name="test_alert"),
]