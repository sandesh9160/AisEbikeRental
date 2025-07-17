from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User as AuthUser
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import EBike, User,Review
from .forms import SignUpForm, ProfileUpdateForm
from django.views.decorators.csrf import csrf_protect

def home(request):
    ebikes = EBike.objects.filter(is_available=True)[:5]
    return render(request, 'core/home.html', {'ebikes': ebikes})

@csrf_protect
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'is_rider') and user.is_rider:
                return redirect('rider_dashboard')
            elif hasattr(user, 'is_vehicle_provider') and user.is_vehicle_provider:
                return redirect('vehicle_provider_dashboard')
            elif user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

@csrf_protect
def submit_review(request):
    if request.method == "POST":
        name = request.POST.get("name")
        rating = request.POST.get("rating")
        message = request.POST.get("message")
        Review.objects.create(name=name, rating=rating, message=message)
        return redirect('home')

def about(request):
    return render(request, 'core/about.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_rider:
                return redirect('rider_dashboard')
            elif user.is_vehicle_provider:
                return redirect('vehicle_provider_dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

def ebikes(request):
    ebikes = EBike.objects.filter(is_available=True)
    return render(request, 'core/ebikes.html', {'ebikes': ebikes})

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            # Redirect to the correct dashboard based on user type
            if request.user.is_rider:
                return redirect('rider_dashboard')
            elif request.user.is_vehicle_provider:
                return redirect('vehicle_provider_dashboard')
            elif request.user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'core/profile_update.html', {'form': form})

