from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, Venue, VenueImage, Booking
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def login_view(request):
    # We purposefully do NOT redirect authenticated users here anymore
    # so they always land on the sign-in page when opening the site.

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        errors = {}

        if not username:
            errors['username'] = 'Username is required.'
        if not password:
            errors['password'] = 'Password is required.'

        user_obj = None
        if username:
            try:
                user_obj = User.objects.get(username=username)
            except User.DoesNotExist:
                if 'username' not in errors:
                    errors['username'] = 'Account does not exist. Please sign up first.'

        # Only check password if username was provided and user exists and password was provided
        if user_obj and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                errors['password'] = 'Incorrect password. Please try again.'

        # If there are any errors, pass them explicitly to the template
        if errors:
            return render(request, 'signin.html', {
                'username': username,
                'username_error': errors.get('username'),
                'password_error': errors.get('password')
            })

    return render(request, 'signin.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('confirmPassword')
        role = request.POST.get('roleSelect')

        # Collect all validation errors
        errors = {}

        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken. Please choose a different username.'

        if password != password2:
            errors['confirmPassword'] = 'Passwords do not match.'

        if User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered. Please use a different email.'

        if errors:
            return render(request, 'signup.html', {
                'username': username,
                'email': email,
                'selected_role': role,
                'password': password,
                'confirmPassword': password2,
                'username_error': errors.get('username'),
                'email_error': errors.get('email'),
                'confirm_error': errors.get('confirmPassword')
            })

        # Create new user
        user = User(email=email, username=username, role=role)
        user.set_password(password)
        user.save()

        # Auto login after signup
        login(request, user)
        return redirect('dashboard')

    return render(request, 'signup.html')


@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    context = {
        'full_name': user.username,
        'role': user.role
    }

    role = (user.role or '').strip().lower()
    if role in ['venue_owner', 'venue owner', 'owner', 'venueowner'] or user.is_superuser or user.is_staff:
        return render(request, 'owner_dashboard.html', context)
    else:
        return render(request, 'customer_dashboard.html', context)


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')



# Forgot / Reset password  (username passed as hidden form field — no session)


def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        try:
            User.objects.get(username=username, email=email)
            messages.success(request, 'Verification successful! Please enter your new password.')
            # Render reset page directly — pass username via context (→ hidden field in form)
            return render(request, 'reset_password.html', {'username': username})
        except User.DoesNotExist:
            messages.error(request, 'Username and email do not match. Please try again.')
            return render(request, 'forgot_password.html', {
                'username': username,
                'email': email
            })

    return render(request, 'forgot_password.html')


def reset_password_view(request):
    if request.method == 'POST':
        # Username submitted via hidden field in the reset_password form
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('confirmPassword')

        if not username:
            messages.error(request, 'Please verify your identity first.')
            return redirect('forgot_password')

        if password != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'reset_password.html', {'username': username})

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'reset_password.html', {'username': username})

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful! Please sign in with your new password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')

    # Direct GET access — send back to forgot password
    messages.error(request, 'Please verify your identity first.')
    return redirect('forgot_password')


# ---------------------------------------------------------------------------
# Venue API views
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def save_venue(request):
    if request.method == 'POST':
        try:
            owner = request.user

            data = request.POST
            venue_id = data.get('venue_id')  # For editing

            if venue_id:
                venue = Venue.objects.get(id=venue_id, owner=owner)
            else:
                venue = Venue(owner=owner)
            venue.name = data.get('venueName')
            venue.owner_name = data.get('ownerName')
            venue.address = data.get('venueAddress')
            venue.city = data.get('city')
            venue.state = data.get('state')
            venue.capacity = data.get('capacity')
            venue.total_area = data.get('totalArea')
            venue.parking_area = data.get('parkingArea')
            venue.venue_type = data.get('venueType')
            venue.facilities = data.get('facilities')
            venue.instructions = data.get('instructions')
            venue.price = data.get('price')
            venue.contact1 = data.get('contact1')
            venue.contact2 = data.get('contact2')

            venue.save()

            # Handle deletions of specific old images
            deleted_image_urls = request.POST.getlist('deleted_images[]')
            if deleted_image_urls and venue_id:
                # The frontend passes the exact URL of the image to delete
                for img_url in deleted_image_urls:
                    # Find and delete the image matching the URL for this venue
                    img_to_delete = venue.images.filter(image__contains=img_url.split('/media/')[-1]).first()
                    if img_to_delete:
                        img_to_delete.delete()

            # Handle new images (Append only)
            images = request.FILES.getlist('images')
            if images:
                # Check current count to enforce max 10 server-side
                current_count = venue.images.count()
                if current_count + len(images) > 10:
                    return JsonResponse({'status': 'error', 'message': f'Cannot exceed 10 images. You currently have {current_count}.'}, status=400)
                
                for image in images:
                    VenueImage.objects.create(venue=venue, image=image)

            return JsonResponse({'status': 'success', 'message': 'Venue saved successfully!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url='login')
def get_venues(request):
    if request.method == 'GET':
        owner = request.user
        venues = Venue.objects.filter(owner=owner)
        venues_data = []
        for v in venues:
            venues_data.append({
                'id': v.id,
                'venueName': v.name,
                'ownerName': v.owner_name,
                'venueAddress': v.address,
                'city': v.city,
                'state': v.state,
                'capacity': v.capacity,
                'totalArea': v.total_area,
                'parkingArea': v.parking_area,
                'venueType': v.venue_type,
                'facilities': v.facilities,
                'instructions': v.instructions,
                'price': str(v.price),
                'contact1': v.contact1,
                'contact2': v.contact2,
                'imageCount': v.images.count(),
                'images': [img.image.url for img in v.images.all()]
            })

        return JsonResponse({'status': 'success', 'venues': venues_data})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def get_all_venues(request):
    if request.method == 'GET':
        venues = Venue.objects.all()
        venues_data = []
        for v in venues:
            venues_data.append({
                'id': v.id,
                'venueName': v.name,
                'ownerName': v.owner_name,
                'venueAddress': v.address,
                'city': v.city,
                'state': v.state,
                'capacity': v.capacity,
                'totalArea': v.total_area,
                'parkingArea': v.parking_area,
                'venueType': v.venue_type,
                'facilities': v.facilities,
                'instructions': v.instructions,
                'price': str(v.price),
                'contact1': v.contact1,
                'contact2': v.contact2,
                'imageCount': v.images.count(),
                'images': [img.image.url for img in v.images.all()]
            })

        return JsonResponse({'status': 'success', 'venues': venues_data})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url='login')
def get_booked_dates(request, venue_id):
    if request.method == 'GET':
        try:
            bookings = Booking.objects.filter(venue_id=venue_id)
            # Return list of ISO formatted date strings: ['2023-10-25', '2023-10-26']
            booked_dates = [booking.date.isoformat() for booking in bookings]
            return JsonResponse({'status': 'success', 'booked_dates': booked_dates})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url='login')
def book_venue(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            venue_id = data.get('venue_id')
            date_str = data.get('date')
            special_requirements = data.get('special_requirements', '')

            if not venue_id or not date_str:
                return JsonResponse({'status': 'error', 'message': 'Missing venue or date.'}, status=400)

            # Flatpickr sends multiple dates as a comma-separated string: "2023-10-25, 2023-10-26"
            date_strings = [d.strip() for d in date_str.split(',') if d.strip()]
            
            if not date_strings:
                 return JsonResponse({'status': 'error', 'message': 'No valid dates provided.'}, status=400)

            venue = Venue.objects.get(id=venue_id)
            bookings_to_create = []

            for ds in date_strings:
                booking_date = datetime.strptime(ds, '%Y-%m-%d').date()
                
                # Check if date is in the past
                if booking_date < datetime.now().date():
                     return JsonResponse({'status': 'error', 'message': f'Cannot book a date in the past: {ds}'}, status=400)

                # Check if already booked
                if Booking.objects.filter(venue_id=venue_id, date=booking_date).exists():
                    return JsonResponse({'status': 'error', 'message': f'Date {ds} is already booked.'}, status=400)
                
                bookings_to_create.append(Booking(
                    venue=venue, 
                    user=request.user, 
                    date=booking_date,
                    special_requirements=special_requirements
                ))

            # Create bookings in bulk if all validations pass
            Booking.objects.bulk_create(bookings_to_create)

            return JsonResponse({'status': 'success', 'message': f'Venue booked successfully for {len(bookings_to_create)} day(s)!'})

        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        except Venue.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Venue not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required(login_url='login')
def owner_booking_details(request):

    owner = request.user

    bookings = Booking.objects.filter(
        venue__owner=owner
    ).select_related('venue', 'user')

    return render(
        request,
        'owner_booking_details.html',
        {'bookings': bookings}
    )

# @login_required(login_url='login')
# def user_booked_venues(request):

#     bookings = Booking.objects.filter(
#         user=request.user
#     ).select_related('venue')

#     return render(
#         request,
#         'user_booked_venues.html',
#         {'bookings': bookings}
#     )
@login_required(login_url='login')
def user_booked_venues(request):

    bookings = Booking.objects.filter(user=request.user)

    context = {
        'bookings': bookings,
        'full_name': request.user.username
    }

    return render(request, 'user_booked_venues.html', context)
@login_required(login_url='login')
def cancel_booking(request, booking_id):

    if request.method == "POST":

        try:

            booking = Booking.objects.get(
                id=booking_id,
                user=request.user
            )

            booking.delete()

            return JsonResponse({
                "status": "success",
                "message": "Booking cancelled"
            })

        except Booking.DoesNotExist:

            return JsonResponse({
                "status": "error",
                "message": "Booking not found"
            }, status=404)

    return JsonResponse({
        "status": "error",
        "message": "Invalid request"
    }, status=400)