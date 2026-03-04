from django import forms
from django.core.exceptions import ValidationError

from .models import Booking, Court


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
            "start_time": forms.TimeInput(attrs={"type": "time"}),
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
        court_number = cleaned_data.get("court_number")

        if not booking_date or court_number is None:
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
