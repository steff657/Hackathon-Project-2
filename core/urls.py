from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("courts/", views.courts, name="courts"),
    path("book/", views.book_court, name="book_court"),
    path(
        "my-bookings/<int:booking_id>/edit/",
        views.edit_booking,
        name="edit_booking",
    ),
    path("saved-slots/save/", views.save_slot, name="save_slot"),
    path("saved-slots/<int:slot_id>/unsave/", views.unsave_slot, name="unsave_slot"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("my-bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
]
