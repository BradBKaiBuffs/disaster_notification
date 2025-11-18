import requests
from celery import shared_task
from dateutil.parser import isoparse
from django.contrib.auth.models import User
from .models import NoaaAlert


"""
test if celery + django connection works
"""
@shared_task
def debug_task(user_id):
    try:
        user = User.objects.get(pk=user_id)
        print(f"username: {user.username}")
        return True
    except Exception as e:
        print(f"access failed: {e}")
        raise

# noaa alerts api endpoint
API_URL = "https://api.weather.gov/alerts/active"


# converts iso timestamp into python datetime object
def parse_noaa_datetime(dt_str):
    if dt_str:
        try:
            return isoparse(dt_str)
        except (ValueError, TypeError):
            return None
    return None

@shared_task
def grab_noaa_alerts_task():
    try:
        headers = {
            # required by noaa for contact
            "User-Agent": "(disaster_notification, bkai1@buffs.wtamu.edu)"
        }

        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        alerts_processed = 0
        alerts_created = 0

        for feature in features:

            props = feature.get("properties", {})
            alert_id = props.get("id")

            # skip if alert has no id
            if not alert_id:
                continue

            # update fields for the model
            defaults_for_model = {
                "geometry": feature.get("geometry") or {},
                "area_desc": props.get("areaDesc", ""),
                "geocode": props.get("geocode", {}),
                "affected_zones": props.get("affectedZones", []),

                # convert time strings to datetime objects
                "sent": parse_noaa_datetime(props.get("sent")),
                "effective": parse_noaa_datetime(props.get("effective")),
                "onset": parse_noaa_datetime(props.get("onset")),
                "expires": parse_noaa_datetime(props.get("expires")),
                "ends": parse_noaa_datetime(props.get("ends")),

                "status": props.get("status", ""),
                "message_type": props.get("messageType", ""),
                "category": props.get("category", ""),
                "severity": props.get("severity", ""),
                "certainty": props.get("certainty", ""),
                "urgency": props.get("urgency", ""),
                "event": props.get("event", ""),
                "sender_name": props.get("senderName", ""),

                "headline": props.get("headline") or "",
                "description": props.get("description") or "",
                "instruction": props.get("instruction") or "",
                "response": props.get("response") or "",
                "parameters": props.get("parameters", {}),
            }

            # updates existing alert or creates new one
            obj, created = NoaaAlert.objects.update_or_create(
                id=alert_id,
                defaults=defaults_for_model,
            )

            alerts_processed += 1
            if created:
                alerts_created += 1

        return f"processed={alerts_processed}, created={alerts_created}"

    except requests.RequestException as e:
        return f"network error: {e}"

    except Exception as e:
        return f"task error: {e}"
