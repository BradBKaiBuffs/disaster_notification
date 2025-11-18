import os
import json
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import NoaaAlert, UserAreaSubscription
from .forms import UserAreaSubscriptionForm, UserRegistrationForm, CsvUploadForm


# dashboard view
def dashboard_view(request):

    # excludes test alerts
    alerts = NoaaAlert.objects.exclude(event__icontains='test')

    # ff the user typed something in the filter boxes uses that
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    # checks if any filter is being used
    any_filter = area or severity or urgency

    # apply filters only if user typed something
    if any_filter:

        # area filter
        if area:
            alerts = alerts.filter(area_desc__icontains=area)

        # severity filter
        if severity:
            alerts = alerts.filter(severity__iexact=severity)

        # urgency filter
        if urgency:
            alerts = alerts.filter(urgency__iexact=urgency)

        # order and slice
        alerts = alerts.order_by('-sent')[:50]

    else:
        # if there is no filter then returns 5 newest alerts
        alerts = alerts.order_by('-sent')[:5]

    # sends the filtered alerts to the page
    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)


# create or update alert subscription
def subscribe_view(request):

    # template breaks if not stated
    user_form = None
    sub_form = None

    # load areas
    areas = (
        NoaaAlert.objects
        .exclude(event__icontains="test")
        .values_list("area_desc", flat=True)
        .distinct()
        .order_by("area_desc")
    )

    # checks if user already logged in
    if request.user.is_authenticated:

        # handle form submission for extra subscription rows
        if request.method == "POST":
            sub_form = UserAreaSubscriptionForm(request.POST)

            # save subscription choices tied to current user
            if sub_form.is_valid():
                subscription = sub_form.save(commit=False)
                subscription.user = request.user
                subscription.save()
                return redirect("subscribe")

        # show empty form when page first loads
        else:
            sub_form = UserAreaSubscriptionForm()

        return render(request, "notification/subscribe.html", {
            # account fields for new user
            "user_form": user_form,
            # alert settings fields
            "sub_form": sub_form,
            # area field
            "areas": areas,
        })

    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        sub_form = UserAreaSubscriptionForm(request.POST)

        # checks if valid
        if user_form.is_valid() and sub_form.is_valid():
            # save user account first
            user = user_form.save()
            login(request, user)

            # save subscription linked to new user
            subscription = sub_form.save(commit=False)
            subscription.user = user
            subscription.save()

            return redirect("subscribe")

    # leads if not logged in
    else:
        user_form = UserRegistrationForm()
        sub_form = UserAreaSubscriptionForm()

    return render(
        request,
        "notification/subscribe.html",
        {
            # account fields for new user
            "user_form": user_form,
            # alert settings fields
            "sub_form": sub_form,
            # area field
            "areas": areas,
        },
    )


@login_required
# dedicated user alert page
def user_alerts_view(request):

    # get only user's saved subscriptions
    subscriptions = UserAreaSubscription.objects.filter(user=request.user)

    # picks which area is being viewed
    selected_area = request.GET.get("area", "").strip()

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

    # severity counter
    severity_counts = (
        alerts_qs.values("severity")   # ⚠ NO SLICE HERE
                 .annotate(count=Count("severity"))
                 .order_by("-count")
    )

    # split into lists for javascript charts
    severity_labels = [row["severity"] for row in severity_counts]
    severity_values = [row["count"] for row in severity_counts]

    # handle submitted subscription form
    if request.method == "POST":
        form = UserAreaSubscriptionForm(request.POST)
        if form.is_valid():
            # assign owner
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
    })


@login_required
# delete subscription
def delete_subscription_view(request, sub_id):
    # finds sub matching id owned by user and if not found throws a 404 error
    sub = get_object_or_404(UserAreaSubscription, id=sub_id, user=request.user)
    sub.delete()
    messages.warning(request, "Subscription removed.")
    return redirect("user_alerts")


# directory where uploaded files are saved temporarily
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# upload csv view
def upload_csv_view(request):
    message = None
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data["file"]
            save_path = os.path.join(UPLOAD_DIR, upload_file.name)
            # write file to disk in chunks
            with open(save_path, "wb+") as destination:
                for chunk in upload_file.chunks():
                    destination.write(chunk)
            # trigger separate process to import data
            subprocess.Popen([
                "python", "manage.py", "import_storms", save_path
            ])
            message = "CSV uploaded"
    else:
        form = CsvUploadForm()
    return render(request, "notification/upload_csv.html", {"form": form, "message": message})