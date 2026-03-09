from django.contrib import admin
from .models import User, Venue, VenueImage, Booking

admin.site.register(User)
admin.site.register(Venue)
admin.site.register(VenueImage)
admin.site.register(Booking)
