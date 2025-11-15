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

class user_area_subscription(models.Model):
    NOTIFY_CHOICES = [
        ('new', 'Notify on New Alert'),
        ('update', 'Notify on Update'),
        ('expires', 'Notify Before Expiry'),
        ('all', 'All notification options'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFY_CHOICES,
        default='new'
    )

    def __str__(self):
        return f"{self.user.username} -> {self.area}"


class alert_notification_tracking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(noaa_alerts, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.alert.id}"

# this model stores what area a user wants to follow for alerts
# these rows let the system know how to message each person
class user_area_subscription(models.Model):
    # this holds the notification choices that the user can pick
    NOTIFY_CHOICES = [
        ('new', 'Notify on New Alert'),
        ('update', 'Notify on Update'),
        ('expires', 'Notify Before Expiry'),
        ('all', 'All notification options'),
    ]

    # this links each subscription to a real user account
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # this stores the area text the user typed in
    area = models.CharField(max_length=255)

    # this keeps the phone number for sending sms alerts later
    phone_number = models.CharField(max_length=20)

    # this saves what notification type the user wants
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFY_CHOICES,
        default='new'
    )

    # this shows a readable label when looking at this model
    def __str__(self):
        return f"{self.user.username} -> {self.area}"


# this model tracks what alerts were already sent so we wont send the same one again
class alert_notification_tracking(models.Model):
    # this links to the user who got the alert
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # this links to the noaa alert that was delivered
    alert = models.ForeignKey(noaa_alerts, on_delete=models.CASCADE)

    # this saves the date and time the alert was sent out
    sent_at = models.DateTimeField(auto_now_add=True)

    # this helps the admin page show meaningful text
    def __str__(self):
        return f"{self.user.username} -> {self.alert.id}"
