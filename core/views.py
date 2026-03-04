from datetime import date

from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

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
            form.save()
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


def my_bookings(request):
    bookings = Booking.objects.order_by("date", "start_time")
    return render(request, "core/my_bookings.html", {"bookings": bookings})
