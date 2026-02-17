# bookmyvenue/main/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=128)  # Will store hashed password
    role = models.CharField(
        max_length=15,
        choices=[
            ('venue_owner', 'Venue Owner'),
            ('user', 'User')
        ],
        default='user'
    )
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.username} ({self.role})"