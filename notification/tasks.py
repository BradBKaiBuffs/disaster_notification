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
        
        data = response.json()
        # using API structure naming convention and creating a dictionary for model
        features = data.get('features', [])

        alerts_processed = 0
        alerts_created = 0
        
        for feature in features:
            property = feature.get('properties', {})
            alert_id = property.get('id')

            if not alert_id:
                continue
            defaults_for_model = {
                    'geometry': feature.get('geometry'),
                    'area_desc': property.get('areaDesc', ''),
                    'geocode': property.get('geocode', {}),
                    'affected_zones': property.get('affectedZones', []),
                    'sent': sort_datetime(property.get('sent')),
                    'effective': sort_datetime(property.get('effective')),
                    'onset': sort_datetime(property.get('onset')),
                    'expires': sort_datetime(property.get('expires')),
                    'ends': sort_datetime(property.get('ends')),
                    'status': property.get('status', ''),
                    'message_type': property.get('messageType', ''),
                    'category': property.get('category', ''),
                    'severity': property.get('severity', ''),
                    'certainty': property.get('certainty', ''),
                    'urgency': property.get('urgency', ''),
                    'event': property.get('event', ''),
                    'sender_name': property.get('senderName', ''),
                    'headline': property.get('headline', ''),
                    'description': property.get('description', ''),
                    'instruction': property.get('instruction', ''),
                    'response': property.get('response', ''),
                    'parameters': property.get('parameters', {}),
                }
            
            # prevent duplicate entries
            obj, created = noaa_alerts.objects.update_or_create(
                id=alert_id,
                default=defaults_for_model
            )

            alerts_processed += 1
            if created:
                alerts_created += 1
            
            # message for logs
            return f"Processed: {alerts_processed}, Created: {alerts_created}"

    # message to tell me if a failure happens
    except requests.RequestException as e:
        return f"Error in data handling: {e}"
    except Exception as e:
        return f"Error occurred: {e}"