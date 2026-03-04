from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("courts/", views.courts, name="courts"),
    path("book/", views.book_court, name="book_court"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("my-bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
]
