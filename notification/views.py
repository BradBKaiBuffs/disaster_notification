from django.shortcuts import render

# Create your views here.
def transit(request):
    return render(request, "homepage.html")

def dashboard(request):
    return render(request, "dashboard.html")