from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, UserUpdateForm, UserProfileForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save User
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Update created profile
            profile = user.profile
            profile.phone = form.cleaned_data['phone']
            profile.age = form.cleaned_data['age']
            profile.gender = form.cleaned_data['gender']
            profile.blood_group = form.cleaned_data['blood_group']
            profile.address = form.cleaned_data['address']
            profile.emergency_contact = form.cleaned_data['emergency_contact']
            profile.save()
            
            messages.success(request, "Account created successfully! You are now logged in.")
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = RegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=request.user.profile)
        
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/profile.html', context)


import os
import requests
import uuid
from urllib.parse import urlencode
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

def google_login(request):
    # State token to prevent CSRF
    state = uuid.uuid4().hex
    request.session['google_oauth_state'] = state
    
    # Construct the callback URI dynamically based on current host
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    params = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    authorization_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(authorization_url)

def google_callback(request):
    # Verify state parameter to prevent CSRF
    state = request.GET.get('state')
    session_state = request.session.pop('google_oauth_state', None)
    
    if not state or state != session_state:
        messages.error(request, "Authentication failed: Invalid state parameter.")
        return redirect('login')
        
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error or not code:
        messages.error(request, f"Authentication failed: {error or 'No code provided.'}")
        return redirect('login')
        
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    # Exchange auth code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            messages.error(request, "Failed to retrieve access token from Google.")
            return redirect('login')
            
        # Get user info
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {'Authorization': f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers, timeout=10)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        email = user_info.get('email')
        if not email:
            messages.error(request, "Failed to retrieve email from Google user profile.")
            return redirect('login')
            
        # Check if user already exists
        user = User.objects.filter(email=email).first()
        
        if user:
            # Existing user - log them in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome back, {user.username} (via Google)!")
        else:
            # New user - create them
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            
            # Generate a unique username based on email
            username_base = email.split('@')[0]
            # Replace dots/special chars which might not be allowed in Django username
            username_base = "".join(c for c in username_base if c.isalnum() or c in ['_', '-'])
            
            username = username_base
            while User.objects.filter(username=username).exists():
                username = f"{username_base}_{get_random_string(4).lower()}"
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password=get_random_string(32), # Random unusable password
                first_name=first_name,
                last_name=last_name
            )
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Successfully registered and logged in as {username} (via Google)!")
            
        return redirect('home')
        
    except requests.RequestException as e:
        messages.error(request, f"Google OAuth communication failed: {str(e)}")
        return redirect('login')

