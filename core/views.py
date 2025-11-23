"""
Views for the core application of the AisEbikeRental system.
"""

# Django imports
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.models import User as AuthUser
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.template.loader import render_to_string

# Local imports
from .models import EBike, User, Review, Testimonial, ContactMessage, Favorite
from .forms import SignUpForm, ProfileUpdateForm, CustomPasswordResetForm, PasswordResetConfirmForm, ReviewForm
from .utils import chatbot_response, get_bike_recommendations, generate_role_based_questions

def home(request):
    """
    Home page view displaying featured available e-bikes and testimonials.

    Shows up to 5 available e-bikes and active testimonials on the main page.
    """
    ebikes = EBike.objects.filter(is_available=True)[:5]
    testimonials = Testimonial.objects.filter(is_active=True).order_by('sort_order')[:6]
    return render(request, 'core/home.html', {
        'ebikes': ebikes,
        'testimonials': testimonials
    })


@csrf_protect
def custom_login(request):
    """
    Custom login view with role-based redirection.

    Authenticates user and redirects to appropriate dashboard
    based on user role (rider, provider, or staff).
    """
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
    """
    Handle review submission from users.

    Validates review form and saves review to database,
    associating with authenticated user if available.
    """
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            if request.user.is_authenticated:
                review.user = request.user
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('home')
        else:
            # If form is not valid, show error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('home')

    # If not a POST request, redirect to home
    return redirect('home')


def about(request):
    """
    About page view.

    Displays information about the e-bike rental service.
    """
    return render(request, 'core/about.html')


def signup(request):
    """
    User registration view.

    Creates new user account and automatically logs them in,
    then redirects to appropriate dashboard based on user role.
    """
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
    """
    E-bikes listing page view.

    Displays all available e-bikes with user's favorite selections
    highlighted for authenticated users.
    """
    ebikes = EBike.objects.filter(is_available=True)
    # Get user's favorite bike IDs if logged in
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('ebike_id', flat=True))
    return render(request, 'core/ebikes.html', {
        'ebikes': ebikes,
        'favorite_ids': favorite_ids
    })

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
                        fail_silently=False,  # In production, raise exceptions for proper error handling
                    )
                    messages.success(request, 'Password reset email sent! Please check your inbox.')
                except Exception as e:
                    # Log the error for production monitoring
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send password reset email to {email}: {str(e)}")

                    if settings.DEBUG:
                        # In development, show the error
                        messages.error(request, f'Failed to send email: {str(e)}')
                    else:
                        # In production, show generic message but log the error
                        messages.error(request, 'Failed to send email. Please contact support if the problem persists.')
                
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


@csrf_exempt
@login_required
def toggle_favorite(request, ebike_id):
    """Toggle favorite status for an e-bike"""
    if request.method == 'POST':
        try:
            ebike = EBike.objects.get(id=ebike_id)
            favorite, created = Favorite.objects.get_or_create(user=request.user, ebike=ebike)
            
            if not created:
                # Already favorited, so remove it
                favorite.delete()
                is_favorite = False
            else:
                is_favorite = True
            
            return JsonResponse({
                'success': True,
                'is_favorite': is_favorite,
                'message': 'Added to favorites' if is_favorite else 'Removed from favorites'
            })
        except EBike.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'E-bike not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def my_favorites(request):
    """View user's favorite e-bikes"""
    favorites = Favorite.objects.filter(user=request.user).select_related('ebike')
    favorite_ebikes = [favorite.ebike for favorite in favorites]
    return render(request, 'core/favorites.html', {
        'favorite_ebikes': favorite_ebikes,
        'favorites_count': len(favorite_ebikes)
    })


def contact(request):
    """
    Contact Us page: saves message to DB and emails both admin and user.

    Stores contact form submission in database, emails admin for processing,
    and sends acknowledgment email to the person who submitted the form.
    """
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

        # Send email to admin/owner for processing - PRODUCTION EMAIL LOGIC
        admin_email = getattr(settings, 'CONTACT_RECEIVER_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        admin_email_sent = False
        if admin_email:
            try:
                send_mail(
                    subject=f"[Contact Form] {subject}",
                    message=f"""From: {name} <{email}>
Subject: {subject}

Message:
{message}

---
This message was submitted via the contact form on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,  # DON'T silently fail in production!
                )
                admin_email_sent = True
            except Exception as e:
                # Log error in production but still accept the submission
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send admin contact email: {str(e)}")
                # Continue processing instead of failing completely

        # Send acknowledgment email to the person who submitted the form
        acknowledgment_email_sent = False
        try:
            acknowledgment_subject = f"We Received Your Message: {subject}"
            acknowledgment_message = f"""
Dear {name},

Thank you for contacting AIS E-bike Rental! We have received your message and our team will respond within 24-48 hours.

Your inquiry details:
Subject: {subject}
Message: {message}

If you have any urgent questions, please call us at +91 XXXXX XXXXX.

Best regards,
AIS E-bike Rental Support Team
support@aisebikerental.com
+91 XXXXX XXXXX

---
This is an automated response confirming receipt of your message sent on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}.
""".strip()

            send_mail(
                subject=acknowledgment_subject,
                message=acknowledgment_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,  # DON'T silently fail user acknowledgments!
            )
            acknowledgment_email_sent = True
        except Exception as e:
            # Log error but don't fail the submission
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send user acknowledgment email: {str(e)}")

        messages.success(request, 'Thanks for contacting us! We\'ve received your message and sent you an acknowledgment email.')
        return redirect('contact')

    return render(request, 'core/contact.html')


@csrf_exempt
def chatbot_view(request):
    """
    AI Chatbot view for customer support using Gemini API.

    Handles both GET (for display) and POST (for chat) requests.
    """
    if request.method == 'POST':
        # Handle JSON data from chat widget
        import json
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            context_type = data.get('context', 'general')
        except (json.JSONDecodeError, TypeError):
            # Fallback for form data
            user_message = request.POST.get('message', '').strip()
            context_type = request.POST.get('context', 'general')

        if not user_message or len(user_message.strip()) == 0:
            return JsonResponse({'error': 'Please provide a message to chat with'}, status=400)

        # Get AI response using Gemini
        ai_response = chatbot_response(
            user_message=user_message,
            user=request.user if request.user.is_authenticated else None,
            context=context_type
        )

        return JsonResponse({
            'response': ai_response,
            'timestamp': timezone.now().strftime('%H:%M')
        })

    # GET request - show chatbot interface
    return render(request, 'core/chatbot.html')


@csrf_exempt
def get_initial_questions(request):
    """
    Return role-based AI questions for newly logged-in users.

    This endpoint is called by the chat widget to get initial
    questions based on the user's role after login.
    """
    if request.method == 'GET':
        user = request.user if request.user.is_authenticated else None
        questions = generate_role_based_questions(user)

        return JsonResponse({
            'questions': questions,
            'user_role': get_user_role(user)
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_user_role(user):
    """Helper function to determine user role as string"""
    if not user or not user.is_authenticated:
        return 'guest'

    if hasattr(user, 'is_rider') and user.is_rider:
        return 'rider'
    elif hasattr(user, 'is_vehicle_provider') and user.is_vehicle_provider:
        return 'provider'
    elif user.is_staff:
        return 'admin'
    else:
        return 'user'


def smart_search(request):
    """
    AI-powered bike search and recommendations.

    Uses Gemini AI to analyze user queries and recommend suitable bikes.
    """
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()

        if not query:
            messages.error(request, 'Please enter a search query')
            return redirect('ebikes')

        # Get all available bikes for recommendations
        available_bikes = EBike.objects.filter(is_available=True)

        # Get AI recommendations
        recommendations = get_bike_recommendations(query, available_bikes, request.user)

        if recommendations:
            # Show success message with count
            messages.success(request, f'Found {len(recommendations)} AI-recommended e-bike(s) for: "{query}"')
        else:
            messages.info(request, f'No specific recommendations found for "{query}". Showing all available bikes.')

        # Render ebikes template with filtered results
        favorite_ids = []
        if request.user.is_authenticated:
            favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('ebike_id', flat=True))

        # If we have AI recommendations, show only those
        if recommendations:
            recommended_bikes = [rec['bike'] for rec in recommendations]
            return render(request, 'core/ebikes.html', {
                'ebikes': recommended_bikes,
                'favorite_ids': favorite_ids,
                'ai_recommendations': recommendations,
                'search_query': query
            })

    # GET request or no recommendations - redirect to regular ebikes page
    return redirect('ebikes')
