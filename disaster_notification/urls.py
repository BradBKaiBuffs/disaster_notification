"""
URL configuration for disaster_notification project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from notification.views import upload_csv_view
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    path('dn_admin/', admin.site.urls),
    path('redis/', staff_member_required(include('dj_redis_panel.urls'))),
    path('', include('notification.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path("upload_csv", upload_csv_view, name="upload_csv"),
    path("forecasting/", include("forecasting.urls")),
]        
