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
    path('api/get-cities/', views.get_cities, name='get_cities'),
    path('api/get-all-venues/', views.get_all_venues, name='get_all_venues'),
    path('api/get-booked-dates/<int:venue_id>/', views.get_booked_dates, name='get_booked_dates'),
    path('api/book-venue/', views.book_venue, name='book_venue'),
    path('owner/booking-details/', views.owner_booking_details, name='owner_booking_details'),
    path('user/booked-venues/',views.user_booked_venues,name='user_booked_venues'),
    path("api/cancel-booking/<int:booking_id>/",views.cancel_booking,name="cancel_booking"),
    path("api/add-feedback/",views.add_feedback,name="add_feedback"),
    path("api/get-feedbacks/<int:venue_id>/",views.get_feedbacks,name="get_feedbacks"),
    path("owner/feedbacks/",views.owner_feedbacks,name="owner_feedbacks"),
]