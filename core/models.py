from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Court(models.Model):
    class Surface(models.TextChoices):
        HARD = "hard", "Hard"
        CLAY = "clay", "Clay"
        GRASS = "grass", "Grass"

    number = models.PositiveSmallIntegerField(unique=True)
    surface = models.CharField(
        max_length=10,
        choices=Surface.choices,
        default=Surface.HARD,
    )
    indoors = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    maintenance_start = models.DateField(blank=True, null=True)
    maintenance_end = models.DateField(blank=True, null=True)
    maintenance_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Court {self.number}"

    def clean(self):
        if self.maintenance_start and self.maintenance_end:
            if self.maintenance_end < self.maintenance_start:
                raise ValidationError(
                    {"maintenance_end": "Maintenance end date cannot be before start date."}
                )
        if bool(self.maintenance_start) != bool(self.maintenance_end):
            raise ValidationError(
                "Set both maintenance start and end dates, or leave both blank."
            )

    def is_available_on(self, booking_date):
        if not self.is_available:
            return False
        if self.maintenance_start and self.maintenance_end:
            if self.maintenance_start <= booking_date <= self.maintenance_end:
                return False
        return True


class Booking(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class Surface(models.TextChoices):
        HARD = "hard", "Hard"
        CLAY = "clay", "Clay"
        GRASS = "grass", "Grass"

    player_name = models.CharField(max_length=100)
    player_email = models.EmailField()
    date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    court_number = models.PositiveSmallIntegerField(default=1)
    surface = models.CharField(
        max_length=10,
        choices=Surface.choices,
        default=Surface.HARD,
    )
    notes = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        blank=True,
        null=True,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_refund_id = models.CharField(max_length=255, blank=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"Court {self.court_number} - {self.player_name} ({self.date})"


class ContactRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_requests",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        related_name="contact_requests",
        blank=True,
        null=True,
    )
    subject = models.CharField(max_length=120)
    message = models.TextField(max_length=1000)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Contact request #{self.id} by {self.owner}"


class SavedSlot(models.Model):
    class Surface(models.TextChoices):
        HARD = "hard", "Hard"
        CLAY = "clay", "Clay"
        GRASS = "grass", "Grass"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_slots",
    )
    date = models.DateField()
    start_time = models.TimeField()
    court_number = models.PositiveSmallIntegerField()
    surface = models.CharField(
        max_length=10,
        choices=Surface.choices,
        default=Surface.HARD,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time", "court_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "date", "start_time", "court_number"],
                name="unique_saved_slot_per_user",
            )
        ]

    def __str__(self):
        return (
            f"{self.owner} saved Court {self.court_number} "
            f"on {self.date} at {self.start_time}"
        )


class About(models.Model):
    title = models.CharField(max_length=100, default="About Us")
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
