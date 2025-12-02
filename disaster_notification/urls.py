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

urlpatterns = [
    path('dn-admin/redis/', include('dj_redis_panel.urls')),
    path('dn-admin/', admin.site.urls),
    path('', include('notification.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path("upload_csv", upload_csv_view, name="upload_csv"),
    path("forecasting/", include("forecasting.urls")),
]        
