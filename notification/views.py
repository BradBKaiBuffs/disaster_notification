from django.shortcuts import render
from .models import noaa_alerts
from django.utils.timezone import now

# Create your views here.
def dashboard(request):
    alerts = noaa_alerts.objects.filter(expires__gt=now())

    # Get filter parameters from GET request
    area = request.GET.get('area')
    severity = request.GET.get('severity')
    urgency = request.GET.get('urgency')

    if area:
        alerts = alerts.filter(area_desc__icontains=area)
    if severity:
        alerts = alerts.filter(severity__iexact=severity)
    if urgency:
        alerts = alerts.filter(urgency__iexact=urgency)

    alerts = alerts.order_by('-sent')  # newest first

    return render(request, 'dashboard.html', {'alerts': alerts})