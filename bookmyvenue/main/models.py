from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model extending AbstractUser with a role field."""
    role = models.CharField(
        max_length=15,
        choices=[
            ('venue_owner', 'Venue Owner'),
            ('user', 'User'),
        ],
        default='user'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Venue(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venues')
    name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    capacity = models.IntegerField()
    total_area = models.CharField(max_length=50, blank=True, null=True)
    parking_area = models.CharField(max_length=50, blank=True, null=True)
    venue_type = models.CharField(max_length=20, choices=[('AC', 'AC'), ('Non-AC', 'Non-AC'), ('Both', 'Both')])
    facilities = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    contact1 = models.CharField(max_length=15)
    contact2 = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class VenueImage(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venue_images/')

    def __str__(self):
        return f"Image for {self.venue.name}"

class Booking(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    special_requirements = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent double booking the same venue on the same date at the DB level
        unique_together = ('venue', 'date')

    def __str__(self):
        return f"Booking: {self.venue.name} by {self.user.username} on {self.date}"