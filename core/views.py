from datetime import date
from django import forms as django_forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookingForm
from .models import Booking, Court, SavedSlot


def _safe_next_url(next_url, fallback_name):
    if next_url and next_url.startswith("/"):
        return next_url
    return reverse(fallback_name)


def _parse_saved_slot_payload(data):
    try:
        parsed_date = django_forms.DateField().clean(data.get("date"))
        parsed_start_time = django_forms.TimeField().clean(data.get("start_time"))
        parsed_court_number = int(data.get("court_number"))
    except (django_forms.ValidationError, TypeError, ValueError):
        return None

    if parsed_court_number < 1:
        return None

    return {
        "date": parsed_date,
        "start_time": parsed_start_time,
        "court_number": parsed_court_number,
    }


def _build_booking_reminder_message(booking):
    edit_url = reverse("edit_booking", args=[booking.id])
    cancel_url = f"{reverse('my_bookings')}#booking-{booking.id}"

    return format_html(
        (
            "<strong>Reminder:</strong> "
            "You booked Court {court} on {date} at {time}. "
            "If your plans change, update it now."
            "<div class='mt-2'>"
            "<a href='{edit_url}' class='btn btn-sm "
            "btn-outline-primary me-2'>Edit booking</a>"
            "<a href='{cancel_url}' class='btn btn-sm "
            "btn-outline-danger'>Cancel booking</a>"
            "</div>"
        ),
        court=booking.court_number,
        date=booking.date.strftime("%d %b %Y"),
        time=booking.start_time.strftime("%H:%M"),
        edit_url=edit_url,
        cancel_url=cancel_url,
    )


def home(request):
    context = {
        "today": date.today(),
        "upcoming_count": Booking.objects.filter(date__gte=date.today()).count(),
    }
    return render(request, "core/home.html", context)


def courts(request):
    selected_date = request.GET.get("date")

    if selected_date:
        selected_date = date.fromisoformat(selected_date)
    else:
        selected_date = date.today()

    selected_surface = request.GET.get("surface", "").strip().lower()
    valid_surfaces = {choice[0] for choice in Court.Surface.choices}

    courts_queryset = Court.objects.order_by("number")

    if selected_surface in valid_surfaces:
        courts_queryset = courts_queryset.filter(surface=selected_surface)
    else:
        selected_surface = ""

    courts_data = [
        court for court in courts_queryset
        if court.is_available_on(selected_date)
    ]

    bookings = Booking.objects.filter(date=selected_date)

    time_slots = [
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
    ]
    
    booked_slots = {
        f"{booking.court_number}-{booking.start_time.strftime('%H:%M')}"
        for booking in bookings
        }

    return render(
        request,
        "core/courts.html",
        {
            "courts": courts_data,
            "surface_choices": Court.Surface.choices,
            "selected_surface": selected_surface,
            "selected_date": selected_date,
            "time_slots": time_slots,
            "booked_slots": booked_slots,
        },
    )


@login_required
def book_court(request):
    initial_data = {
        "court_number": request.GET.get("court_number"),
        "date": request.GET.get("date"),
        "start_time": request.GET.get("start_time"),
    }

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.owner = request.user
            booking.save()

            messages.success(
                request,
                _build_booking_reminder_message(booking),
                extra_tags="booking-reminder",
            )
            return redirect("my_bookings")
    else:
        form = BookingForm(initial=initial_data)

    saved_prefill = None
    if request.user.is_authenticated:
        saved_prefill = _parse_saved_slot_payload(initial_data)
        if saved_prefill:
            existing_saved_slot = SavedSlot.objects.filter(
                owner=request.user,
                date=saved_prefill["date"],
                start_time=saved_prefill["start_time"],
                court_number=saved_prefill["court_number"],
            ).first()
            saved_prefill["is_saved"] = bool(existing_saved_slot)
            saved_prefill["slot_id"] = existing_saved_slot.id if existing_saved_slot else None

    has_any_available_court = Court.objects.filter(is_available=True).exists()
    return render(
        request,
        "core/book_court.html",
        {
            "form": form,
            "has_any_available_court": has_any_available_court,
            "saved_prefill": saved_prefill,
            "is_edit_mode": False,
        },
    )


@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, owner=request.user)

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save(commit=False)
            updated_booking.owner = request.user
            updated_booking.save()

            messages.success(
                request,
                _build_booking_reminder_message(updated_booking),
                extra_tags="booking-reminder",
            )
            return redirect("my_bookings")
    else:
        form = BookingForm(instance=booking)

    has_any_available_court = Court.objects.filter(is_available=True).exists()
    return render(
        request,
        "core/book_court.html",
        {
            "form": form,
            "has_any_available_court": has_any_available_court,
            "saved_prefill": None,
            "is_edit_mode": True,
            "booking": booking,
        },
    )


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(owner=request.user)
        .order_by("date", "start_time")
    )
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    past_bookings = []
    upcoming_bookings = []

    for booking in bookings:
        is_past_booking = booking.date < today or (
            booking.date == today and booking.start_time < now_time
        )
        if is_past_booking:
            past_bookings.append(booking)
        else:
            upcoming_bookings.append(booking)

    saved_slots = list(
        SavedSlot.objects.filter(owner=request.user).order_by("date", "start_time", "court_number")
    )
    saved_slot_lookup = {
        (slot.date, slot.start_time, slot.court_number): slot.id for slot in saved_slots
    }

    for booking in upcoming_bookings + past_bookings:
        slot_key = (
            booking.date,
            booking.start_time,
            booking.court_number,
        )
        booking.saved_slot_id = saved_slot_lookup.get(slot_key)
        booking.is_saved_slot = bool(booking.saved_slot_id)

    court_map = {court.number: court for court in Court.objects.all()}
    occupied_saved_slot_keys = set(
        Booking.objects.filter(
            date__in=[slot.date for slot in saved_slots],
            court_number__in=[slot.court_number for slot in saved_slots],
        ).values_list("date", "start_time", "court_number")
    )
    for slot in saved_slots:
        court = court_map.get(slot.court_number)
        if not court:
            slot.can_rebook = False
            continue
        slot.can_rebook = court.is_available_on(slot.date) and (
            slot.date,
            slot.start_time,
            slot.court_number,
        ) not in occupied_saved_slot_keys

    return render(
        request,
        "core/my_bookings.html",
        {
            "upcoming_bookings": upcoming_bookings,
            "past_bookings": past_bookings,
            "saved_slots": saved_slots,
        },
    )


@login_required
@require_POST
def save_slot(request):
    redirect_url = _safe_next_url(request.POST.get("next"), "my_bookings")
    parsed_payload = _parse_saved_slot_payload(request.POST)
    if not parsed_payload:
        messages.error(request, "Could not save this slot. Please choose a valid court, date, and time.")
        return redirect(redirect_url)

    court = Court.objects.filter(number=parsed_payload["court_number"]).first()
    if not court:
        messages.error(request, "Could not save this slot because the selected court does not exist.")
        return redirect(redirect_url)

    saved_slot, created = SavedSlot.objects.get_or_create(
        owner=request.user,
        date=parsed_payload["date"],
        start_time=parsed_payload["start_time"],
        court_number=parsed_payload["court_number"],
        defaults={"surface": court.surface},
    )
    if not created and saved_slot.surface != court.surface:
        saved_slot.surface = court.surface
        saved_slot.save(update_fields=["surface"])

    if created:
        messages.success(
            request,
            (
                f"Saved Court {saved_slot.court_number} for "
                f"{saved_slot.date:%d %b %Y} at {saved_slot.start_time:%H:%M}."
            ),
        )
    else:
        messages.info(request, "This court/date/time is already saved.")
    return redirect(redirect_url)


@login_required
@require_POST
def unsave_slot(request, slot_id):
    redirect_url = _safe_next_url(request.POST.get("next"), "my_bookings")
    saved_slot = get_object_or_404(SavedSlot, pk=slot_id, owner=request.user)
    saved_slot.delete()
    messages.success(request, "Saved slot removed.")
    return redirect(redirect_url)


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.owner_id != request.user.id:
        return HttpResponseForbidden("You cannot cancel another user's booking.")

    booking.delete()
    messages.success(request, "Booking cancelled successfully.")
    return redirect("my_bookings")

