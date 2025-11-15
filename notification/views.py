from django.shortcuts import render
from .models import noaa_alerts

# this view shows recent alerts and keeps out test ones
def dashboard(request):
    alerts = noaa_alerts.objects.exclude(event__icontains='test').order_by('-sent')

    # this pulls filter text if the user typed something in the filter boxes
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    # this filters by area match and ignores case
    if area:
        alerts = alerts.filter(area_desc__icontains=area)

    # this filters by severity if the user selected one
    if severity:
        alerts = alerts.filter(severity__iexact=severity)

    # this filters by urgency when picked
    if urgency:
        alerts = alerts.filter(urgency__iexact=urgency)

    # this sends the filtered alerts to the page
    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)
