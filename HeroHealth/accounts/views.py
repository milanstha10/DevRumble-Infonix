import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, UserUpdateForm, UserProfileForm
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from .models import ensure_user_profile

logger = logging.getLogger(__name__)

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
            profile = ensure_user_profile(user)
            profile.phone = form.cleaned_data['phone']
            profile.age = form.cleaned_data['age']
            profile.gender = form.cleaned_data['gender']
            profile.blood_group = form.cleaned_data['blood_group']
            profile.address = form.cleaned_data['address']
            profile.emergency_contact = form.cleaned_data['emergency_contact']
            profile.email_verified = False
            profile.save()
            
            # Create verification token & link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build absolute verification URI
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            verification_link = f"{protocol}://{domain}{reverse('verify_email', kwargs={'uidb64': uid, 'token': token})}"
            
            # Send verification email
            subject = "Verify your HeroHealth Email"
            message = (
                f"Hi {user.username},\n\n"
                f"Thank you for registering at HeroHealth! Please click the link below to verify your email:\n"
                f"{verification_link}\n\n"
                f"If you did not create this account, please ignore this email."
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False
                )
                messages.success(request, "Registration successful! A verification email has been sent. Please verify your email before logging in.")
            except Exception as e:
                messages.warning(request, f"Account created, but we failed to send a verification email: {str(e)}")
            
            return redirect('login')
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
                # Check email verification (bypass for admin/staff)
                is_verified = ensure_user_profile(user).email_verified
                    
                if not is_verified and not user.is_superuser and not user.is_staff:
                    messages.error(request, "Please verify your email first. A verification link was sent to your email.")
                    return redirect('login')
                    
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
        p_form = UserProfileForm(request.POST, instance=ensure_user_profile(request.user))
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=ensure_user_profile(request.user))
        
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
            # Google log ins are auto-verified
            profile = ensure_user_profile(user)
            if not profile.email_verified:
                profile.email_verified = True
                profile.save()
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
                
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=get_random_string(32), # Random unusable password
                    first_name=first_name,
                    last_name=last_name
                )
                # Auto-verify Google user profile
                profile = ensure_user_profile(user)
                profile.email_verified = True
                profile.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Successfully registered and logged in as {username} (via Google)!")
            
        return redirect('home')
        
    except requests.RequestException:
        logger.exception("Google OAuth communication failed")
        messages.error(request, "Google sign-in could not be completed. Please try again.")
        return redirect('login')
    except Exception:
        logger.exception("Google OAuth callback failed")
        messages.error(request, "We could not finish setting up your account. Please try again.")
        return redirect('login')


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        profile = ensure_user_profile(user)
        profile.email_verified = True
        profile.save()
        messages.success(request, "Your email has been verified! You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect('login')

