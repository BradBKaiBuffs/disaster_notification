import os
import json
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import NoaaAlert, UserAreaSubscription, StormEvent
from .forms import UserAreaSubscriptionForm, UserRegistrationForm, CsvUploadForm
from django.http import HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import plotly.graph_objs as pltgo
from plotly.offline import plot

# dashboard chart that does storm events per year
def get_storm_events_per_year():
    data = StormEvent.objects.values("begin_year")
    data = data.annotate(total=Count("event_id"))
    data = data.order_by("begin_year")
    return data

# builds data for heatmap
# grouping by year and month
def get_storm_heatmap_data():
    data = (
        StormEvent.objects
        .values("begin_year", "begin_month")
        .annotate(total=Count("event_id"))
        .order_by("begin_year", "begin_month")
    )
    return data

# builds matrix for plotly heatmap
def build_heatmap_matrix():
    data = get_storm_heatmap_data()

    # gets unique list of years
    years = []
    for d in data:
        if d["begin_year"] not in years:
            years.append(d["begin_year"])
    years.sort()

    # month list
    months = list(range(1, 13))

    # makes empty rows for each year
    z = []
    for _ in years:
        empty_row = [0] * len(months)
        z.append(empty_row)

    # fills in totals
    for row in data:
        yr = row["begin_year"]
        mo = row["begin_month"]
        total = row["total"]

        yr_index = years.index(yr)
        mo_index = months.index(mo)
        z[yr_index][mo_index] = total

    return years, months, z


# heatmap
def heatmap_chart():
    years, months, z = build_heatmap_matrix()

    fig = pltgo.Figure(
        data=pltgo.Heatmap(
            z=z,
            x=months,
            y=years,
            colorscale="Viridis",
            colorbar=dict(title="Events")
        )
    )

    fig.update_layout(
        title="Storm Events Heatmap from 2015-2025 (Year vs Month)",
        xaxis=dict(title="Month"),
        yaxis=dict(title="Year")
    )

    return plot(fig, output_type="div")

# dashboard view
def dashboard_view(request):

    # chart for storm events per year
    storm_data = get_storm_events_per_year()

    years = []
    totals = []
    for d in storm_data:
        years.append(d["begin_year"])
        totals.append(d["total"])

    fig1 = pltgo.Figure(
        data=[pltgo.Bar(x=years, y=totals)],
        layout=pltgo.Layout(
            title="Storm Events Per Year (2015-2025)",
            yaxis=dict(title="Event Count", range=[0, max(totals) * 1.1])
        )
    )
    storm_chart = plot(fig1, output_type="div")

    # heatmap
    heatmap = heatmap_chart()

    # storm type chart for whole dataset
    all_types = (
        StormEvent.objects
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )

    labels = [t["event_type"] for t in all_types]
    counts = [t["total"] for t in all_types]

    fig_types = pltgo.Figure(
        data=[pltgo.Bar(x=labels, y=counts)],
        layout=pltgo.Layout(title="Storm Events by Type (2015-2025)")
    )

    storm_type_chart = plot(fig_types, output_type="div")

    # excludes test alerts
    alerts = NoaaAlert.objects.exclude(event__icontains='test')

    # gets filter text
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    any_filter = area or severity or urgency

    # filtering
    if any_filter:

        if area:
            alerts = alerts.filter(area_desc__icontains=area)

        if severity:
            alerts = alerts.filter(severity__iexact=severity)

        if urgency:
            alerts = alerts.filter(urgency__iexact=urgency)

        alerts = alerts.order_by('-sent')[:50]

    else:
        alerts = alerts.order_by('-sent')[:5]

    context = {
        'heatmap': heatmap,
        'storm_chart': storm_chart,
        'storm_type_chart': storm_type_chart,
        'alerts': alerts
    }

    return render(request, 'notification/dashboard.html', context)

# yearly weather counts for county
def get_county_yearly_data(county):

    cleaned = county.lower().strip()

    data = (
        StormEvent.objects
        .filter(county__iexact=cleaned)
        .values("begin_year")
        .annotate(total=Count("event_id"))
        .order_by("begin_year")
    )
    return data

# bar chart for county
def county_yearly_chart(county):
    yearly = get_county_yearly_data(county)

    years = []
    totals = []
    for r in yearly:
        years.append(r["begin_year"])
        totals.append(r["total"])

    fig = pltgo.Figure(
        data=[pltgo.Bar(x=years, y=totals)],
        layout=pltgo.Layout(title=f"Storm Events Per Year in {county}", yaxis=dict(title="Count"))
    )

    return plot(fig, output_type="div")

# storm type breakdown
def get_county_event_type_data(county):

    cleaned = county.lower().strip()

    data = (
        StormEvent.objects
        .filter(county__iexact=cleaned)
        .values("event_type")
        .annotate(total=Count("event_id"))
        .order_by("-total")
    )
    return data

# chart for storm type
def county_event_type_chart(county):

    type_data = get_county_event_type_data(county)

    labels = []
    counts = []
    for r in type_data:
        labels.append(r["event_type"])
        counts.append(r["total"])

    fig = pltgo.Figure(
        data=[pltgo.Bar(x=labels, y=counts)],
        layout=pltgo.Layout(
            title=f"Storm Events by Type in {county}",
        )
    )

    return plot(fig, output_type="div")

# create or update alert subscription
def subscribe_view(request):

    user_form = None
    sub_form = None

    # area list
    areas = (
        NoaaAlert.objects
        .exclude(event__icontains="test")
        .values_list("area_desc", flat=True)
        .distinct()
        .order_by("area_desc")
    )

    # county list
    counties = (
        StormEvent.objects
        .values_list("county", flat=True)
        .distinct()
        .order_by("county")
    )

    # logged in user
    if request.user.is_authenticated:

        if request.method == "POST":
            sub_form = UserAreaSubscriptionForm(request.POST)

            # check
            if sub_form.is_valid():
                sub = sub_form.save(commit=False)
                sub.user = request.user
                sub.save()
                return redirect("subscribe")

        else:
            sub_form = UserAreaSubscriptionForm()

        return render(request, "notification/subscribe.html", {
            "user_form": user_form,
            "sub_form": sub_form,
            "areas": areas,
            "counties": counties,
        })

    # new user creating account + alerts
    if request.method == "POST":

        user_form = UserRegistrationForm(request.POST)
        sub_form = UserAreaSubscriptionForm(request.POST)

        # check
        if user_form.is_valid() and sub_form.is_valid():

            user = user_form.save()
            login(request, user)

            sub = sub_form.save(commit=False)
            sub.user = user
            sub.save()

            return redirect("subscribe")

    else:
        user_form = UserRegistrationForm()
        sub_form = UserAreaSubscriptionForm()

    return render(request, "notification/subscribe.html", {
        "user_form": user_form,
        "sub_form": sub_form,
        "areas": areas,
        "counties": counties,
    })

@login_required
# dedicated user alert page
def user_alerts_view(request):

    # get only user's saved subscriptions
    subscriptions = UserAreaSubscription.objects.filter(user=request.user)

    # picks which area is being viewed
    selected_area = request.GET.get("area", "").strip()

    # graphs for county
    selected_county = request.GET.get("county", "").strip()

    # auto set a default area if user didn’t choose one yet
    if not selected_area and subscriptions.exists():
        selected_area = subscriptions.first().area

    # pull full alert query except for test alerts
    alerts_qs = NoaaAlert.objects.exclude(event__icontains="test")

    # filter alerts if user selected an area
    if selected_area:
        alerts_qs = alerts_qs.filter(area_desc__icontains=selected_area)

    # ordering before slicing to avoid django error I kept getting
    alerts = alerts_qs.order_by("-sent")[:50]

    # picks which county is being viewed
    selected_county = request.GET.get("county", "").strip()

    # picks first saved county if user didnt choose one yet
    if not selected_county and subscriptions.exists():
        selected_county = subscriptions.first().county

    # filtered storm events for county dashboards
    county_events = []
    if selected_county:
        county_events = StormEvent.objects.filter(county__iexact=selected_county)

    # severity counter
    severity_counts = (
        alerts_qs.values("severity")
        .annotate(count=Count("severity"))
        .order_by("-count")
    )

    # lists for javascript charts
    severity_labels = []
    severity_values = []
    for s in severity_counts:
        severity_labels.append(s["severity"])
        severity_values.append(s["count"])

    # form handler
    if request.method == "POST":
        form = UserAreaSubscriptionForm(request.POST)

        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()
            messages.success(request, "subscription added")
            return redirect("user_alerts")

    else:
        form = UserAreaSubscriptionForm()

    # send everything to page
    return render(request, "notification/user_alerts.html", {
        "subscriptions": subscriptions,
        "selected_area": selected_area,
        "alerts": alerts,
        "form": form,
        "severity_labels": json.dumps(severity_labels),
        "severity_values": json.dumps(severity_values),
        "selected_county": selected_county,
        "county_events": county_events,
        "county_yearly_chart": county_yearly_chart(selected_county) if selected_county else None,
        "county_event_type_chart": county_event_type_chart(selected_county) if selected_county else None,
    })


@login_required
# delete subscription
def delete_subscription_view(request, sub_id):

    # finds sub matching id owned by user
    sub = get_object_or_404(UserAreaSubscription, id=sub_id, user=request.user)
    sub.delete()

    # prompt stating completion
    messages.warning(request, "Subscription removed.")

    return redirect("user_alerts")


# directory where uploaded files are saved temporarily
UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# only admin can access
@staff_member_required
# upload csv
def upload_csv_view(request):

    # only admin can upload csv
    if not request.user.is_staff:
        return HttpResponseForbidden("Only admin has access to this page.")

    message = None
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data["file"]
            save_path = os.path.join(UPLOAD_DIR, upload_file.name)

            # write file
            with open(save_path, "wb+") as destination:
                for chunk in upload_file.chunks():
                    destination.write(chunk)

            # run import command
            subprocess.Popen([
                "python", "manage.py", "import_storms", save_path
            ])

            message = "CSV uploaded"
    else:
        form = CsvUploadForm()
        
    return render(request, "notification/upload_csv.html", {"form": form, "message": message})