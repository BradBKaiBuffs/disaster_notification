# Disaster Notification system
## Overview
This project is an attempt to create a personalized notification system retrieved from the NOAA alert API. The system will allow users to subscribe to counties and will get notified of an alert.
This project is for my WTAMU MS-CISBA Capstone project which should integrate the coursework in the following areas: Software Systems, Business Analytics, Data Management and Networking & Cybersecurity.
## Key Features
### Real-Time NOAA Alerts through SMS and Email notifications
- Automated processing of NOAA's National Weather Service API
- Celery services run tasks based on statuses of alerts
### Prediction and Prescription Analytics
- Forecasting of events 30 days in events based on historical NOAA storm event records from 2015-2025
- Probability of disaster events like tornados, hail and flash floods
- Recommendations for preparing for disasters
### Web application experience
-	User registration and login
-	Subscription system
-	Dashboard displaying graphs and alerts
### Full stack architecture
-	Django Web Framework
-	Celery and Redis services
-	PostgreSQL cloud instance
-	Railway deployment
### Technology stack
- **Python 3.12+**
- **Django**
- **Celery**
- **Redis**
- **PostgreSQL**
- **Bootstrap**
- **Vonage SMS API**
- **NOAA NWS API**
- **Railway Cloud Hosting**

## How to install locally
Clone repository:
```bash
git clone https://github.com/bradbkaibuffs/disaster_notifications.git
cd disaster_notifications
```
Install dependencies:
```
pip install -r requirements.txt
```
Run migrations:
```
python manage.py migrate
```
Start dev server:
```
python manage.py runserver
```
Start celery worker (local):
```
celery -A disaster_notification worker --loglevel=info
```

## Data Sources
- NOAA Weather Alerts (live) https://api.weather.gov/alerts
- NOAA Storm Events Database (2015–2025) https://www.ncdc.noaa.gov/stormevents/
## About the Author
Brad Kai\
MS-CISBA Candidate\
West Texas A&M University\

Background is in Information Technology managing, configuring and administering enterprise technologies such as Azure, Intune, JAMF in non-profit, government and corporate organizations.
