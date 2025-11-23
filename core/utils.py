import os
from google import genai
from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
import logging

from core.models import EBike, Booking

logger = logging.getLogger(__name__)

# 🔧 Initialize Gemini AI with NEW SDK
# The client automatically gets the API key from GEMINI_API_KEY environment variable
client = genai.Client()

# Find working model - NEW SDK approach
working_model = None

try:
    # List available models with new SDK
    models_list = client.models.list()
    available_models = [model.name for model in models_list]

    logger.info(f"API Key supports these models: {available_models}")

    # Preferred models in order of preference (gemini-2.5-flash is the latest flagship!)
    preferred_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite', 'gemini-pro']

    # Clean model names (API returns "models/gemini-..." but we need just "gemini-...")
    clean_available_models = [model.replace('models/', '') for model in available_models]

    # Find intersection
    supported_models = [model for model in preferred_models if model in clean_available_models]

    if supported_models:
        for model_name in supported_models:
            try:
                # Test with new SDK method
                response = client.models.generate_content(
                    model=model_name,
                    contents="test"
                )
                working_model = model_name
                logger.info(f"✅ Successfully connected with NEW SDK - Model: {working_model}")
                break
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                continue
    else:
        logger.error("None of the preferred models are available!")
        logger.error(f"Available models: {available_models}")

except Exception as e:
    logger.warning(f"Could not connect to Gemini API: {e}")
    logger.error("🚨 GEMINI API UNAVAILABLE!")
    logger.error("   1. Check your GEMINI_API_KEY in .env")
    logger.error("   2. Ensure it's from: https://makersuite.google.com/app/apikey")
    logger.error("   3. Restart your Django server")

# Note: We'll use the client directly in the functions below instead of a global model


def sync_bike_availability() -> int:
    """Recompute EBike.is_available based on current date AND time (real-time updates).

    This function now handles expired bookings by checking both date and time
    to ensure bikes become available immediately when bookings expire.

    Returns the number of bikes whose availability was updated.
    """
    now = timezone.now()
    today = now.date()
    current_time = now.time()
    updated = 0

    with transaction.atomic():
        for bike in EBike.objects.all():
            # Check for bookings that are still active
            # A booking is active if:
            # 1. It's approved, paid, not rejected AND
            # 2. Current datetime is between start_datetime and end_datetime
            has_active_booking = Booking.objects.filter(
                ebike=bike,
                status='approved',
                is_rejected=False,
                is_paid=True,
            ).filter(
                # Booking starts before now AND ends after now
                models.Q(
                    # Multi-day booking spanning across current date
                    start_date__lt=today,
                    end_date__gt=today
                ) | models.Q(
                    # Started earlier today and hasn't ended yet
                    start_date=today,
                    start_time__lte=current_time,
                    end_date__gt=today
                ) | models.Q(
                    # Started and ends today, current time is between start and end
                    start_date=today,
                    end_date=today,
                    start_time__lte=current_time,
                    end_time__gt=current_time
                ) | models.Q(
                    # Starts later today
                    start_date=today,
                    start_time__gt=current_time,
                    end_date__gt=today
                ) | models.Q(
                    # Ends today, hasn't started yet (for same-day bookings)
                    start_date=today,
                    end_date=today,
                    start_time__gt=current_time
                )
            ).exists()

            new_available = not has_active_booking

            if bike.is_available != new_available:
                bike.is_available = new_available
                bike.save(update_fields=["is_available"])
                updated += 1

    return updated


def get_bike_recommendations(user_query, available_bikes, user=None):
    """
    Use Gemini AI to recommend bikes based on user query and available bikes.

    Args:
        user_query: User's requirements (e.g., "fast bike for city commute")
        available_bikes: QuerySet of available EBike objects
        user: User object (optional, for personalization)

    Returns:
        List of recommended bikes with explanations
    """
    if not available_bikes:
        return []

    # Build bike information
    bikes_data = []
    for bike in available_bikes:
        review_count = bike.reviews.count()
        avg_rating = 0
        if review_count > 0:
            avg_rating = sum(review.rating for review in bike.reviews.all()) / review_count

        bike_info = f"""
        Bike Name: {bike.name}
        Description: {bike.description[:200]}...
        Daily Rate: ₹{bike.price_per_day}
        Weekly Rate: ₹{bike.price_per_week}
        Provider: {bike.provider.username}
        Reviews: {review_count} reviews, {avg_rating:.1f} stars
        """
        bikes_data.append(bike_info.strip())

    # Create context for AI
    context = f"""
    You are an expert e-bike rental consultant for AIS E-Bike Rental.

    Available bikes in our system:
    {'-' * 50}
    {chr(10).join(bikes_data)}

    User query: "{user_query}"

    Instructions:
    1. Analyze the user's requirements from their query
    2. Recommend 1-3 best matching bikes from the available options
    3. For each recommendation, explain why it's a good match
    4. Consider factors like speed, battery life, comfort, terrain, distance, budget
    5. Keep responses helpful and conversational

    Format your response as:
    **Recommended E-Bikes:**

    1. **Bike Name** - ₹Price/day
       Why this bike: [brief explanation]

    2. **Bike Name** - ₹Price/day
       Why this bike: [brief explanation]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Use the actual working model here
            contents=context
        )

        # Extract bike recommendations from response
        recommendations = []
        response_text = response.text

        # Simple parsing to extract bike names from response
        for bike in available_bikes:
            if bike.name.lower() in response_text.lower():
                recommendations.append({
                    'bike': bike,
                    'explanation': 'AI-powered recommendation based on your requirements'
                })

        return recommendations[:3]  # Return top 3 recommendations

    except Exception as e:
        logger.error(f"Error getting bike recommendations: {str(e)}")
        return []


def chatbot_response(user_message, user=None, context="general"):
    """
    Generate intelligent responses using Gemini AI for customer service.

    Args:
        user_message: User's question or message
        user: User object (optional, for personalization)
        context: Context like "booking", "support", "general"

    Returns:
        AI-generated response string
    """
    # Get system context based on the context parameter
    system_contexts = {
        "booking": """
        You are a helpful booking assistant for AIS E-Bike Rental.
        Help users with booking inquiries, availability checks, pricing questions.
        Be encouraging about the booking process and highlight e-bike benefits.
        """,

        "support": """
        You are a customer support specialist for AIS E-Bike Rental.
        Help with technical issues, account problems, general questions.
        Be empathetic and solution-focused.
        """,

        "general": """
        You are a friendly AI assistant for AIS E-Bike Rental.
        Answer questions about our e-bike rental service, locations, hours, policies.
        Be informative, helpful, and promote our eco-friendly electric bikes.
        """
    }

    system_prompt = system_contexts.get(context, system_contexts["general"])

    # Add user-specific context
    user_context = ""
    if user:
        user_context = f"\nUser: {user.get_full_name() or user.username} (ID: {user.id})"
        if hasattr(user, 'is_rider') and user.is_rider:
            user_context += " - Registered rider"
        if hasattr(user, 'is_vehicle_provider') and user.is_vehicle_provider:
            user_context += " - Vehicle provider"

    # Build conversation starter with comprehensive website information
    chat_context = f"""
    {system_prompt}

    COMPLETE AIS E-BIKE RENTAL INFORMATION:
    ================================

    LOCATION & HOURS:
    - Store Location: AIS E-bike Rental Store, India
    - Operating Hours: 9 AM to 6 PM, Monday to Sunday
    - Pickup/Return: Direct from AIS Store only

    BOOKING & AVAILABILITY:
    - Real-time bike availability tracking
    - Online booking via our website
    - Instant booking confirmation
    - 24/7 booking availability

    PAYMENT & PRICING:
    - Payment Method: Online via Razorpay (secure)
    - Platform Fee: 10% service charge
    - Minimum Withdrawal: ₹200
    - Refund Policy: As per terms

    AVAILABLE E-BIKES:
    - Ola S3: Comfortable city commuter, 60-100km range, ₹20-30/day
    - Hero Optima HX: Powerful electric bike, 80-120km range, ₹25-35/day
    - Revolt RV: Premium long-range, 150km+, ₹40-50/day
    - Kabira KM400: Adventure/off-road capable, ₹30-40/day
    - **Real-time availability**: All bikes shown are currently available

    BOOKING PROCESS:
    1. Choose bike from website
    2. Select dates and times
    3. Pay online via Razorpay
    4. Get booking confirmation
    5. Visit AIS Store for pickup

    WITHDRAWAL & PROVIDER SYSTEM:
    - Providers earn 90% of rental fees
    - Minimum ₹200 to withdraw
    - Withdrawals processed within 24 hours
    - Bank transfer or UPI options

    SUPPORT & CONTACT:
    - Email: support@aisebikerental.com
    - Phone: Customer care available
    - Live chat: Available 24/7
    - Dashboard: Self-service for users

    POLICIES:
    - Cancellation: Free up to 24 hours before pickup
    - Late returns: Additional charges apply
    - Damage: Insurance covers minor incidents
    - Helmet: Provided with every rental (mandatory)
    - Documents required: Valid government ID

    {user_context}

    IMPORTANT: Answer ANY question about our e-bike rental service with accurate information from the above details. Be helpful, knowledgeable, and encouraging about electric bike rentals.

    User Question: "{user_message}"

    Response Guidelines:
    - Always answer questions about AIS E-bike Rental based on the information above
    - Be enthusiastic about eco-friendly electric bikes
    - Provide specific pricing and availability information
    - Guide users through the booking process when asked
    - Be helpful for both riders and providers
    - Keep responses conversational and friendly
    - Include relevant next steps or contact information when appropriate
    - Never refuse to answer - use the information provided
    """

    try:
        response = client.models.generate_content(
            model=working_model or "gemini-2.5-flash",
            contents=chat_context
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating chatbot response: {str(e)}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now. Please try again or contact our support team for immediate assistance."


def generate_role_based_questions(user):
    """
    Generate role-specific AI questions for newly logged-in users.

    Args:
        user: User object (authenticated user)

    Returns:
        List of role-specific questions to ask the user
    """
    if not user or not user.is_authenticated:
        return ["👋 Welcome! How can I help you today?"]

    # Rider specific questions
    if hasattr(user, 'is_rider') and user.is_rider:
        return [
            "🏍️ Welcome back! Ready to rent an e-bike?",
            "📅 Looking to book for tomorrow or later?",
            "❓ Need help finding the perfect bike for your trip?"
        ]

    # Vehicle provider specific questions
    elif hasattr(user, 'is_vehicle_provider') and user.is_vehicle_provider:
        return [
            "🚲 Welcome back! How's your bike fleet doing?",
            "💰 Interested in checking your earnings today?",
            "📱 Need help managing your listings or withdrawals?"
        ]

    # Admin staff specific questions
    elif user.is_staff:
        return [
            "👑 Welcome Admin! Ready to manage the platform?",
            "📊 Want to review recent bookings or user activity?",
            "⚙️ Need assistance with user verifications or withdrawals?"
        ]

    # Default fallback
    return ["👋 Welcome! How can I assist you with your e-bike rental needs?"]


def generate_smart_content(content_type, context_data=None):
    """
    Generate various content using Gemini AI.

    Args:
        content_type: "email_marketing", "review_response", "support_message"
        context_data: Dictionary with relevant context information

    Returns:
        Generated content string
    """
    prompts = {
        "email_marketing": f"""
        Generate a personalized marketing email for AIS E-Bike Rental.

        Context: {context_data or {}}

        The email should:
        - Highlight eco-friendly benefits
        - Mention current promotions
        - Include a clear call-to-action
        - Be under 200 words
        """,

        "review_response": f"""
        Generate a professional response to a customer review.

        Review context: {context_data or {}}

        Response should be:
        - Thankful and positive
        - Address specific points mentioned
        - Professional and company-branded
        - Under 100 words
        """,

        "support_message": f"""
        Generate a helpful support message template.

        Issue context: {context_data or {}}

        Message should:
        - Empathize with customer
        - Provide clear solution steps
        - Offer contact information
        - Professional tone
        """
    }

    prompt = prompts.get(content_type, "Generate engaging content for AIS E-Bike Rental.")

    try:
        response = client.models.generate_content(
            model=working_model or "gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating smart content: {str(e)}")
        return "Content generation temporarily unavailable."
