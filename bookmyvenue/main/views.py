from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
import re

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                request.session['user_id'] = user.id
                request.session['user_name'] = user.username
                request.session['user_role'] = user.role
                
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
        request.session['user_role'] = user.role
        
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
    
    if context['role'] == 'venue_owner':
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