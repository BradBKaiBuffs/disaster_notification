from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .models import noaa_alerts, user_area_subscription
from .forms import user_area_subscription_form, user_registration_form
from django.db.models import Count
import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# view shows recent alerts and keeps out test ones
def dashboard(request):

    # build base queryset only once (do NOT order here yet)
    alerts = noaa_alerts.objects.exclude(event__icontains='test')

    # pulls filter text if the user typed something in the filter boxes
    area = request.GET.get('area', '').strip()
    severity = request.GET.get('severity', '').strip()
    urgency = request.GET.get('urgency', '').strip()

    # checks if any filter is being used
    any_filter = area or severity or urgency

    # apply filters ONLY if user typed something
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

        # NOW it is safe to order and slice
        alerts = alerts.order_by('-sent')[:50]

    else:
        # no filter → return 5 newest alerts
        alerts = alerts.order_by('-sent')[:5]

    # sends the filtered alerts to the page
    context = {
        'alerts': alerts
    }
    return render(request, 'notification/dashboard.html', context)


# view lets a user create or update their alert subscription
def subscribe(request):

    # template breaks if not stated
    user_form = None
    sub_form = None

    # load areas
    areas = (
        noaa_alerts.objects
        .exclude(event__icontains="test")
        .values_list("area_desc", flat=True)
        .distinct()
        .order_by("area_desc")
    )

    # checks if user already logged in
    if request.user.is_authenticated:

        # handle form submit for extra subscription rows
        if request.method == "POST":
            sub_form = user_area_subscription_form(request.POST)

            # save subscription row tied to current user
            if sub_form.is_valid():
                subscription = sub_form.save(commit=False)
                subscription.user = request.user
                subscription.save()
                return redirect("subscribe")

        # show empty form when page first loads
        else:
            sub_form = user_area_subscription_form()

        areas = (
            noaa_alerts.objects
            .exclude(event__icontains="test")
            .values_list("area_desc", flat=True)
            .distinct()
            .order_by("area_desc")
        )
        areas_list = list(areas)

        return render(request, "notification/subscribe.html", {
            # account fields for new user
            "user_form": user_form,
            # alert settings fields
            "sub_form": sub_form,
            # area field
            "areas": areas,
        })

    if request.method == "POST":
        user_form = user_registration_form(request.POST)
        sub_form = user_area_subscription_form(request.POST)

        # both account and subscription must pass validation
        if user_form.is_valid() and sub_form.is_valid():
            # save user account first
            user = user_form.save()
            login(request, user)

            # now save subscription linked to new user
            subscription = sub_form.save(commit=False)
            subscription.user = user
            subscription.save()

            return redirect("subscribe")

    # first load for non logged visitor
    else:
        user_form = user_registration_form()
        sub_form = user_area_subscription_form()

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
def user_alerts(request):

    # get only this user's saved subscriptions
    subscriptions = user_area_subscription.objects.filter(user=request.user)

    # picks which area is being viewed on the page
    selected_area = request.GET.get("area", "").strip()

    # auto set a default area if user didn’t choose one yet
    if not selected_area and subscriptions.exists():
        selected_area = subscriptions.first().area

    # pull full alert queryset and remove test alerts
    alerts_qs = noaa_alerts.objects.exclude(event__icontains="test")

    # filter alerts if user selected an area
    if selected_area:
        alerts_qs = alerts_qs.filter(area_desc__icontains=selected_area)

    # ordering ALWAYS before slicing to avoid django error
    alerts = alerts_qs.order_by("-sent")[:50]

    # severity counter (for charts)
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
        form = user_area_subscription_form(request.POST)
        if form.is_valid():
            # assign owner
            sub = form.save(commit=False)
            sub.user = request.user
            sub.save()
            messages.success(request, "subscription added")
            return redirect("user_alerts")
    else:
        form = user_area_subscription_form()

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
def delete_subscription(request, sub_id):
    # finds sub matching id owned by user and if not found throws a 404 error
    sub = get_object_or_404(user_area_subscription, id=sub_id, user=request.user)
    sub.delete()
    messages.warning(request, "Subscription removed.")
    return redirect("user_alerts")