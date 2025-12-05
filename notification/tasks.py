# import requests calls the api and get json data
import requests
# shared_task for celery tasks
from celery import shared_task
# isoparse so iso date strings turn into datetime objects
from dateutil.parser import isoparse
# for sending email
from django.core.mail import send_mail
from notification.models import NoaaAlert, UserAreaSubscription, AlertNotificationTracking
from django.conf import settings
from datetime import timedelta
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
    # debug since worker showing an issue with updated task
    print("TESTING")
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

            email_body, sms_body = combined_alert_summary([obj])

            if created:
                notify_users_task(obj, "new", email_body=email_body, sms_body=sms_body)
            else:
                notify_users_task(obj, "update", email_body=email_body, sms_body=sms_body)

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

# ran into a situation where sms was getting cut off so for now just giving a status update and link to site but no longer used but netwrok times out in Railway
# sends SMS messages using gmail
# @shared_task
# def send_sms_task(phone_number, carrier_domain, alert_kind):

#     notify_label = alert_kind.capitalize()
#     site_link = "disasternotification-production.up.railway.app"
#     sms_message = (
#         f"You have a {notify_label} notification from your subscription. See details here: {site_link}"
#     )

#     # debugging
#     print("notify_label", alert_kind)
#     print("sms_message", sms_message)

#     # create the email address that will be used to send via gmail
#     sms_email = f"{phone_number}@{carrier_domain}"

#     # debugging
#     print("phone_number", phone_number)
#     print("carrier domain", carrier_domain)

#     try:
#         send_mail(
#             # subject is not needed for sms
#             subject="",
#             message=sms_message,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[sms_email],
#             fail_silently=False
#         )
#         return "Sent SMS"
#     except Exception as e:
#         return f"Failed: {str(e)}"
    
   
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

# switched to vonage after being rejected by Twilio, failing to have reliability with gmail smtp to sms and this is needed by notify_users_task
def send_sms_vonage(to_number, text):

    # url to send text messages to
    url = "https://rest.nexmo.com/sms/json"

    # required fields by Vonage
    vonage_data = {
        "api_key": settings.VONAGE_API_KEY,
        "api_secret": settings.VONAGE_API_SECRET,
        "to": to_number,
        "from": settings.VONAGE_NUMBER,
        "text": text,
    }

    response = requests.post(url, data=vonage_data, timeout=10)

    result = response.json()

    # debugging
    #print("Vonage sms response:", result)

    return result

# after testing I found that Vonage requires the +1 for U.S. numbers so I have to factor this in
def format_phone_number(raw_number):
    
    digits = raw_number

    if digits.startswith("+1"):
        return "+" + digits
    
    if len(digits) == 10:
        return "+1" + digits
    
    return "+" + digits


def sub_alert_matching(alert, sub):

    from notification.views import grab_fips

    # use geocode same list from alert
    same_raw = alert.geocode.get("SAME", [])
    if not same_raw:
        return False

    # take the last five digits to match the fips code from storm event data
    alert_fips = []
    for code in same_raw:
        code_str = str(code).strip()
        alert_fips.append(code_str[-5:])

    user_fips = grab_fips(sub)
    if not user_fips:
        return False

    user_fips = str(user_fips).zfill(5)

    return user_fips in alert_fips

# due to the sheer amount of sms/emails one subscription and chug out, decided to combine alerts into a list that is sent in one sms/email per cycle if new active alert status exist
def notify_users_task(alerts, alert_kind, email_body=None, sms_body=None):

    # ran into a situation where work service doesn't like it when alert is not in a list so I'm just going to make everything a list
    from notification.models import NoaaAlert
    if isinstance(alerts, NoaaAlert):
        alerts = [alerts]

    subs = UserAreaSubscription.objects.all()
   
    # for testing, pushes a test alert to all also requires "test" in the message 
    testing = "test" in alerts[0].event.lower()

    # toggle to change testing, just going to comment out when testing
    if testing:
        print("Not testing")
        return

    for sub in subs:

        if not testing:

            # NOT USED ANYMORE
            # if sub.area.lower() not in alert.area_desc.lower():
                # continue

            # check for fips match
            if not sub_alert_matching(alerts[0], sub):
                continue

            if sub.notification_type.lower() != "all" and sub.notification_type.lower() != alert_kind:
                continue
        
        # check for alerts already sent
        already_sent = AlertNotificationTracking.objects.filter(
            user=sub.user,
            alert=alerts[0],
            alert_kind=alert_kind,
        ).exists()

        if already_sent:
            # debug
            # print("already_sent user", {sub.user.username})
            # print("alert and kind", {alerts[0].id}, {alert_kind})
            continue

        # for sms alert notifications
        if sub.phone_number:

            # go through the check to make sure the +1 exists
            to_number = format_phone_number(sub.phone_number)
            
            if sms_body:
                # debug
                # print("SMS user", {sub.user.username})
                # print("kind", {alert_kind})
                send_sms_vonage(to_number, sms_body)

        # for email alert notifications
        if sub.user.email and email_body:
                # debug
                # print("SMS user", {sub.user.username})
                # print("kind", {alert_kind})
                send_mail(
                    subject=f"Alerts ({len(alerts)})",
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[sub.user.email],
                    fail_silently=True
                )

        # track that alert was sent to user
        AlertNotificationTracking.objects.create(
            user=sub.user,
            alert=alerts[0],
            alert_kind=alert_kind,
            sent_at=timezone.now()
        )
        # debug
        # print("tracked user", {sub.user.username})
        # print("alert and kind", {alerts[0].id}, {alert_kind})

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
        email_body, sms_body = combined_alert_summary([alert])

        notify_users_task(
            alerts=[alert],
            alert_kind="expires",
            email_body=email_body,
            sms_body=sms_body,
        )

    return f"{expiring.count()} alerts for expiration"

# sends test alerts to a user by the admin
def send_test_alert_to_user_task(alert, user):

    # test sms 
    try:
        sub = UserAreaSubscription.objects.filter(user=user).first()
        if sub and sub.phone_number:
            send_sms_vonage(
                format_phone_number(sub.phone_number),
                "This is a test notification"
            )
            print("Test sms sent")
    except Exception as e:
        print("Test sms failed:", e)

    # test email
    try:
        if user.email:
            send_mail(
                subject="TEST ALERT",
                message="This is a test email alert",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )
            print("Test email sent")
    except Exception as e:
        print("Test email failed:", e)

# found that an county can easily push out dozens of alerts so this is to limit the amount of texts/emails sent
def combined_alert_summary(alerts, alert_kind):
    # debug
    # print("alerts_count", {len(alerts)})

    if not alerts:
        #
        # print("No active alerts")
        return("","")

    # different header for each alert kind status
    if alert_kind.lower() == "new":
        header = "New alert:\n\n"
        sms_header = "You have new alerts.\n"
    elif alert_kind.lower() == "update":
        header = "You have updated alerts:\n\n"
        sms_header = "You have updated alerts.\n"
    else:
        header = "Alert expiring:\n\n"
        sms_header = "You have an alert expiring.\n"

    email_body = header
    site_link = "https://disasternotification-production.up.railway.app/"

    # email + sms
    for alert in alerts:
        # debug
        # print("alert_id and event", {alert.id}, {alert.event})
        email_body += (
            "Event: " + alert.event + "\n"
            "Area: " + alert.area_desc + "\n"
            "Severity: " + alert.severity + "\n"
            "Expires: " + str(alert.expires) + "\n"
            "View here: " + site_link + "\n\n"
        )

    # sms will just show alert event due to character restrictions
    sms_body = (
        sms_header
        + "View here: " + site_link
    )

    # debug
    # print("email_body_length", len(email_body))
    # print("sms_body_length", len(sms_body))
    return (email_body, sms_body)

# with new subscriptions added to user page, this will activate and send the active alerts to the user via notify_users_task
def send_active_alerts_to_user_task(subscription):

    user = subscription.user
    now = timezone.now()
    alert_kind = "New"

    # grab all the active alerts
    active_alerts = (
        NoaaAlert.objects
        .filter(
            status__iexact="Actual",
            expires__gt=now,
        )
        .exclude(message_type__iexact="Cancel")
        .exclude(event__icontains="test")
    )

    # filter through the active alerts that fits the subscription made
    matching_alerts = []
    for alert in active_alerts:
        if sub_alert_matching(alert, subscription):
            matching_alerts.append(alert)
    
    # filter through the alerts that were already marked as sent
    new_alerts = []
    for alert in matching_alerts:
        already_sent = AlertNotificationTracking.objects.filter(
            user=user, 
            alert=alert, 
            alert_kind=alert_kind,
        ).exists()

        # debug
        # print("alert", {alert.id})
        # print("alredy_sent", {already_sent})

        if not already_sent:
            new_alerts.append(alert)

    # no new alerts means nothing gets sent
    if not new_alerts:
        # debug
        # print("no new alerts to send")
        return

    # mark the alerts as tracked
    for alert in new_alerts:
            AlertNotificationTracking.objects.create(
                user=user,
                alert=alert,
                alert_kind=alert_kind,
                sent_at=timezone.now(),
            )
            # debug
            # print("tracked_user", {user.username})
            # print("alert and kind", {alert.id}, {alert_kind})

    email_body, sms_body = combined_alert_summary(new_alerts)

    notify_users_task(
        alerts=new_alerts,
        alert_kind="new",
        email_body=email_body,
        sms_body=sms_body
    )
    print("notify_users_task called")