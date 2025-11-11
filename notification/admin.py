from django.contrib import admin
from .models import noaa_alerts

# Register your models here.
@admin.register(noaa_alerts)
class noaa_alert_admin(admin.ModelAdmin):
    list_display = ('event', 'severity', 'sent', 'sender_name', 'status')
    
    # filters for browsing ease
    list_filter = ('severity', 'status', 'event', 'sender_name')
    
    # search bar for ease
    search_fields = ('event', 'headline', 'description', 'area_desc')
