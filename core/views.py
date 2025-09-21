from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User as AuthUser
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import EBike, User, Review, ContactMessage
from .forms import SignUpForm, ProfileUpdateForm, CustomPasswordResetForm, PasswordResetConfirmForm
from django.views.decorators.csrf import csrf_protect
from django.template.loader import render_to_string

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
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            # If AJAX, return JSON success without redirect
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!',
                    'username': user.username,
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'profile_image_url': (user.profile_image.url if user.profile_image else ''),
                })
            messages.success(request, 'Profile updated successfully!')
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
            if is_ajax:
                html = render_to_string('core/_profile_update_form.html', {'form': form}, request=request)
                return JsonResponse({'success': False, 'html': html}, status=400)
    else:
        form = ProfileUpdateForm(instance=request.user)
        if is_ajax:
            html = render_to_string('core/_profile_update_form.html', {'form': form}, request=request)
            return JsonResponse({'success': True, 'html': html})
    return render(request, 'core/profile_update.html', {'form': form})


@csrf_protect
def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Send email
                subject = 'Password Reset Request - AI E-Bike Rental'
                message = f"""
                Hello {user.username},
                
                You have requested to reset your password for your AI E-Bike Rental account.
                
                Please click the link below to reset your password:
                {reset_url}
                
                If you did not request this password reset, please ignore this email.
                
                This link will expire in 24 hours.
                
                Best regards,
                AI E-Bike Rental Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'Password reset email sent! Please check your inbox.')
                except Exception as e:
                    messages.error(request, 'Failed to send email. Please try again later.')
                    print(f"Email error: {e}")
                
                return redirect('password_reset_done')
                
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'core/password_reset_form.html', {'form': form})


@csrf_protect
def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
                return redirect('login')
        else:
            form = PasswordResetConfirmForm()
        
        return render(request, 'core/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('password_reset_request')


def password_reset_done(request):
    return render(request, 'core/password_reset_done.html')


def contact(request):
    """Contact Us page: saves message to DB and emails site owner."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not (name and email and subject and message):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'core/contact.html', {
                'prefill': {'name': name, 'email': email, 'subject': subject, 'message': message}
            })

        # Save to DB
        ContactMessage.objects.create(name=name, email=email, subject=subject, message=message)

        # Send email to admin/owner
        to_email = getattr(settings, 'CONTACT_RECEIVER_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if to_email:
            try:
                send_mail(
                    subject=f"[Contact] {subject}",
                    message=f"From: {name} <{email}>\n\n{message}",
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', email),
                    recipient_list=[to_email],
                    fail_silently=True,
                )
            except Exception:
                # Silently ignore email failures but still accept the submission
                pass

        messages.success(request, 'Thanks for contacting us! We will get back to you soon.')
        return redirect('contact')

    return render(request, 'core/contact.html')

