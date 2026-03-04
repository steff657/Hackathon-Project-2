from datetime import date, time

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .admin import BookingAdmin, CourtAdmin
from .models import Booking, Court


class BookingAdminTests(TestCase):
    def setUp(self):
        court = Court.objects.first()
        self.booking = Booking.objects.create(
            player_name="Alice Example",
            player_email="alice@example.com",
            date=date(2026, 3, 5),
            start_time=time(10, 0),
            court_number=court.number,
        )
        user_model = get_user_model()
        self.superuser = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-pass-123",
        )
        self.user = user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="member-pass-123",
        )

    def test_booking_registered_in_admin(self):
        self.assertIn(Booking, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Booking], BookingAdmin)

    def test_booking_admin_configuration(self):
        model_admin = admin.site._registry[Booking]
        self.assertEqual(model_admin.list_display, ("user", "court", "date", "time_slot"))
        self.assertEqual(model_admin.list_filter, ("date", "court_number", "player_name"))
        self.assertEqual(model_admin.search_fields, ("player_email", "player_name"))
        self.assertEqual(model_admin.ordering, ("date", "start_time"))

    def test_admin_can_access_booking_list_and_detail(self):
        self.client.force_login(self.superuser)

        changelist_url = reverse("admin:core_booking_changelist")
        change_url = reverse("admin:core_booking_change", args=[self.booking.pk])

        changelist_response = self.client.get(changelist_url)
        change_response = self.client.get(change_url)

        self.assertEqual(changelist_response.status_code, 200)
        self.assertEqual(change_response.status_code, 200)

    def test_non_admin_cannot_access_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)


class CourtAdminTests(TestCase):
    def test_court_registered_in_admin(self):
        self.assertIn(Court, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Court], CourtAdmin)

    def test_court_admin_configuration(self):
        model_admin = admin.site._registry[Court]
        self.assertEqual(
            model_admin.list_display,
            ("number", "surface", "is_available", "maintenance_start", "maintenance_end"),
        )
        self.assertEqual(model_admin.list_filter, ("is_available", "surface", "indoors"))
        self.assertEqual(model_admin.list_editable, ("is_available",))


class AvailabilityBookingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="booking-owner",
            email="owner@example.com",
            password="owner-pass-123",
        )
        self.available_court = Court.objects.create(
            number=10,
            surface=Court.Surface.HARD,
            is_available=True,
        )
        self.unavailable_court = Court.objects.create(
            number=11,
            surface=Court.Surface.CLAY,
            is_available=False,
            maintenance_reason="Local event",
        )
        self.maintenance_court = Court.objects.create(
            number=12,
            surface=Court.Surface.GRASS,
            is_available=True,
            maintenance_start=date(2026, 3, 10),
            maintenance_end=date(2026, 3, 12),
            maintenance_reason="Net replacement",
        )

    def test_unavailable_court_is_not_shown_in_courts_page(self):
        response = self.client.get(reverse("courts"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Court 10")
        self.assertNotContains(response, "Court 11")

    def test_cannot_book_unavailable_court(self):
        response = self.client.post(
            reverse("book_court"),
            {
                "player_name": "Player One",
                "player_email": "player@example.com",
                "date": "2026-03-11",
                "start_time": "10:00",
                "duration_minutes": 60,
                "court_number": 11,
                "notes": "Test booking",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Court is unavailable")
        self.assertEqual(Booking.objects.count(), 0)

    def test_cannot_book_court_during_maintenance_window(self):
        response = self.client.post(
            reverse("book_court"),
            {
                "player_name": "Player Two",
                "player_email": "player2@example.com",
                "date": "2026-03-11",
                "start_time": "11:00",
                "duration_minutes": 60,
                "court_number": 12,
                "notes": "Test booking",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "under maintenance")
        self.assertEqual(Booking.objects.count(), 0)

    def test_existing_bookings_stay_visible_even_if_court_becomes_unavailable(self):
        Booking.objects.create(
            player_name="Legacy Booking",
            player_email="legacy@example.com",
            date=date(2026, 3, 15),
            start_time=time(9, 0),
            court_number=self.available_court.number,
            surface=self.available_court.surface,
            owner=self.owner,
        )
        self.available_court.is_available = False
        self.available_court.save()

        self.client.force_login(self.owner)
        response = self.client.get(reverse("my_bookings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Legacy Booking")

    def test_booking_page_shows_clear_message_if_no_courts_available(self):
        Court.objects.update(is_available=False)
        response = self.client.get(reverse("book_court"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No courts are available right now")


class CancelBookingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner-user",
            email="owner.user@example.com",
            password="owner-pass-123",
        )
        self.other_user = user_model.objects.create_user(
            username="other-user",
            email="other.user@example.com",
            password="other-pass-123",
        )
        self.court = Court.objects.first()
        self.owner_booking = Booking.objects.create(
            player_name="Owner Player",
            player_email="owner.user@example.com",
            date=date(2026, 3, 20),
            start_time=time(10, 0),
            court_number=self.court.number,
            surface=self.court.surface,
            owner=self.owner,
        )
        self.other_booking = Booking.objects.create(
            player_name="Other Player",
            player_email="other.user@example.com",
            date=date(2026, 3, 21),
            start_time=time(11, 0),
            court_number=self.court.number,
            surface=self.court.surface,
            owner=self.other_user,
        )

    def test_logged_in_user_only_sees_own_bookings(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("my_bookings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner Player")
        self.assertNotContains(response, "Other Player")
        self.assertContains(response, "Cancel")

    def test_owner_can_cancel_booking(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("cancel_booking", args=[self.owner_booking.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("my_bookings"))
        self.assertFalse(Booking.objects.filter(pk=self.owner_booking.pk).exists())
        self.assertContains(response, "Booking cancelled successfully.")

    def test_user_cannot_cancel_another_users_booking(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("cancel_booking", args=[self.other_booking.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Booking.objects.filter(pk=self.other_booking.pk).exists())

    def test_manual_url_get_cannot_delete_another_users_booking(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("cancel_booking", args=[self.other_booking.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Booking.objects.filter(pk=self.other_booking.pk).exists())
