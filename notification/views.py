from django.shortcuts import render
from .models import noaa_alerts
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    alerts = noaa_alerts.objects.all()

    # Optional: filter by GET parameters
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    if area:
        alerts = alerts.filter(area_desc__icontains=area)
    if severity:
        alerts = alerts.filter(severity__iexact=severity)
    if urgency:
        alerts = alerts.filter(urgency__iexact=urgency)

    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)