from django.db import models
from django.contrib.auth.models import User

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

    from django.contrib.auth.models import User

# stores what area a user wants to follow for alerts
# these rows let the system know how to message each person
class user_area_subscription(models.Model):
    # holds the notification choices that the user can pick
    NOTIFY_CHOICES = [
        ('new', 'Notify on New Alert'),
        ('update', 'Notify on Update'),
        ('expires', 'Notify Before Expiry'),
        ('all', 'All notification options'),
    ]

    # links each subscription to a real user account
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # stores the area tex
    area = models.CharField(max_length=255)

    # keeps the phone number for sending sms alerts later
    phone_number = models.CharField(max_length=20)

    # saves what notification type the user wants
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFY_CHOICES,
        default='new'
    )
    # timestamp when created
    created_at = models.DateTimeField(auto_now_add=True)

    # shows a readable label when looking at this model
    def __str__(self):
        return f"{self.user.username} -> {self.area}"


# tracks what alerts were already sent so we wont send the same one again
class alert_notification_tracking(models.Model):
    # links to the user who got the alert
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # links to the noaa alert that was delivered
    alert = models.ForeignKey(noaa_alerts, on_delete=models.CASCADE)

    # saves the date and time the alert was sent out
    sent_at = models.DateTimeField(auto_now_add=True)

    # shows readable label when looking at the info
    def __str__(self):
        return f"{self.user.username} -> {self.alert.id}"

# storm events csv
class storm_event(models.Model):
    event_id = models.CharField(primary_key=True, max_length=50)
    event_type = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)
    # manually split fields through cleaning before imported
    begin_year = models.IntegerField()
    begin_month = models.IntegerField()
    end_year = models.IntegerField()
    end_month = models.IntegerField()

    def __str__(self):
        return f"{self.event_type} in {self.state} ({self.year})"