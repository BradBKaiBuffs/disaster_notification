import requests
from celery import shared_task
from dateutil.parser import isoparse
from .models import noaa_alerts
from django.contrib.auth.models import User

"""
Test if connections are working
"""
@shared_task
def debug(user_id):
    try:
        user = User.objects.get(pk=user_id)
        print(f" Username: {user.username}")
        return True
    except Exception as e:
        print(f"Access failed: {e}")
        raise

API_URL = "https://api.weather.gov/alerts/active"

def sort_datetime(dt_str):
    if dt_str:
        try:
            return isoparse(dt_str)
        except (ValueError, TypeError):
            return None
    return None

@shared_task
def grab_noaa_alerts():
    try:
        headers = {
            # Required by NOAA for contacting in event of anything
            'User-Agent': '(disaster_notification, bkai1@buffs.wtamu.edu)'
        }
        response = requests.get(API_URL, headers=headers)
        
        # check for bad response
        response.raise_for_status()

        data = response.json()
        # using API structure naming convention and creating a dictionary for model
        features = data.get('features', [])

        alerts_processed = 0
        alerts_created = 0
        
        for feature in features:
            props = feature.get('properties', {})
            alert_id = props.get('id')

            if not alert_id:
                continue
            defaults_for_model = {
                "geometry": feature.get("geometry") or {},
                "area_desc": props.get("areaDesc", ""),
                "geocode": props.get("geocode", {}),
                "affected_zones": props.get("affectedZones", []),
                "sent": sort_datetime(props.get("sent")),
                "effective": sort_datetime(props.get("effective")),
                "onset": sort_datetime(props.get("onset")),
                "expires": sort_datetime(props.get("expires")),
                "ends": sort_datetime(props.get("ends")),
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
            
            # prevent duplicate entries
            obj, created = noaa_alerts.objects.update_or_create(
                id=alert_id,
                defaults=defaults_for_model
            )

            alerts_processed += 1
            if created:
                alerts_created += 1
            
        # message for logs
        return f"Processed: {alerts_processed}, Created: {alerts_created}"

    # states if error happened
    except requests.RequestException as e:
        return f"Error in data handling: {e}"
    except Exception as e:
        return f"Error occurred: {e}"