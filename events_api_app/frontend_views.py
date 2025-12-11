# events_api_app/frontend_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive

from .models import Event, RSVP, Review, UserProfile
from django.contrib.auth.models import User

def _parse_datetime_input(value):
    """
    Accepts:
      - ISO 8601 string (e.g. 2025-12-20T10:00 or 2025-12-20T10:00:00)
      - HTML datetime-local value (same format)
    Returns a timezone-aware datetime or None.
    """
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        # Try replacing space with 'T'
        try:
            dt = parse_datetime(value.replace(' ', 'T'))
        except Exception:
            dt = None
    if dt is None:
        return None
    if is_naive(dt):
        # assume local timezone and make aware
        return make_aware(dt, timezone.get_current_timezone())
    return dt

def events_list_view(request):
    """
    Shows a list of events with RSVP counts and review counts.
    Uses normalized dict keys so template lookup is simple (no spaces in keys).
    """
    user = request.user
    qs = Event.objects.all().order_by('-created_at')
    if user.is_authenticated:
        qs = qs.filter(
            models.Q(is_public=True) |
            models.Q(invited_users=user) |
            models.Q(organizer=user)
        ).distinct()
    else:
        qs = qs.filter(is_public=True)

    events = qs.select_related('organizer').prefetch_related('invited_users')

    events_summary = []
    for ev in events:
        # normalized keys: 'Going', 'Maybe', 'Not_Going'
        counts = {'Going': 0, 'Maybe': 0, 'Not_Going': 0}
        for r in ev.rsvps.all().values('status'):
            st = r['status']
            if st == 'Not Going':
                counts['Not_Going'] += 1
            else:
                counts[st] = counts.get(st, 0) + 1

        review_count = ev.reviews.count()
        user_rsvp = None
        if user.is_authenticated:
            ur = RSVP.objects.filter(event=ev, user=user).first()
            if ur:
                user_rsvp = ur.status
        events_summary.append({
            'event': ev,
            'rsvp_counts': counts,
            'review_count': review_count,
            'user_rsvp': user_rsvp,
        })

    return render(request, "events/list.html", {"events_summary": events_summary})


def event_detail_view(request, event_id):
    """
    Event detail page: shows event data and its reviews along with counts and user's RSVP.
    """
    event = get_object_or_404(Event, id=event_id)

    # permission: private events viewable by invited users or organizer only
    if not event.is_public:
        if not request.user.is_authenticated or (request.user != event.organizer and request.user not in event.invited_users.all()):
            messages.error(request, "You are not allowed to view this private event.")
            return redirect('events_list')

    reviews = event.reviews.all().order_by('-created_at')
    user_rsvp = None
    if request.user.is_authenticated:
        user_rsvp = RSVP.objects.filter(event=event, user=request.user).first()

    counts = {'Going': 0, 'Maybe': 0, 'Not_Going': 0}
    for r in event.rsvps.all().values('status'):
        st = r['status']
        if st == 'Not Going':
            counts['Not_Going'] += 1
        else:
            counts[st] = counts.get(st, 0) + 1

    return render(request, "events/detail.html", {
        "event": event,
        "reviews": reviews,
        "user_rsvp": user_rsvp,
        "rsvp_counts": counts,
        "review_count": reviews.count(),
    })


@login_required
def rsvp_create_or_update(request, event_id):
    """
    Called when user clicks RSVP buttons (Going/Maybe/Not Going).
    Redirects back to detail.
    """
    event = get_object_or_404(Event, id=event_id)

    # Check permission for private events
    if not event.is_public and request.user != event.organizer and request.user not in event.invited_users.all():
        messages.error(request, "You are not invited to this private event.")
        return redirect('events_detail', event_id=event.id)

    if request.method == "POST":
        status = request.POST.get("status")
        if status not in dict(RSVP.STATUS_CHOICES):
            messages.error(request, "Invalid RSVP status.")
            return redirect('events_detail', event_id=event.id)

        rsvp, created = RSVP.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={"status": status}
        )
        messages.success(request, f"RSVP set to '{rsvp.status}'.")
    return redirect('events_detail', event_id=event.id)


@login_required
def post_review(request, event_id):
    """
    Handles posting/updating a review from the event detail page.
    """
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        # Basic validation
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                raise ValueError
        except Exception:
            messages.error(request, "Rating must be an integer between 1 and 5.")
            return redirect('events_detail', event_id=event.id)

        # Update if exists else create
        existing = Review.objects.filter(event=event, user=request.user).first()
        if existing:
            existing.rating = rating_int
            existing.comment = comment
            existing.save()
            messages.success(request, "Updated your review.")
        else:
            Review.objects.create(event=event, user=request.user, rating=rating_int, comment=comment)
            messages.success(request, "Review posted.")

    return redirect('events_detail', event_id=event.id)


@login_required
def create_event_view(request):
    """
    Create an event via a simple HTML form.
    invited_users_input: comma-separated usernames (optional).
    start_time/end_time expected in 'YYYY-MM-DDTHH:MM' or ISO formats (datetime-local).
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        location = request.POST.get("location", "").strip()
        start_raw = request.POST.get("start_time", "").strip()
        end_raw = request.POST.get("end_time", "").strip()
        is_public = bool(request.POST.get("is_public", ""))  # checkbox
        invited_input = request.POST.get("invited_users", "").strip()

        # Basic validations
        if not title:
            messages.error(request, "Title is required.")
            return redirect('events_create')
        if not start_raw or not end_raw:
            messages.error(request, "Start and end times are required.")
            return redirect('events_create')

        start_dt = _parse_datetime_input(start_raw)
        end_dt = _parse_datetime_input(end_raw)
        if not start_dt or not end_dt:
            messages.error(request, "Invalid date/time format. Use the form fields provided.")
            return redirect('events_create')
        if start_dt >= end_dt:
            messages.error(request, "start_time must be before end_time.")
            return redirect('events_create')

        # Create event
        ev = Event.objects.create(
            title=title,
            description=description,
            organizer=request.user,
            location=location,
            start_time=start_dt,
            end_time=end_dt,
            is_public=is_public
        )

        # handle invited users (optional)
        if invited_input:
            usernames = [u.strip() for u in invited_input.split(",") if u.strip()]
            for uname in usernames:
                try:
                    u = User.objects.get(username=uname)
                    ev.invited_users.add(u)
                except User.DoesNotExist:
                    # ignore unknown usernames but add a flash message
                    messages.warning(request, f"User '{uname}' not found — ignored.")
        messages.success(request, "Event created.")
        return redirect('events_detail', event_id=ev.id)

    # GET -> render form
    return render(request, "events/create.html", {})


@login_required
def profile_view(request):
    """
    Simple user profile page showing UserProfile fields and list of user's events and RSVPs.
    """
    user = request.user
    # Ensure UserProfile exists
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    organized_events = user.organized_events.all().order_by('-created_at')
    invited_events = user.invited_events.all().order_by('-created_at')
    rsvps = RSVP.objects.filter(user=user).select_related('event').order_by('-created_at')
    reviews = Review.objects.filter(user=user).select_related('event').order_by('-created_at')

    return render(request, "registration/profile.html", {
        "profile": profile,
        "organized_events": organized_events,
        "invited_events": invited_events,
        "rsvps": rsvps,
        "reviews": reviews,
    })
