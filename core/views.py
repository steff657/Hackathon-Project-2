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
    today = date.today()
    courts_data = [
        court for court in Court.objects.order_by("number") if court.is_available_on(today)
    ]
    return render(request, "core/courts.html", {"courts": courts_data})


def book_court(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            if request.user.is_authenticated:
                booking.owner = request.user
            booking.save()
            messages.success(request, "Booking created successfully.")
            return redirect("my_bookings")
    else:
        form = BookingForm()

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
