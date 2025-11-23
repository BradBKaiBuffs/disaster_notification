# import requests calls the api and get json data
import requests
# shared_task for celery tasks
from celery import shared_task
# isoparse so iso date strings turn into datetime objects
from dateutil.parser import isoparse
# for sending email
from django.core.mail import send_mail
from .models import NoaaAlert, UserAreaSubscription, AlertNotificationTracking
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone


# noaa api url for active alerts
API_URL = "https://api.weather.gov/alerts/active"


# turns iso formatted date text into datetime used for the grab_noaa_alerts_task()
def parse_noaa_datetime(dt_str):
    # check if string exists
    if dt_str:
        try:
            return isoparse(dt_str)
        except (ValueError, TypeError):
            return None
    return None


# celery task that grabs alerts from noaa
@shared_task
def grab_noaa_alerts_task():
    try:
        # noaa wants to know contact information for whoever pulls their data
        headers = {
            "User-Agent": "(disaster_notification, bkai1@buffs.wtamu.edu)"
        }

        response = requests.get(API_URL, headers=headers)

        # raises an error
        response.raise_for_status()

        # turn the json text into a dictionary
        data = response.json()

        # grab the list of features which hold alert details
        features = data.get("features", [])

        # counters so I know how many were created or processed with each task job
        alerts_processed = 0
        alerts_created = 0

        for feature in features:

            # grab the properties
            prop = feature.get("properties", {})

            # every alert appears to have a long unique id which is used as a primary key
            alert_id = prop.get("id")

            # skip if missing id
            if not alert_id:
                continue

            # dictionary for updating or creating the NoaaAlert object
            defaults_for_model = {
                # for the below added "" or {} in case data is missing as I decided to pull all entries 
                "geometry": feature.get("geometry") or {},
                "area_desc": prop.get("areaDesc", ""),
                "geocode": prop.get("geocode", {}),
                "affected_zones": prop.get("affectedZones", []),

                # converting timestamp text to datetime objects
                "sent": parse_noaa_datetime(prop.get("sent")),
                "effective": parse_noaa_datetime(prop.get("effective")),
                "onset": parse_noaa_datetime(prop.get("onset")),
                "expires": parse_noaa_datetime(prop.get("expires")),
                "ends": parse_noaa_datetime(prop.get("ends")),

                "status": prop.get("status", ""),
                "message_type": prop.get("messageType", ""),
                "category": prop.get("category", ""),
                "severity": prop.get("severity", ""),
                "certainty": prop.get("certainty", ""),
                "urgency": prop.get("urgency", ""),
                "event": prop.get("event", ""),
                "sender_name": prop.get("senderName", ""),
                "headline": prop.get("headline") or "",
                "description": prop.get("description") or "",
                "instruction": prop.get("instruction") or "",
                "response": prop.get("response") or "",
                "parameters": prop.get("parameters", {}),
            }

            # creates or updates the alert in database
            # update_or_create looks for id=alert_id and updates it and if not found it creates a new row
            obj, created = NoaaAlert.objects.update_or_create(
                id=alert_id,
                defaults=defaults_for_model,
            )

            if created:
                notify_users_task(obj, "new")
            else:
                notify_users_task(obj, "update")

            alerts_processed += 1

            if created:
                alerts_created += 1

        return f"Processed = {alerts_processed}, Created = {alerts_created}"

    # network exception
    except requests.RequestException as e:
        return f"{e}"

    except Exception as e:
        return f"{e}"


# testing for now
# will use this for emailing
@shared_task(bind=True)
def send_email_task(self, subject, message, to_email):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False
        )
        return f"Sent to {to_email}"
    except Exception as e:
        return f"Sent failed: {e}"
    
# carriers to be used for task
CARRIER_GATEWAYS = {
    "att": "txt.att.net",
    "Verizon": "vtext.com",
    "T-Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com",
    "Boost": "myboostmobile.com",
    "Cricket": "sms.cricketwireless.net",
    "GoogleFi": "msg.fi.google.com",
    "US Mobile": "tmomail.net"
}

# sends SMS messages using gmail
@shared_task
def send_sms_task(to_number, carrier, message):
    # check the carrier table
    if carrier not in CARRIER_GATEWAYS:
        return "Carrier not found"
    
    gateway = CARRIER_GATEWAYS[carrier]

    # create the email address that will be used to send via gmail
    sms_email = f"{to_number}@{gateway}"

    try:
        send_mail(
            subject="",
            message=message,
            from_email=None,
            recipient_list=[sms_email],
            fail_silently=False
        )
        return "Sent SMS"
    except Exception as e:
        return f"Failed: {str(e)}"
    
# message task for the alert messages for text and email
def alert_message_task(alert):
    return (
        f"Alert Type: {alert.event}\n"
        f"Area: {alert.area_desc}\n\n"
        f"Description:\n{alert.description}\n\n"
        f"Instructions:\n{alert.instruction}\n\n"
        f"Status: {alert.status}\n"
        f"Severity: {alert.severity}\n"
        f"Certainty: {alert.certainty}\n"
        f"Urgency: {alert.urgency}\n\n"
        f"Sent: {alert.sent}\n"
        f"Effective: {alert.effective}\n"
        f"Onset: {alert.onset}\n"
        f"Expires: {alert.expires}\n"
    )

# task checks for all user subscriptions for alerts and sends out messages
def notify_users_task(alert, alert_kind):
    message = alert_message_task(alert)

    subs = UserAreaSubscription.objects.all()

    # for testing, pushes a test alert to all
    testing = "test" in alert.event.lower()

    for sub in subs:

        if not testing:

            if sub.area.lower() not in alert.area_desc.lower():
                continue

            if sub.notification_type != "all" and sub.notification_type != alert_kind:
                continue

        if AlertNotificationTracking.objects.filter(user=sub.user, alert=alert).exists():
            continue
        
        if sub.user.email:
            try:
                send_mail(
                    f"{alert.event} Alert",
                    message,
                    settings.EMAIL_HOST_USER,
                    [sub.user.email],
                    fail_silently=True
                )
            except:
                pass

        # send sms if user entered carrier
        if sub.phone_number and sub.carrier:
            email_gateway = f"{sub.phone_number}@{sub.carrier}"
            try:
                send_mail(
                    "",  # subject not needed for sms
                    message,
                    settings.EMAIL_HOST_USER,
                    [email_gateway],
                    fail_silently=True
                )
            except:
                pass

        # store tracking so user does not get duplicate alerts
        AlertNotificationTracking.objects.create(
            user=sub.user,
            alert=alert
        )

# checks for alerts that are close to expiration and notifies users
@shared_task
def expiring_alerts_task():

    now = timezone.now()

    # cutoff for the window of alerts that expire within the next 30 minutes
    cutoff = now + timedelta(minutes=30)

    # grabs all that have not expired yet
    expiring = NoaaAlert.objects.filter(
        expires__isnull=False,
        expires__gt=now,
        expires__lte=cutoff
    )

    for alert in expiring:
        notify_users_task(alert, "expires")

    return f"{expiring.count()} alerts for expiration"