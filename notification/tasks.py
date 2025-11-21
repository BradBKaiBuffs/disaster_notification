# import requests calls the api and get json data
import requests
# shared_task for celery tasks
from celery import shared_task
# isoparse so iso date strings turn into datetime objects
from dateutil.parser import isoparse
# importing the User model from django auth system for the debug task
from django.contrib.auth.models import User
from .models import NoaaAlert


# noaa api url for active alerts
API_URL = "https://api.weather.gov/alerts/active"


# turns iso formatted date text into datetime
def parse_noaa_datetime(dt_str):
    # check if string exists
    if dt_str:
        try:
            return isoparse(dt_str)
        except (ValueError, TypeError):
            # return none because datetime could not be parsed
            return None
    # return none if dt_str was empty or none
    return None


# celery task that grabs alerts from noaa
@shared_task
def grab_noaa_alerts_task():
    try:
        # noaa wants to know contact information for whoever pulls their data
        headers = {
            "User-Agent": "(disaster_notification, bkai1@buffs.wtamu.edu)"
        }

        # makes the api request to noaa with the user agent included
        response = requests.get(API_URL, headers=headers)

        # raises an error if the status code is not 200
        response.raise_for_status()

        # turn the json text into dictionary
        data = response.json()

        # grab the list of "features" which hold alert details
        features = data.get("features", [])

        # counters
        alerts_processed = 0
        alerts_created = 0

        # loop each alert
        for feature in features:

            # grab the properties dictionary with alert info
            prop = feature.get("properties", {})

            # every alert has an id which we use as primary key
            alert_id = prop.get("id")

            # skip if missing id
            if not alert_id:
                continue

            # build dictionary for updating or creating the NoaaAlert object
            defaults_for_model = {
                # geometry information or {} if missing
                "geometry": feature.get("geometry") or {},

                # area description text that includes cities
                "area_desc": prop.get("areaDesc", ""),

                # geocode information for county/state/etc
                "geocode": prop.get("geocode", {}),

                # zones affected by this disaster alert
                "affected_zones": prop.get("affectedZones", []),

                # converting timestamp text to datetime objects
                "sent": parse_noaa_datetime(prop.get("sent")),
                "effective": parse_noaa_datetime(prop.get("effective")),
                "onset": parse_noaa_datetime(prop.get("onset")),
                "expires": parse_noaa_datetime(prop.get("expires")),
                "ends": parse_noaa_datetime(prop.get("ends")),

                # message fields from noaa
                "status": prop.get("status", ""),
                "message_type": prop.get("messageType", ""),

                # these categories describe how bad or urgent the disaster alert is
                "category": prop.get("category", ""),
                "severity": prop.get("severity", ""),
                "certainty": prop.get("certainty", ""),
                "urgency": prop.get("urgency", ""),

                # event name like tornado warning, flood alert, etc
                "event": prop.get("event", ""),

                # sender name
                "sender_name": prop.get("senderName", ""),

                "headline": prop.get("headline") or "",
                "description": prop.get("description") or "",
                "instruction": prop.get("instruction") or "",
                "response": prop.get("response") or "",

                # parameters is a dictionary of extra values noaa sometimes includes
                "parameters": prop.get("parameters", {}),
            }

            # creates or updates the alert in database
            # update_or_create looks for id=alert_id and updates it
            # if not found it creates a new row
            obj, created = NoaaAlert.objects.update_or_create(
                id=alert_id,
                defaults=defaults_for_model,
            )

            # add one for each processed
            alerts_processed += 1

            # add one for each created
            if created:
                alerts_created += 1

        # return a summary message that celery can log
        return f"processed = {alerts_processed}, created = {alerts_created}"

    # network exception
    except requests.RequestException as e:
        return f"{e}"

    # catching any other exception inside entire task
    except Exception as e:
        return f"{e}"