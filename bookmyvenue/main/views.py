from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import User, Venue, VenueImage

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                request.session['user_id'] = user.id
                request.session['user_name'] = user.username
                request.session['user_role'] = user.role.strip().lower()
                
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Incorrect password. Please try again.')
                return render(request, 'signin.html', {
                    'username': username
                })
        except User.DoesNotExist:
            messages.error(request, 'Account does not exist. Please sign up first.')
            return render(request, 'signin.html', {
                'username': username
            })
    
    return render(request, 'signin.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('confirmPassword')
        role = request.POST.get('roleSelect')
        
        # Collect all validation errors
        errors = []
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken. Please choose a different username.')
        
        # Check if passwords match
        if password != password2:
            errors.append('Passwords do not match.')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered. Please use a different email.')
        
        # If there are any errors, display them all together
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'signup.html', {
                'username': username,
                'email': email,
                'selected_role': role,
                'password': password,
                'confirmPassword': password2
            })
        
        # Create new user
        user = User(
            email=email,
            username=username,
            role=role
        )
        user.set_password(password)
        user.save()
        
        # Auto login after signup
        request.session['user_id'] = user.id
        request.session['user_name'] = user.username
        request.session['user_role'] = user.role.strip().lower()
        
        messages.success(request, f'Account created successfully! Welcome, {username}!')
        return redirect('dashboard')
    
    return render(request, 'signup.html')

def dashboard_view(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    context = {
        'full_name': request.session.get('user_name'),
        'role': request.session.get('user_role')
    }
    
    role = (context.get('role') or '').strip().lower()
    if role in ['venue_owner', 'venue owner', 'owner', 'venueowner']:
        return render(request, 'owner_dashboard.html', context)
    else:
        return render(request, 'customer_dashboard.html', context)

def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        # Verify that username and email match
        try:
            user = User.objects.get(username=username, email=email)
            # Store username in session for password reset
            request.session['reset_username'] = username
            messages.success(request, 'Verification successful! Please enter your new password.')
            return redirect('reset_password')
        except User.DoesNotExist:
            messages.error(request, 'Username and email do not match. Please try again.')
            return render(request, 'forgot_password.html', {
                'username': username,
                'email': email
            })
    
    return render(request, 'forgot_password.html')

def reset_password_view(request):
    # Check if user has verified their identity
    if 'reset_username' not in request.session:
        messages.error(request, 'Please verify your identity first.')
        return redirect('forgot_password')
    
    username = request.session.get('reset_username')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('confirmPassword')
        
        # Validate passwords match
        if password != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'reset_password.html', {'username': username})
        
        # Validate password length
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'reset_password.html', {'username': username})
        
        # Update password
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            
            # Clear session
            del request.session['reset_username']
            
            messages.success(request, 'Password reset successful! Please sign in with your new password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')
    
    return render(request, 'reset_password.html', {'username': username})

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('login')

def save_venue(request):
    if request.method == 'POST' and 'user_id' in request.session:
        try:
            owner = User.objects.get(id=request.session['user_id'])
            
            # Extract data
            data = request.POST
            venue_id = data.get('venue_id') # For editing
            
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
            
            # Handle Images
            images = request.FILES.getlist('images')
            if images:
                # Optionally, delete old images on update
                if venue_id:
                    venue.images.all().delete()
                    
                for image in images:
                    VenueImage.objects.create(venue=venue, image=image)
                    
            return JsonResponse({'status': 'success', 'message': 'Venue saved successfully!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def get_venues(request):
    if request.method == 'GET' and 'user_id' in request.session:
        owner = User.objects.get(id=request.session['user_id'])
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