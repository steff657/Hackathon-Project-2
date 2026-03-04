from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import BookingForm
from .models import Booking, Court


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

            confirmation_message = (
                f"Booking confirmed for Court {booking.court_number} on "
                f"{booking.date:%d %b %Y} at {booking.start_time:%H:%M}."
            )
            messages.success(request, confirmation_message)
            return redirect("my_bookings")
    else:
        form = BookingForm(initial=initial_data)

    has_any_available_court = Court.objects.filter(is_available=True).exists()
    return render(
        request,
        "core/book_court.html",
        {"form": form, "has_any_available_court": has_any_available_court},
    )


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(owner=request.user).order_by("date", "start_time")
    return render(request, "core/my_bookings.html", {"bookings": bookings})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.owner_id != request.user.id:
        return HttpResponseForbidden("You cannot cancel another user's booking.")

    booking.delete()
    messages.success(request, "Booking cancelled successfully.")
    return redirect("my_bookings")

