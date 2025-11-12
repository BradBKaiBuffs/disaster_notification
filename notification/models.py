from django.db import models

# Create your models here.
class noaa_alerts(models.Model):
    # stores an alert
    # use the 'id' from the API properties as the primary key
    id = models.CharField(primary_key=True, max_length=255)
    area_desc = models.TextField()
    event = models.CharField(max_length=255)
    headline = models.TextField(null=True, blank=True)
    description = models.TextField()
    instruction = models.TextField(null=True, blank=True)

    response = models.CharField(max_length=50, null=True, blank=True)
    affected_zones = models.JSONField(default=list)
    geometry = models.JSONField(default=dict, null=True, blank=True)

    # message info
    status = models.CharField(max_length=50)
    message_type = models.CharField(max_length=50)
    
    # categories
    category = models.CharField(max_length=50)
    severity = models.CharField(max_length=50)
    certainty = models.CharField(max_length=50)
    urgency = models.CharField(max_length=50)
    
    # Timestamps (from API)
    sent = models.DateTimeField()
    effective = models.DateTimeField()
    onset = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    ends = models.DateTimeField(null=True, blank=True)

    # sender Info
    sender_name = models.CharField(
        max_length=255, 
        help_text="The name of the NWS office that sent the alert."
    )
    
    # JSON Fields for nested/variable data
    geocode = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)