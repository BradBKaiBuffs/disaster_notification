from django.contrib import admin
from .models import noaa_alerts, user_area_subscription, alert_notification_tracking

# this admin setup shows important alert fields when browsing in the admin page
@admin.register(noaa_alerts)
class noaa_alerts_admin(admin.ModelAdmin):
    # this helps see the main info at a glance
    list_display = ('event', 'severity', 'sent', 'sender_name', 'status')

    # this lets you filter alerts to find something quicker
    list_filter = ('severity', 'status', 'event', 'sender_name')

    # this adds a search bar for looking up alert text fields
    search_fields = ('event', 'headline', 'description', 'area_desc')


# this admin class handles subscriptions for each user
@admin.register(user_area_subscription)
class user_area_subscription_admin(admin.ModelAdmin):
    # this shows who is subscribed and to what area
    list_display = ('user', 'area', 'phone_number', 'notification_type')

    # this lets you filter subs by type or user
    list_filter = ('notification_type', 'user')


# this admin class keeps track of delivered alerts so we dont double send them
@admin.register(alert_notification_tracking)
class alert_notification_tracking_admin(admin.ModelAdmin):
    # this shows who got what alert
    list_display = ('user', 'alert', 'sent_at')

    # this helps filter entries by user
    list_filter = ('user',)