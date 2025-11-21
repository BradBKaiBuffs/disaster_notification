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
from .models import NoaaAlert, UserAreaSubscription, StormEvent
from .forms import UserAreaSubscriptionForm, UserRegistrationForm, CsvUploadForm
# sends a forbidden response when someone not allowed opens a page
from django.http import HttpResponseForbidden
# decorator so only staff can use upload page
from django.contrib.admin.views.decorators import staff_member_required
# import settings to use BASE_DIR for file paths
from django.conf import settings
# import plotly graph objects to build charts
import plotly.graph_objs as pltgo
# plot function turns plotly chart into html to show on template
from plotly.offline import plot
# used to end json response to javascript
from django.http import JsonResponse


# disaster events grouped by year
def get_disaster_events_per_year():

    # grabs begin_year from StormEvent model as a list of dicts
    data = StormEvent.objects.values("begin_year")

    # adds up all the event_id counts for each year
    data = data.annotate(total=Count("event_id"))

    # sorting by year
    data = data.order_by("begin_year")

    return data

# builds the raw grouped info for disaster heatmap
def get_disaster_heatmap_data():

    # grabs begin year and begin month from StormEvent model and counts how many happened
    # groups by two fields
    data = (
        StormEvent.objects
        .values("begin_year", "begin_month")
        .annotate(total=Count("event_id"))
        .order_by("begin_year", "begin_month")
    )

    return data


# builds a matrix for the heatmap chart
def build_heatmap_matrix():

    # grabs grouped data
    data = get_disaster_heatmap_data()

    # list for years
    years = []
    for d in data:
        # only add if not already in list
        if d["begin_year"] not in years:
            years.append(d["begin_year"])

    # sort years
    years.sort()

    # list of 1 to 12 for each month
    months = list(range(1, 13))

    # matrix
    h = []
    for _ in years:
        # making a row of zeros matching the 12 months
        # i learned this pattern from stackoverflow
        empty_row = [0] * len(months)
        h.append(empty_row)

    # nadd matrix with data
    for row in data:
        # grabs the year and month from each row
        yr = row["begin_year"]
        mo = row["begin_month"]

        # count of events
        total = row["total"]

        # find index for year row
        yr_index = years.index(yr)

        # find index for month column
        mo_index = months.index(mo)

        # put the count number into that spot in matrix
        h[yr_index][mo_index] = total

    # send back the years, months, and matrix
    return years, months, h

# heatmap chart
# uses the matrix from build_heatmap_matrix and turns it into a plotly heatmap
def heatmap_chart():

    # call build_heatmap_matrix to build years, months, and the matrix h
    years, months, h = build_heatmap_matrix()

    # create a figure object from plotly
    fig = pltgo.Figure(
        data=pltgo.Heatmap(
            z=h,
            x=months,
            y=years,
            colorscale="Viridis",
            colorbar=dict(title="Events")
        )
    )

    # layout
    fig.update_layout(
        title="Disaster Events Heatmap from 2015-2025 (Year vs Month)",
        xaxis=dict(title="Month"),
        yaxis=dict(title="Year")
    )

    # turns the figure into a html div string
    return plot(fig, output_type="div")


# main dashboard page view
# displays charts and NOAA alerts
def dashboard_view(request):

    # grab yearly disaster data
    disaster_data = get_disaster_events_per_year()

    # two lists, one for years and one for totals
    years = []
    totals = []
    for d in disaster_data:
        # add the year to the years list
        years.append(d["begin_year"])
        # add the count to the totals list
        totals.append(d["total"])

    # bar chart for disaster events per year
    fig1 = pltgo.Figure(
        data=[pltgo.Bar(x=years, y=totals)],
        layout=pltgo.Layout(
            title="Disaster Events Per Year (2015-2025)",
            yaxis=dict(
                title="Event Count",
                # max(totals) * 1.1 to get a figure above bars
                range=[0, max(totals) * 1.1]
            )
        )
    )

    # convert the figure into html div
    disaster_chart = plot(fig1, output_type="div")

    # grab heatmap function to make the heatmap html
    heatmap = heatmap_chart()

    # basis of chart for disaster event types across all data
    # grabs event_type and counts how many for each one
    all_types = (
        StormEvent.objects
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )

    # build label and count lists for the chart
    labels = []
    counts = []
    for t in all_types:
        # event_type goes in labels
        labels.append(t["event_type"])
        # total number goes in counts
        counts.append(t["total"])

    # bar chart for disaster types with plotly
    fig_types = pltgo.Figure(
        data=[pltgo.Bar(x=labels, y=counts)],
        layout=pltgo.Layout(title="Disaster Events by Type (2015-2025)"),
        # max(totals) * 1.1 to get a figure above bars
    )

    # padding for y-axis range
    fig_types.update_yaxes(range=[0, max(totals) * 1.1])

    # convert disaster type chart to html
    disaster_type_chart = plot(fig_types, output_type="div")

    # grab noaa alerts but exclude test
    alerts = NoaaAlert.objects.exclude(event__icontains='test')

    # read any filters the user typed in query string
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

    # build the context dictionary that goes to the template
    context = {
        'heatmap': heatmap,
        'disaster_chart': disaster_chart,
        'disaster_type_chart': disaster_type_chart,
        'alerts': alerts
    }

    return render(request, 'notification/dashboard.html', context)

# grabs yearly disaster counts for a specific county and state
def get_county_yearly_data(state, county):

    # normalize the state by forcing lowercase and removing extra spaces
    st = state.lower().strip()

    # normalize county by lowercasing and removing extra spaces
    ct = county.lower().strip()

    # filter StormEvent model by state and county
    data = (
        StormEvent.objects
        .filter(state__iexact=st, county__iexact=ct)
        .values("begin_year")
        .annotate(total=Count("event_id"))
        .order_by("begin_year")
    )

    return data


# bar chart for the county disaster yearly numbers
def county_yearly_chart(state, county):

    # grabs grouped county disaster info from get_county_yearly_data
    yearly = get_county_yearly_data(state, county)

    # build lists for years and totals
    years = []
    totals = []
    for r in yearly:
        # add year to list
        years.append(r["begin_year"])
        # add total for that year
        totals.append(r["total"])

    # bar chart using plotly
    fig = pltgo.Figure(
        data=[pltgo.Bar(x=years, y=totals)],
        layout=pltgo.Layout(
            title=f"Disaster Events Per Year in {county}, {state} (2015 to 2025)",
            yaxis=dict(title="Count")
        )
    )

    # return as html string
    return plot(fig, output_type="div")


# grabs disaster event types and how many happened for each type
def get_county_event_type_data(state, county):

    # cleaning like before
    st = state.lower().strip()
    ct = county.lower().strip()

    # group by event_type and count how many for each type
    data = (
        StormEvent.objects
        .filter(state__iexact=st, county__iexact=ct)
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )

    return data


# bar chart shows disaster event types for a certain county
def county_event_type_chart(state, county):

    # grab type data from get_county_event_type_data
    type_data = get_county_event_type_data(state, county)

    # build label and count lists
    labels = []
    counts = []
    for r in type_data:
        # type name goes into labels
        labels.append(r["event_type"])
        # total count goes into counts
        counts.append(r["total"])

    # bar chart for event types using plotly again
    fig = pltgo.Figure(
        data=[pltgo.Bar(x=labels, y=counts)],
        layout=pltgo.Layout(title=f"Disaster Events by Type in {county}, {state} (2015 to 2025)")
    )

    # convert to html
    return plot(fig, output_type="div")


# returns a list of counties for a given state as json
# this is for ajax call from javascript when user picks a state
def get_counties_for_state(request):

    # get the state from querystring and trim spaces
    state = request.GET.get("state", "").strip()

    # filters StormEvent model for all rows that match state choice then grab distinct counties and order by county name
    counties = list(
        StormEvent.objects.filter(state__iexact=state)
        .values_list("county", flat=True)
        .distinct()
        .order_by("county")
    )

    # return json response that javascript can read
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


# personalized user page view
# user must be logged in
@login_required
def user_alerts_view(request):

    # grab all the states from StormEvent model
    # values_list grabs the state column not whole rows
    states = (
        StormEvent.objects
        .values_list("state", flat=True)
        .distinct()
        .order_by("state")
    )

    # build a county map for each state like before
    county_map = {}

    # loop every state for counties
    for s in states:
        # filter by state and counties
        # using distinct and order_by
        county_map[s] = list(
            StormEvent.objects
            .filter(state=s)
            .values_list("county", flat=True)
            .distinct()
            .order_by("county")
        )

    # grabs all subscriptions for the logged in user
    # allows county selection to view disaster charts
    subscriptions = UserAreaSubscription.objects.filter(user=request.user)

    # read selected county from querystring if provided
    selected_county = request.GET.get("county", "").strip()

    # if no county selected and user has subscriptions, then default to the first one
    if not selected_county and subscriptions.exists():
        selected_county = subscriptions.first().county

    # determine the state for the selected county
    # finds one matching row and grabs the state
    selected_state = None

    # if a county exists, then find its state
    if selected_county:
        # filter rows for that county paired with the first state found
        row = (
            StormEvent.objects
            .filter(county__iexact=selected_county)
            .values_list("state", flat=True)
            .first()
        )

        # only update if row is not None
        if row:
            selected_state = row

    # notification type if user posted a form
    selected_type = request.POST.get("notification_type", "")

    # if user submitted the form then build a subscription form from POST data
    if request.method == "POST":
        form = UserAreaSubscriptionForm(request.POST)
        selected_type = request.POST.get("notification_type", "")

    # blank form for new subscription
    else:
        form = UserAreaSubscriptionForm()
        selected_type = ""

    # build the yearly chart using county_yearly_chart
    # both county and state must be chosen for chart to work
    yearly_chart = (
        county_yearly_chart(selected_state, selected_county)
        if selected_state and selected_county else None
    )

    # build the disaster type chart the same way
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
    })


# deletes user subscription row
@login_required
def delete_subscription_view(request, sub_id):

    # grabs the sub id
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


# staff users upload annual csv files containing cleaned disaster event data
@staff_member_required
def upload_csv_view(request):

    # checks if user is staff
    if not request.user.is_staff:
        return HttpResponseForbidden("Only admin has access to this page.")

    # placeholder for message after upload completes
    message = None

    # check if submitted form
    if request.method == 'POST':

        # build form
        form = CsvUploadForm(request.POST, request.FILES)

        if form.is_valid():

            # use the uploaded file
            upload_file = form.cleaned_data["file"]

            # build the full save path
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

            # after uploading and starting import, set message text
            message = "CSV uploaded"

    # GET request shows empty form
    else:
        form = CsvUploadForm()
        
    return render(request, "notification/upload_csv.html", {"form": form, "message": message})