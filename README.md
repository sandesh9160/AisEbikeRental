# AIS E-Bike Rental System

A comprehensive Django-based e-bike rental platform that connects electric bike owners with renters.

## Features

### For Riders (Customers)
- Browse and search available e-bikes
- Book e-bikes with online payment via Razorpay
- View booking history and manage reservations
- Write and view reviews for e-bikes
- Favorite e-bikes for quick access
- Profile management with mobile number and profile image

### For Vehicle Providers
- Register and list e-bikes for rental
- Upload documents for verification
- Manage provider dashboard and earnings
- Handle withdrawal requests
- Track vehicle registrations and approvals

### Admin Features
- Dashboard for managing bookings, providers, and reviews
- Document verification system for providers
- Withdrawal management and approval
- Notification system
- Contact message handling

### System Features
- User authentication with role-based access (Rider/Provider/Admin)
- Payment integration with Razorpay
- Email notifications and password reset
- Social login options
- Responsive web interface
- Document upload and verification system
- AI-powered chatbot for customer support
- AI-powered bike search and recommendations using Gemini API
- Automated availability synchronization
- Cron job management for expired booking checks
- Comprehensive admin dashboard with analytics

## Technology Stack

- **Backend**: Django 5.1.7
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: Django Allauth
- **Payments**: Razorpay
- **AI**: Google Gemini API (Generative AI)
- **Media Management**: Django's FileField system
- **Email**: SMTP (Gmail)

## Project Structure

```
ais_ebike_rental/
├── ais_ebike_rental/          # Main Django project settings
├── core/                      # Core application (models, views, forms)
├── riders/                    # Rider dashboard and booking management
├── vehicle_providers/         # Provider management and earnings
├── admin_dashboard/           # Admin interface and management
├── templates/                 # HTML templates
├── static/                    # CSS, JavaScript, images
├── media/                     # User uploaded files
└── requirements.txt           # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/sandesh9160/AisEbikeRental.git
   cd AisEbikeRental
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   RAZORPAY_KEY_ID=your-razorpay-key-id
   RAZORPAY_KEY_SECRET=your-razorpay-key-secret
   RAZORPAY_WEBHOOK_SECRET=your-razorpay-webhook-secret
   GEMINI_API_KEY=your-google-gemini-api-key
   CONTACT_RECEIVER_EMAIL=admin-email@example.com
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Models

### Core Models
- **User**: Extended Django User with role flags (rider/provider)
- **EBike**: Electric bike listings with pricing and availability
- **Booking**: Rental reservations with payment tracking
- **Review**: User feedback for e-bikes
- **Notification**: In-app notifications
- **ContactMessage**: Contact form submissions
- **Withdrawal**: Provider earnings withdrawal requests

### Additional Models
- **ProviderDocument**: Document uploads for verification
- **VehicleRegistration**: Vehicle registration management
- **Favorite**: User favorite e-bikes

## URLs and Views

### Core URLs
- `/`: Home page with featured e-bikes
- `/login/`: User authentication
- `/signup/`: User registration
- `/ebikes/`: E-bike listings
- `/contact/`: Contact form
- `/profile/`: User profile management

### App-specific URLs
- `/rider/`: Rider dashboard and bookings
- `/provider/`: Provider management
- `/admin/`: Administrative dashboard

## Payment Integration

The system uses Razorpay for payment processing:
- Secure online payments for bookings
- Webhook integration for payment confirmations
- Order and payment ID tracking

## Deployment

### Production Setup
1. Set `DEBUG=False`
2. Configure PostgreSQL database
3. Set up proper email backend
4. Configure static file serving (nginx/Apache)
5. Set up media file serving
6. Configure environment variables
7. Use gunicorn for application server

### Static Files
- Use WhiteNoise for static file serving in production
- Collect static files with `python manage.py collectstatic`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Commit your changes
6. Push to your fork
7. Create a Pull Request

## License

This project is for educational purposes. Please check local laws and regulations regarding rental services in your area.

## Support

For questions or issues, please use the contact form within the application or create an issue in the repository.
