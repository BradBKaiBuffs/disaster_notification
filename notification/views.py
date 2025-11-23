# importing os because it is needed for file paths
import os
# importing json because need to load or dump json
import json
# import runs python commands or shell commands for running manage.py commands
import subprocess
# shows html pages or redirects you also has the get_object_or_404 thing that returns 404 automatically
from django.shortcuts import render, redirect, get_object_or_404
# log in the user after registering
from django.contrib.auth import login
# decorator makes a view only work when the user is logged in
from django.contrib.auth.decorators import login_required
# for showing messages at the top of page like success or warning
from django.contrib import messages
# using Count to annotate and count rows
from django.db.models import Count
from .models import NoaaAlert, UserAreaSubscription, StormEvent, AlertNotificationTracking
from .forms import UserAreaSubscriptionForm, UserRegistrationForm, CsvUploadForm
# sends a forbidden response when someone not allowed opens a page
from django.http import HttpResponseForbidden
# decorator so only staff can use upload page
from django.contrib.admin.views.decorators import staff_member_required
# import settings to use BASE_DIR for file paths
from django.conf import settings
# import plotly graph objects to build charts
import plotly.graph_objs as go
# plot function turns plotly chart into html to show on template
from plotly.offline import plot
# used to end json response to javascript
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .tasks import send_email_task, send_sms_task, notify_users_task
from django.utils import timezone
import uuid


# disaster events grouped by year
def grab_disaster_events_per_year():

    event_data = StormEvent.objects.values("begin_year")

    event_data = event_data.annotate(total=Count("event_id"))

    event_data = event_data.order_by("begin_year")

    return event_data

# create the raw grouped info for disaster heatmap
def grab_disaster_heatmap_data():

    # grabs begin year and begin month from StormEvent model and counts how many happened and groups by two fields
    calendar_data = (
        StormEvent.objects
        .values("begin_year", "begin_month")
        .annotate(total=Count("event_id"))
        .order_by("begin_year", "begin_month")
    )

    return calendar_data


# create a matrix for the heatmap chart used for the dashboard page
def create_heatmap_matrix():

    # grabs grouped data
    heatmap_data = grab_disaster_heatmap_data()

    years = []

    for h in heatmap_data:
        # only add if not already in list
        if h["begin_year"] not in years:
            years.append(h["begin_year"])

    years.sort()

    months = list(range(1, 13))

    # matrix
    m = []
    for _ in years:
        # making a row of zeros matching the 12 months
        empty_row = [0] * len(months)
        m.append(empty_row)

    # add matrix with data
    for row in heatmap_data:

        yr = row["begin_year"]
        mo = row["begin_month"]

        total = row["total"]

        yr_index = years.index(yr)

        mo_index = months.index(mo)

        # put the count number into that spot in matrix
        m[yr_index][mo_index] = total

    # send back the years, months, and matrix
    return years, months, m

# heatmap chart that uses the matrix from create_heatmap_matrix and turns it into a plotly heatmap
def heatmap_chart():

    years, months, h = create_heatmap_matrix()

    fig = go.Figure(
        data=go.Heatmap(
            z=h,
            x=months,
            y=years,
            colorscale="Viridis",
            colorbar=dict(title="Events"),
        )
    )

    fig.update_layout(
        title="Disaster Events Heatmap from 2015-2025 (Year vs Month)",
        xaxis=dict(
            title="Month",
        ),
        yaxis=dict(
            title="Year",
        ),
    )

    return plot(fig, output_type="div")


# main dashboard page view that displays charts when selecting a county/state
def dashboard_view(request):

    disaster_data = grab_disaster_events_per_year()

    years = []
    totals = []

    for d in disaster_data:
        years.append(d["begin_year"])
        totals.append(d["total"])

    # bar chart that is for disaster events per year
    fig1 = go.Figure(
        data=[
            go.Bar(
                x=years,
                y=totals
                )
            ],
        layout=go.Layout(
            title="Disaster Events Per Year (2015-2025)",
            yaxis=dict(
                title="Event Count",

                # max(totals) * 1.1 to get a figure above bars since it looks better like this than default
                range=[0, max(totals) * 1.1]
            )
        )
    )

    disaster_chart = plot(fig1, output_type="div")

    heatmap = heatmap_chart()

    # looks at event_type and counts how many for each one
    all_types = (
        StormEvent.objects
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )

    labels = []
    counts = []

    for t in all_types:
        labels.append(t["event_type"])
        counts.append(t["total"])

    # plotly bar char for disaster events by type
    fig_types = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=counts
                )
            ],
        layout=go.Layout(
            title="Disaster Events by Type (2015-2025)"
            ),
    )

    # max(totals) * 1.1 to get a figure above bars
    fig_types.update_yaxes(range=[0, max(totals) * 1.1])

    disaster_type_chart = plot(fig_types, output_type="div")

    # excludes test alerts since this provide little value
    alerts = NoaaAlert.objects.exclude(event__icontains='test')

    # area filter
    area = request.GET.get('area', '').strip()
    # severity filter
    severity = request.GET.get('severity', '').strip()
    # urgency filter
    urgency = request.GET.get('urgency', '').strip()

    # checks if at least one filter has some text
    any_filter = area or severity or urgency

    # if user put something in filters then filter alerts
    if any_filter:

        if area:
            alerts = alerts.filter(area_desc__icontains=area)

        # match exact severity
        if severity:
            alerts = alerts.filter(severity__iexact=severity)

        # match exact urgency
        if urgency:
            alerts = alerts.filter(urgency__iexact=urgency)

        # sort newest first and limit to 50 rows
        alerts = alerts.order_by('-sent')[:50]

    # no filters selected shows the last 5 alerts created
    else:
        alerts = alerts.order_by('-sent')[:5]

    context = {
        'heatmap': heatmap,
        'disaster_chart': disaster_chart,
        'disaster_type_chart': disaster_type_chart,
        'alerts': alerts
    }

    return render(request, 'notification/dashboard.html', context)

# grabs totals of disasters per year for a specific combination of county and state
def grab_county_yearly_data(state, county):

    st = state.lower().strip()

    ct = county.lower().strip()

    combined_data = (
        StormEvent.objects
        .filter(state__iexact=st, county__iexact=ct)
        .values("begin_year")
        .annotate(total=Count("event_id"))
        .order_by("begin_year")
    )

    return combined_data


# bar chart for the selected county over the span of the years 
def county_yearly_chart(state, county):

    yearly = grab_county_yearly_data(state, county)

    years = []
    totals = []

    for y in yearly:

        years.append(y["begin_year"])

        totals.append(y["total"])

    # bar chart using plotly
    fig = go.Figure(
        data=[
            go.Bar(
                x=years,
                y=totals,
                )
            ],
        layout=go.Layout(
            title=f"Disaster Events Per Year in {county}, {state} (2015 to 2025)",
            yaxis=dict(
                title="Count"
                )
        )
    )

    return plot(fig, output_type="div")


# grabs disaster event types and how many happened for each type
def grab_county_event_type_data(state, county):

    st = state.lower().strip()
    ct = county.lower().strip()

    # group by event_type and count how many for each type
    combined_data = (
        StormEvent.objects
        .filter(state__iexact=st, county__iexact=ct)
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )

    return combined_data


# bar chart for disaster types for when a user selects a county on user page
def county_event_type_chart(state, county):

  combined_type = grab_county_event_type_data(state, county)

  disaster_types = []
  disaster_totals = []

  for t in combined_type:
    disaster_types.append(t["event_type"])
    disaster_totals.append(t["total"])

  # use Plotly to create chart
  fig = go.Figure(
    data=[
        go.Bar(
            x=disaster_types, 
            y=disaster_totals,
            )
        ],
        layout=
            go.Layout(
                title=f"Disaster Event Types in {county}, {state} (2015 - 2025)"
            )
        )

  # turn the chart into html so it shows up on the webpage
  return plot(fig, output_type="div")


# returns a list of counties
def grab_counties_for_state(request):

    # grab state
    state = request.GET.get("state", "").strip()

    # find the county with the state
    counties = list(
        StormEvent.objects.filter(state__iexact=state)
        .values_list("county", flat=True)
        .distinct()
        .order_by("county")
    )

    # json response for javascript
    return JsonResponse({"counties": counties})


# view lets the user subscribe to alerts and also register new account if needed
def subscribe_view(request):

    # grabs a list of areas from noaa alerts that are not test alerts
    areas = (
        NoaaAlert.objects
        .exclude(event__icontains="test")
        .values_list("area_desc", flat=True)
        .distinct()
        .order_by("area_desc")
    )

    # grab list of all counties from StormEvent model
    counties = (
        StormEvent.objects
        .values_list("county", flat=True)
        .distinct()
        .order_by("county")
    )

    # grab list of all states
    states = (
        StormEvent.objects
        .values_list("state", flat=True)
        .distinct()
        .order_by("state")
    )

    # map where each state links to a list of counties
    county_map = {}

    # build state list for counties
    for s in states:
        # filter by each state and counties with no repeats
        county_map[s] = list(
            StormEvent.objects
            .filter(state=s)
            .values_list("county", flat=True)
            .distinct()
            .order_by("county")
        )

    # this reads notification type from POST if user selected one
    # grabs the value or empty string if nothing in POST
    selected_type = request.POST.get("notification_type", "")

    # check if the user already logged in
    # logged in users only see subscription form
    if request.user.is_authenticated:

        # if user submitted the form (POST request)
        if request.method == "POST":
            # create form instance with posted data
            sub_form = UserAreaSubscriptionForm(request.POST)

            # check subscription form is valid
            if sub_form.is_valid():

                # save the form but don't commit to db yet
                sub = sub_form.save(commit=False)

                # attach the logged in user to subscription
                sub.user = request.user

                # save the subscription
                sub.save()

                # redirect back to subscription page
                return redirect("subscribe")

        # if request is GET or other, show blank subscription form
        else:
            sub_form = UserAreaSubscriptionForm()

        # return the subscription page for logged in user
        return render(request, "notification/subscribe.html", {
            "areas": areas,
            "counties": counties,
            "states": states,
            "county_map": county_map,
            "county_map_json": json.dumps(county_map),
            "sub_form": sub_form,
            "selected_type": selected_type,
        })

    # a user not logged in can register amd pick a subscription at same time
    if request.method == "POST":

        # registration form
        user_form = UserRegistrationForm(request.POST)

        # subscription form
        sub_form = UserAreaSubscriptionForm(request.POST)

        # check both forms are valid
        if user_form.is_valid() and sub_form.is_valid():

            # save new user to database
            user = user_form.save()

            # log in the new user automatically after saving
            login(request, user)

            # create subscription object but not save yet
            sub = sub_form.save(commit=False)

            # connect the subscription to new user
            sub.user = user

            # save subscription
            sub.save()

            # redirect to subscribe page
            return redirect("subscribe")

    # if page is opened with GET, show blank forms for new registration
    else:
        user_form = UserRegistrationForm()
        sub_form = UserAreaSubscriptionForm()

    # render subscribe page with both forms for new users
    return render(request, "notification/subscribe.html", {
        "user_form": user_form,
        "sub_form": sub_form,
        "areas": areas,
        "counties": counties,
        "states": states,
        "county_map": county_map,
        "county_map_json": json.dumps(county_map),
        "selected_type": selected_type,
    })


# login is required because it is tied to user subscription
@login_required
# personalized user page view
def user_alerts_view(request):

    # grabs all subscriptions for the logged in user and is used for alerts and charts
    subscriptions = UserAreaSubscription.objects.filter(user=request.user)

    # pull active alerts that user subscribed to
    active_alerts = []

    all_alerts = NoaaAlert.objects.all()

    for alert in all_alerts:
        for sub in subscriptions:
            if sub.area.lower() in alert.area_desc.lower():
                active_alerts.append(alert)
                break

    # grab all the states from StormEvent model
    states = (
        StormEvent.objects
        .values_list("state", flat=True)
        .distinct()
        .order_by("state")
    )

    # create a county map for each state
    county_map = {}

    # go through every state for counties
    for s in states:
        county_map[s] = list(
            StormEvent.objects
            .filter(state=s)
            .values_list("county", flat=True)
            .distinct()
            .order_by("county")
        )

    selected_county = request.GET.get("county", "").strip()

    # if no county selected and user has subscriptions, then default to the first one
    if not selected_county and subscriptions.exists():
        selected_county = subscriptions.first().county

    # determine the state for the selected county
    # finds one matching row and grabs the state
    selected_state = None

    # find the state for the selected county
    if selected_county:
        # filter rows for that county paired with the first state found
        row = (
            StormEvent.objects
            .filter(county__iexact=selected_county)
            .values_list("state", flat=True)
            .first()
        )

        # update if nothing selected
        if row:
            selected_state = row

    # notification type if user posted a form
    selected_type = request.POST.get("notification_type", "")

    # if user submitted the form then creates a subscription form from POST data
    if request.method == "POST":
        form = UserAreaSubscriptionForm(request.POST)
        selected_type = request.POST.get("notification_type", "")

    else:
        form = UserAreaSubscriptionForm()
        selected_type = ""

    # creates the yearly chart using county_yearly_chart where both county and state must be chosen for chart to work
    yearly_chart = (
        county_yearly_chart(selected_state, selected_county)
        if selected_state and selected_county else None
    )

    type_chart = (
        county_event_type_chart(selected_state, selected_county)
        if selected_state and selected_county else None
    )

    return render(request, "notification/user_alerts.html", {
        "subscriptions": subscriptions,
        "selected_county": selected_county,
        "selected_state": selected_state,
        "county_yearly_chart": yearly_chart,
        "county_event_type_chart": type_chart,
        "states": states,
        "county_map": county_map,
        "county_map_json": json.dumps(county_map),
        "selected_type": selected_type,
        "form": form,
        "active_alerts": active_alerts,
    })


# this is tied to user subscriptions so have to be logged in
@login_required
# deletes user subscription row in alert user page 
def delete_subscription_view(request, sub_id):

    # grabs the subscription id
    sub = get_object_or_404(UserAreaSubscription, id=sub_id, user=request.user)

    # delete the subscription from the database
    sub.delete()

    # deletion message
    messages.warning(request, "Subscription removed.")

    return redirect("user_alerts")


# sets a folder path for uploaded files
UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploaded_files")

# make the directory if it does not exist
os.makedirs(UPLOAD_DIR, exist_ok=True)


# staff only csv upload
# I was going to initially use this as the primary method but files were too big
@staff_member_required
def upload_csv_view(request):

    if not request.user.is_staff:
        return HttpResponseForbidden("Only admin has access to this page.")

    message_sent = None

    if request.method == 'POST':

        form = CsvUploadForm(request.POST, request.FILES)

        if form.is_valid():

            # use the uploaded file
            upload_file = form.cleaned_data["file"]

            # create save path
            save_path = os.path.join(UPLOAD_DIR, upload_file.name)

            # open the file
            with open(save_path, "wb+") as destination:
                # write the file chunks one by one
                for chunk in upload_file.chunks():
                    destination.write(chunk)

            # call import_storms
            subprocess.Popen([
                "python", "manage.py", "import_storms", save_path
            ])

            message_sent = "Your file was uploaded"

    # GET request shows empty form
    else:
        form = CsvUploadForm()
        
    return render(request, "notification/upload_csv.html", {
        "form": form,
        "message_sent": message_sent
        })


# not used anymore but keeping it for future use
@staff_member_required
def test_email_view(request):

    message_sent = None

    subject = "Disaster Notification"
    message = "There is a new alert in your area."
    to_email = "bkai1@buffs.wtamu.edu"

    send_email_task.delay(subject, message, to_email)

    message_sent = "Email sent to Celery Worker"

    return render(request, "notification/test_email.html", {

        "message_sent": message_sent
    })

# not used anymore but keeping it for future use
@staff_member_required
def test_sms_view(request):

    message_sent = None

    if request.method == "POST":

        phone = request.POST.get("phone")
        carrier = request.POST.get("carrier")
        msg = request.POST.get("message")

        send_sms_task.delay(phone, carrier, msg)

        message_sent = "SMS Sent to Celery Worker"

    return render( request, "notification/test_sms.html", {
        "message_sent": message_sent
    })

# for testing alerts at initial stage of development
@staff_member_required
def test_alert_view(request):

    # create the primary key using uuid
    fake_id = str(uuid.uuid4())

    # basic information for the alert in email and text, I had to crunch down what I sent for texts
    alert = NoaaAlert.objects.create(
        id=fake_id,
        event="Test Disaster Alert",
        area_desc="Canyon, TX",
        description="This is a test alert for disaster notification system.",
        instruction="This is only a test.",
        category="Met",
        severity="Moderate",
        certainty="Likely",
        urgency="Expected",
        sent=timezone.now(),
        effective=timezone.now(),
        onset=timezone.now(),
        expires=timezone.now() + timezone.timedelta(hours=1),
        affected_zones=[],
    )

    notify_users_task(alert, "new")

    return render(request, "notification/test_alert.html", {
        "message_sent": "Completed"
    })
