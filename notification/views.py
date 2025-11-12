from django.shortcuts import render
from .models import noaa_alerts
from django.utils.timezone import now

# Create your views here.
def notification(request):
    return render(request, "homepage.html")

def dashboard(request):
    # Display all active NOAA alerts
    active_alerts = noaa_alerts.objects.filter(
        expires__gt=now()
    ).order_by('-sent')  # newest first

    context = {
        'alerts': active_alerts
    }
    return render(request, 'dashboard.html', context)