from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import EBike, User,Review
from .forms import SignUpForm
from django.views.decorators.csrf import csrf_protect

def home(request):
    ebikes = EBike.objects.filter(is_available=True)[:5]
    return render(request, 'core/home.html', {'ebikes': ebikes})

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

