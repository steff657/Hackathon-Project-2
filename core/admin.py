from django.contrib import admin

from .models import Booking, Court


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("number", "surface", "is_available", "maintenance_start", "maintenance_end")
    list_filter = ("is_available", "surface", "indoors")
    list_editable = ("is_available",)
    search_fields = ("=number", "maintenance_reason")
    ordering = ("number",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "court", "date", "time_slot")
    list_filter = ("date", "court_number", "player_name")
    search_fields = ("player_email", "player_name")
    ordering = ("date", "start_time")

    @admin.display(ordering="player_name", description="User")
    def user(self, obj):
        return f"{obj.player_name} ({obj.player_email})"

    @admin.display(ordering="court_number", description="Court")
    def court(self, obj):
        return f"Court {obj.court_number}"

    @admin.display(ordering="start_time", description="Time Slot")
    def time_slot(self, obj):
        return obj.start_time
