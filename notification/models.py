from django.db import models
from django.contrib.auth.models import User

# create your models here.
# NOAA alert API model
class NoaaAlert(models.Model):
    # stores an alert
    # uses the 'id' from the api properties as the primary key
    id = models.CharField(primary_key=True, max_length=255)
    area_desc = models.TextField()
    event = models.CharField(max_length=255)
    headline = models.TextField(null=True, blank=True)
    description = models.TextField()
    instruction = models.TextField(null=True, blank=True)

    # core response info
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

    # timestamps from the api
    sent = models.DateTimeField()
    effective = models.DateTimeField()
    onset = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    ends = models.DateTimeField(null=True, blank=True)

    # sender info
    sender_name = models.CharField(
        max_length=255,
        help_text="the name of the nws office that sent the alert.",
    )

    # json fields for nested or variable data
    geocode = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)

    def __str__(self):
        # simple readable label for admin and logs
        return f"{self.event} ({self.severity})"


# stores what area a user wants to follow for alerts
class UserAreaSubscription(models.Model):
    # holds the notification choices that the user can pick
    NOTIFY_CHOICES = [
        ("new", "Notify on new alert"),
        ("update", "Notify on update"),
        ("expires", "Notify before expiry"),
        ("all", "All notifications"),
    ]

    # links each subscription to a real user account
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # stores the area text
    area = models.CharField(max_length=255)

    # stores county
    # already had fields during tests so have to put in a default space to make it work
    county = models.CharField(max_length=255, default='')
    state = models.CharField(max_length=255, default='')

    # keeps the phone number for sending sms alerts later
    phone_number = models.CharField(max_length=20)

    # saves what notification type the user wants
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFY_CHOICES,
        default="new",
    )

    # timestamp when created
    created_at = models.DateTimeField(auto_now_add=True)

    # shows a readable label when looking at this model
    def __str__(self):
        return f"{self.user.username} -> {self.area}"


# tracks what alerts were already sent so it doesn't send the same one again
class AlertNotificationTracking(models.Model):
    # links to the user who got the alert
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # links to the noaa alert that was delivered
    alert = models.ForeignKey(NoaaAlert, on_delete=models.CASCADE)

    # saves the date and time the alert was sent out
    sent_at = models.DateTimeField(auto_now_add=True)

    # shows readable label when looking at the info
    def __str__(self):
        return f"{self.user.username} -> {self.alert.id}"


# storm events csv
class StormEvent(models.Model):
    # uses the event id from the csv as the primary key
    event_id = models.CharField(primary_key=True, max_length=50)

    # type of weather event
    event_type = models.CharField(max_length=100)

    # state and county where the event happened
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)

    # date and time
    begin_year = models.IntegerField(default=1)
    begin_month = models.IntegerField(default=1)
    end_year = models.IntegerField(default=1)
    end_month = models.IntegerField(default=1)
    begin_time = models.IntegerField(default=1)
    end_time = models.IntegerField(default=1)

    def __str__(self):
        # show event, state, and beginning year for the eye test
        return f"{self.event_type} in {self.state} ({self.begin_year})"