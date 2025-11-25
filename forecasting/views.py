from django.shortcuts import render

def forecasting_view(request):
    return render(request, 'forecasting/forecasting.html', {
        "ready_link": "https://www.ready.gov/severe-weather",
    })