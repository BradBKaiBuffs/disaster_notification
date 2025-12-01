from django.shortcuts import render
from django.utils.timezone import now
from notification.models import StormEvent
import datetime
import pandas as pd
import json

# grab the states
def grab_states():
    return (
        StormEvent.objects
        .values_list("state", flat=True)
        .distinct()
        .order_by("state")
    )

# grab the counties for the state
def grab_counties_for_state(state):
    return (
        StormEvent.objects
        .filter(state=state)
        .values_list("county", flat=True)
        .distinct()
        .order_by("county")
    )

# forecast the next 30 days from today
def forecast_30_days_out(state, county, event_type):

    today = datetime.date.today()
    next_month = (today.month % 12) + 1

    prediction_data = StormEvent.objects.filter(
        county__icontains=county,
        state__iexact=state,
        begin_month=next_month
    )

    # used for event type selection
    if event_type:
        prediction_data = prediction_data.filter(event_type=event_type)

    prediction_data = prediction_data.values("begin_year")
    df = pd.DataFrame(list(prediction_data))

    if df.empty:
        return 0.0

    average_events = len(df) / df["begin_year"].nunique()
    return round(average_events, 2)


def type_probability(state, county):
    """
    Computes the percentage chance for each disaster type
    based on how many years that type occurred in the next month.
    """
    today = datetime.date.today()
    next_month = (today.month % 12) + 1

    qs = (
        StormEvent.objects
        .filter(
            state__iexact=state,
            county__icontains=county,
            begin_month=next_month
        )
        .values("event_type", "begin_year")
    )

    df = pd.DataFrame(list(qs))
    if df.empty:
        return []

    total_years = df["begin_year"].nunique()

    # Count number of years in which each event type occurred
    type_years = (
        df.groupby("event_type")["begin_year"]
        .nunique()
        .reset_index(name="years_with_events")
    )

    # Convert to % chance
    type_years["probability"] = (
        type_years["years_with_events"] / total_years * 100
    ).round(1)

    return type_years.to_dict("records")


def classify_disaster_chance(average_events):
    if average_events <= 3:
        return "Low chance"
    elif average_events <= 7:
        return "Moderate chance"
    else:
        return "High chance"


def prescription(chance):
    if chance == "High chance":
        return (
            "Prepare an emergency kit, secure outdoor items, and "
            "monitor weather alerts closely. Check Ready.gov for guidance on specific disasters."
        )
    elif chance == "Moderate chance":
        return (
            "Review your disaster event plans, check supplies, "
            "and stay aware of changing conditions. Check Ready.gov for guidance on specific disasters."
        )
    else:
        return (
            "Maintain general readiness. Check Ready.gov for guidance on specific disasters."
        )

# forecasting view that has state and county drop downs for forecasting
def forecasting_view(request):

    states = list(grab_states())
    selected_state = request.GET.get("state", states[0])

    county_map = {s: list(grab_counties_for_state(s)) for s in states}
    counties = county_map[selected_state]
    selected_county = request.GET.get("county", counties[0])

    event_types = (
        StormEvent.objects
        .values_list("event_type", flat=True)
        .distinct()
        .order_by("event_type")
    )
    selected_event_type = request.GET.get("event_type", "").strip()

    year = now().year
    month = now().month

    recent_queryset = StormEvent.objects.filter(
        state__iexact=selected_state,
        county__icontains=selected_county,
        begin_year=year,
        begin_month=month
    )

    if selected_event_type:
        recent_queryset = recent_queryset.filter(event_type=selected_event_type)

    recent_events = recent_queryset.count()

    # forecast
    forecast_events = forecast_30_days_out(
        selected_state,
        selected_county,
        selected_event_type
    )

    # prediction
    chance = classify_disaster_chance(forecast_events)
    
    # prescription
    advice = prescription(chance)

    type_probabilities = type_probability(
    selected_state,
    selected_county
    )

    return render(request, "forecasting/forecasting.html", {
        "states": states,
        "county_map_json": json.dumps(county_map),
        "counties": counties,
        "selected_state": selected_state,
        "selected_county": selected_county,
        "event_types": event_types,
        "selected_event_type": selected_event_type,
        "recent_events": recent_events,
        "forecast_events": forecast_events,
        "chance": chance,
        "advice": advice,
        "type_probabilities": type_probabilities,
        "ready_link": "https://www.ready.gov/severe-weather",
    })