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
    response = models.CharField(max_length=50, null=True, blank=True)
    affected_zones = models.JSONField(default=list)
    geometry = models.JSONField(default=dict, null=True, blank=True)
    status = models.CharField(max_length=50)
    message_type = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    severity = models.CharField(max_length=50)
    certainty = models.CharField(max_length=50)
    urgency = models.CharField(max_length=50)
    sent = models.DateTimeField()
    effective = models.DateTimeField()
    onset = models.DateTimeField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    ends = models.DateTimeField(null=True, blank=True)
    sender_name = models.CharField(max_length=255)

    # json fields for nested or variable data
    geocode = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)

    def __str__(self):
        # simple readable label for admin and logs
        return f"{self.event} ({self.severity})"

# NOT USED FOR VONAGE
# CREATED ORIGINALLY FOR GMAIL/SENDGRID SMTP METHOD - will just be hidden from user view and default value will be ''
# CARRIER_NAMES = {
#     "vtext.com": "Verizon",
#     "txt.att.net": "AT&T",
#     "tmomail.net": "T-Mobile",
#     "messaging.sprintpcs.com": "Sprint",
#     "mms.uscc.net": "US Cellular",
#     "message.alltel.com": "AllTel",
# }

# stores what area a user wants to follow for alerts
class UserAreaSubscription(models.Model):
    # holds the notification choices that the user can pick
    NOTIFY_CHOICES = [
        ("New", "Notify on new alert"),
        ("Update", "Notify on update"),
        ("Expires", "Notify before expiration"),
        ("All", "All notifications"),
    ]

    # links each subscription to a real user account
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    area = models.CharField(max_length=255)

    # already had users in the database during tests so have to put in a default space for county and state to make it work
    county = models.CharField(max_length=255, default='')
    state = models.CharField(max_length=255, default='')

    phone_number = models.CharField(max_length=20)

    # similar situation with state and county so I had to put in default parameters
    # NOT USED FOR VONAGE
    # CREATED ORIGINALLY FOR GMAIL/SENDGRID SMTP METHOD - will just be hidden from user view and default value will be ''
    carrier = models.CharField(max_length=50, default='', blank=True)

    # pulled the value like vtext.com instead of Verizon on the Alert Subscriptions page
    # def carrier_label(self):
    #     return CARRIER_NAMES.get(self.carrier, self.carrier)

    # saves what notification type the user wants
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFY_CHOICES,
        default="New",
    )

    # timestamp when created
    created_at = models.DateTimeField(auto_now_add=True)

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

    # states the kind of alert like "new" or "expiring"
    alert_kind = models.CharField(max_length=20, default="New")

    def __str__(self):
        return f"{self.user.username} -> {self.alert.id}"


# storm events csv
class StormEvent(models.Model):
    # uses the event id from the csv as the primary key
    event_id = models.CharField(primary_key=True, max_length=50)
    event_type = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)
    begin_year = models.IntegerField(default=1)
    begin_month = models.IntegerField(default=1)
    end_year = models.IntegerField(default=1)
    end_month = models.IntegerField(default=1)
    begin_time = models.IntegerField(default=1)
    end_time = models.IntegerField(default=1)
    # added to address area_desc issue; fips will be able to match UGC data in noaaalerts
    county_fips = models.CharField(max_length=10, default='')
    state_fips = models.CharField(max_length=10, default='')

    def __str__(self):
        return f"{self.event_type} in {self.state} ({self.begin_year})"