from datetime import datetime, time, timedelta
from allauth.account.forms import LoginForm, SignupForm
from django import forms
from django.core.exceptions import ValidationError

from .models import Booking, ContactRequest, Court

BOOKING_OPEN_TIME = time(9, 0)
BOOKING_CLOSE_TIME = time(17, 0)
LAST_HOURLY_START_TIME = time(16, 0)


class BookingForm(forms.ModelForm):
    court_number = forms.TypedChoiceField(
        coerce=int,
        empty_value=None,
        choices=(),
    )

    class Meta:
        model = Booking
        fields = [
            "player_name",
            "player_email",
            "date",
            "start_time",
            "duration_minutes",
            "court_number",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "min": BOOKING_OPEN_TIME.strftime("%H:%M"),
                    "max": LAST_HOURLY_START_TIME.strftime("%H:%M"),
                    "step": "3600",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_date = self._get_selected_date()
        available_courts = self._get_available_courts(selected_date)
        choices = [
            (court.number, f"Court {court.number} ({court.get_surface_display()})")
            for court in available_courts
        ]
        # Set time picker restrictions based on selected court
        if self.data.get("court_number"):
            try:
                court_number = int(self.data.get("court_number"))
                court = Court.objects.filter(number=court_number).first()
                if court:
                    effective_open = max(court.opening_time, BOOKING_OPEN_TIME)
                    effective_close = min(court.closing_time, BOOKING_CLOSE_TIME)
                    latest_hourly_start = time(max(effective_open.hour, effective_close.hour - 1), 0)
                    self.fields["start_time"].widget.attrs.update({
                        "min": effective_open.strftime("%H:%M"),
                        "max": latest_hourly_start.strftime("%H:%M"),
                        "step": "3600",  # 1 hour intervals
                    })
            except (ValueError, TypeError):
                pass

        posted_court = self.data.get("court_number") if self.is_bound else None
        if posted_court:
            try:
                posted_number = int(posted_court)
            except (TypeError, ValueError):
                posted_number = None
            if posted_number and posted_number not in {value for value, _ in choices}:
                court = Court.objects.filter(number=posted_number).first()
                if court:
                    choices.append(
                        (
                            court.number,
                            f"Court {court.number} ({court.get_surface_display()})",
                        )
                    )
        self.fields["court_number"].choices = choices
        self.fields["court_number"].label = "Court"

    def _get_selected_date(self):
        raw_date = self.data.get("date") if self.data else None
        if not raw_date and self.initial:
            raw_date = self.initial.get("date")
        if not raw_date and self.instance and self.instance.pk:
            raw_date = self.instance.date

        if not raw_date:
            return None
        if hasattr(raw_date, "year"):
            return raw_date

        try:
            return forms.DateField().clean(raw_date)
        except ValidationError:
            return None

    def _get_available_courts(self, selected_date):
        courts = Court.objects.filter(is_available=True).order_by("number")
        if selected_date:
            courts = [
                court for court in courts if court.is_available_on(selected_date)
            ]
        return courts

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("start_time")
        court_number = cleaned_data.get("court_number")

        if not booking_date or not booking_time or court_number is None:
            return cleaned_data

        try:
            court = Court.objects.get(number=court_number)
        except Court.DoesNotExist:
            self.add_error("court_number", "Selected court does not exist.")
            return cleaned_data

        if not court.is_available_on(booking_date):
            reason = "Court is unavailable."
            if (
                court.maintenance_start
                and court.maintenance_end
                and court.maintenance_start <= booking_date <= court.maintenance_end
            ):
                reason = "Court is under maintenance for the selected date."
            elif court.maintenance_reason:
                reason = f"Court is unavailable: {court.maintenance_reason}"
            self.add_error("court_number", reason)

        # Check if booking is within court opening hours
        start_datetime = datetime.combine(booking_date, booking_time)
        duration = cleaned_data.get("duration_minutes", 60)
        end_datetime = start_datetime + timedelta(minutes=duration)

        if booking_time < court.opening_time:
            self.add_error(
                "start_time",
                f"Court opens at {court.opening_time.strftime('%H:%M')}. Please select a later time."
            )

        if end_datetime.time() > court.closing_time:
            self.add_error(
                "start_time",
                f"Court closes at {court.closing_time.strftime('%H:%M')}. This booking would end too late."
            )

        # Enforce platform-wide bookable window (09:00 to 17:00).
        if booking_time < BOOKING_OPEN_TIME:
            self.add_error(
                "start_time",
                "Bookings are only available between 09:00 and 17:00.",
            )

        if end_datetime.time() > BOOKING_CLOSE_TIME:
            self.add_error(
                "start_time",
                "Bookings are only available between 09:00 and 17:00.",
            )

        existing_slot_bookings = Booking.objects.filter(
            date=booking_date,
            start_time=booking_time,
            court_number=court_number,
        )
        if self.instance.pk:
            existing_slot_bookings = existing_slot_bookings.exclude(pk=self.instance.pk)

        if existing_slot_bookings.exists():
            self.add_error(
                None,
                "Booking failed: this court and time slot is already taken. Please choose another slot.",
            )

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        try:
            booking.surface = Court.objects.get(number=booking.court_number).surface
        except Court.DoesNotExist:
            pass
        if commit:
            booking.save()
        return booking


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ["booking", "subject", "message"]
        widgets = {
            "subject": forms.TextInput(
                attrs={"placeholder": "Refund request for cancelled booking"}
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Tell us why you need a refund and include any details.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["booking"].required = False
        self.fields["booking"].queryset = Booking.objects.none()
        if user and user.is_authenticated:
            self.fields["booking"].queryset = Booking.objects.filter(
                owner=user
            ).order_by("-date", "-start_time")
        self.fields["booking"].label = "Booking (optional)"
        apply_bootstrap_field_classes(self)


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_field_classes(self)


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_field_classes(self)


def apply_bootstrap_field_classes(form):
    for field in form.fields.values():
        input_type = getattr(field.widget, "input_type", "")
        base_class = (
            "form-check-input" if input_type == "checkbox" else "form-control"
        )
        existing = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{existing} {base_class}".strip()
