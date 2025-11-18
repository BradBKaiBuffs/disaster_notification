from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import NoaaAlert, UserAreaSubscription, AlertNotificationTracking, StormEvent


# shows important alert fields when browsing in the admin page
@admin.register(NoaaAlert)
class NoaaAlertAdmin(admin.ModelAdmin):

    # helps see the main info at a glance
    list_display = ("event", "severity", "sent", "sender_name", "status")

    # filter alerts to find something quicker
    list_filter = ("severity", "status", "event", "sender_name")

    # adds a search bar for looking up alert text fields
    search_fields = ("event", "headline", "description", "area_desc")


# handles subscriptions for each user
@admin.register(UserAreaSubscription)
class UserAreaSubscriptionAdmin(admin.ModelAdmin):

    # shows who is subscribed and to what area
    list_display = ("user", "area", "phone_number", "notification_type")

    # filter subs by type or user
    list_filter = ("notification_type", "user")


# keeps track of delivered alerts so we dont double send them
@admin.register(AlertNotificationTracking)
class AlertNotificationTrackingAdmin(admin.ModelAdmin):

    # shows who got what alert
    list_display = ("user", "alert", "sent_at")

    # helps filter entries by user
    list_filter = ("user",)


# allows uploading of csv for storm events
@admin.register(StormEvent)
class StormEventAdmin(ImportExportModelAdmin):
    # import-export already provides actions and tools
    pass
