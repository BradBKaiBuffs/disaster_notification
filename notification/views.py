from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import noaa_alerts, user_area_subscription
from .forms import user_area_subscription_form, user_registration_form
from django.db.models import Count
import json

# view shows recent alerts and keeps out test ones
def dashboard(request):
    alerts = noaa_alerts.objects.exclude(event__icontains='test').order_by('-sent')

    # pulls filter text if the user typed something in the filter boxes
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    # checks if any filter is being used
    any_filter = area or severity or urgency

    # no filters applied just shows 5 most recent alerts
    if not any_filter:
        alerts = noaa_alerts.objects.exclude(event__icontains='test').order_by('-sent')[:5]
    else:

        # area filter
        if area:
            alerts = alerts.filter(area_desc__icontains=area)

        # severity filter
        if severity:
            alerts = alerts.filter(severity__iexact=severity)

        # urgency filter
        if urgency:
            alerts = alerts.filter(urgency__iexact=urgency)

    # sends the filtered alerts to the page
    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)

from .forms import user_area_subscription_form

# view lets a user create or update their alert subscription
def subscribe(request):
    # load areas
    areas = (
        noaa_alerts.objects
        .exclude(event__icontains="test")
        .values_list("area_desc", flat=True)
        .distinct()
        .order_by("area_desc")
    )

    # checks if user already logged in
    if request.user.is_authenticated:

        # handle form submit for extra subscription rows
        if request.method == "POST":
            sub_form = user_area_subscription_form(request.POST)

            # save subscription row tied to current user
            if sub_form.is_valid():
                subscription = sub_form.save(commit=False)
                subscription.user = request.user
                subscription.save()
                return redirect("subscribe")

        # show empty form when page first loads
        else:
            sub_form = user_area_subscription_form()

        areas = (
            noaa_alerts.objects
            .exclude(event__icontains="test")
            .values_list("area_desc", flat=True)
            .distinct()
            .order_by("area_desc")
        )
        areas_list = list(areas)

        return render(request, "notification/subscribe.html", {
            # account fields for new user
            "user_form": user_form,
            # alert settings fields
            "sub_form": sub_form,
            # area field
            "areas": areas,
        })

    if request.method == "POST":
        user_form = user_registration_form(request.POST)
        sub_form = user_area_subscription_form(request.POST)

        # both account and subscription must pass validation
        if user_form.is_valid() and sub_form.is_valid():
            # save user account first
            user = user_form.save()
            login(request, user)

            # now save subscription linked to new user
            subscription = sub_form.save(commit=False)
            subscription.user = user
            subscription.save()

            return redirect("subscribe")

    # first load for non logged visitor
    else:
        user_form = user_registration_form()
        sub_form = user_area_subscription_form()

    return render(
        request,
        "notification/subscribe.html",
        {   
            # account fields for new user
            "user_form": user_form,
            # alert settings fields
            "sub_form": sub_form,
            # area field
            "areas": areas,
        },
    )

def user_alerts(request):
    #  grabs all subscriptions that belong to the logged in user
    subscriptions = user_area_subscription.objects.filter(user=request.user)

    # gets the area choice from url query or uses first sub if none
    selected_area = request.GET.get("area", "").strip()
    if not selected_area and subscriptions.exists():
        selected_area = subscriptions.first().area

    # excludes test alert messages
    alerts = noaa_alerts.objects.exclude(event__icontains="test")

    # filters alerts if an area is selected
    if selected_area:
        alerts = alerts.filter(area_desc__icontains=selected_area)

    # sorts newest first and keeps table readable
    alerts = alerts.order_by("-sent")[:50]

    # creates severity counts so we can build the bar chart
    severity_counts = (
        alerts.values("severity")
        .annotate(count=Count("severity"))
        .order_by("-count")
    )

    # splits the severity data into two lists
    severity_labels = [item["severity"] for item in severity_counts]
    severity_values = [item["count"] for item in severity_counts]

    # handles the form when user adds new subscripton info
    if request.method == "POST":
        form = user_area_subscription_form(request.POST)

        # connects the saved sub to the correct user
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()

            # user back to the same page after saving
            return redirect("user_alerts")

    # loads an empty form if page is first loaded
    else:
        form = user_area_subscription_form()

    # builds all values
    context = {
        "form": form,
        "subscriptions": subscriptions,
        "alerts": alerts,
        "selected_area": selected_area,
        "severity_labels": json.dumps(severity_labels),
        "severity_values": json.dumps(severity_values),
    }

    return render(request, "notification/user_alerts.html", context)
