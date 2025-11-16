from django.shortcuts import render
from .models import noaa_alerts

# this view shows recent alerts and keeps out test ones
def dashboard(request):
    alerts = noaa_alerts.objects.exclude(event__icontains='test').order_by('-sent')

    # this pulls filter text if the user typed something in the filter boxes
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    # this checks if any filter is being used
    any_filter = area or severity or urgency

    # with no filters applied, just shows 5 most recent alerts
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

    # this sends the filtered alerts to the page
    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)

from .forms import user_area_subscription_form

# this view lets a user create or update their alert subscription
def subscribe(request):
    # this checks if form was submitted
    if request.method == "POST":
        form = user_area_subscription_form(request.POST)

        # this saves the form if everything looks ok
        if form.is_valid():
            form.save()
            # this redirects user back after save
            return render(request, "notification/subscribe_success.html")
    else:
        # this makes an empty form for user to fill
        form = user_area_subscription_form()

    # this sends the form to the html page
    return render(request, "notification/subscribe.html", {"form": form})
