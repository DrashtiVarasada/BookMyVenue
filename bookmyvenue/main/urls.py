from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),  
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    path('api/save-venue/', views.save_venue, name='save_venue'),
    path('api/get-venues/', views.get_venues, name='get_venues'),
    path('api/get-all-venues/', views.get_all_venues, name='get_all_venues'),
    path('api/get-booked-dates/<int:venue_id>/', views.get_booked_dates, name='get_booked_dates'),
    path('api/book-venue/', views.book_venue, name='book_venue'),
]