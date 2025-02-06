# AIS E-bikes Rentals Platform

## Overview

AIS E-bikes Rentals Platform is an innovative online e-bike rental booking system that connects riders with e-bike providers. This platform allows users to rent e-bikes for short periods at affordable rates, and enables bike owners to earn by renting out their vehicles. It's designed to make sustainable transportation accessible and convenient for everyone.

## Purpose

The main purpose of this project is to:
- Facilitate easy access to rented e-bikes for people who want to travel alone or with their family and friends.
- Provide a convenient solution for short-term transportation needs without the commitment of purchasing a vehicle.
- Create a platform for bike dealers or owners to rent out their bikes and generate additional income.
- Promote sustainable and eco-friendly transportation options in urban areas.

## Features

- User-friendly interface for both riders and e-bike providers
- Secure user authentication and registration system
- E-bike listing and booking functionality
- Dashboard for riders to view available e-bikes and manage bookings
- Dashboard for vehicle providers to manage their e-bikes and view earnings
- Admin console to oversee all operations and user management
- Weekly subscription and daily rental options
- Vehicle registration and verification system for providers
- Earnings tracking and platform fee calculation

## Technology Stack

- Frontend:
  - HTML
  - CSS
  - Bootstrap
- Backend:
  - Python
  - Django
- Database:
  - MySQL

## Project Structure

- `home/`: Home page with image slides and navigation
- `riders/`: User registration, login, and dashboard for riders
- `providers/`: Vehicle provider registration, login, and dashboard
- `admin/`: Admin dashboard for overseeing operations
- `about/`: Information about the company and contact details
- `e-bikes/`: Listing and details of available e-bikes
- `bookings/`: Booking management system

## Pages and Components

1. Home Page:
   - Header with navigation menu
   - Image slides showcasing e-bikes
   - Quick access to e-bikes, riders, and vehicle provider sections
   - Footer with company information

2. Riders Page:
   - Login form
   - Registration form
   - Dashboard showing top 5 e-bikes
   - Available e-bikes listing
   - Booking options (weekly subscription, one-day ride)

3. Vehicle Provider Page:
   - Login form
   - Registration form (including vehicle registration number and RC attachment)
   - Dashboard showing total earnings, platform charges, e-bike details, and occupied e-bike client details

4. Admin Dashboard:
   - Overview of rider and vehicle provider data
   - E-bike occupancy status
   - Actions for user management (delete, approve, align)
   - Display of riders waiting for e-bikes
   - E-bike availability status

5. About Us Page:
   - Company vision and mission
   - Office addresses and contact information

## Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed on your system:
- Python (3.8 or higher)
- pip (Python package manager)
- MySQL (5.7 or higher)
- Git

### Step 1: Clone the Repository

1. Open your terminal or command prompt.
2. Navigate to the directory where you want to store the project.
3. Clone the repository:
   \`\`\`
   git clone https://github.com/your-username/ais-e-bikes-rentals.git
   \`\`\`
4. Navigate into the project directory:
   \`\`\`
   cd ais-e-bikes-rentals
   \`\`\`

### Step 2: Set Up a Virtual Environment

1. Create a virtual environment:
   \`\`\`
   python -m venv venv
   \`\`\`
2. Activate the virtual environment:
   - On Windows:
     \`\`\`
     venv\Scripts\activate
     \`\`\`
   - On macOS and Linux:
     \`\`\`
     source venv/bin/activate
     \`\`\`

### Step 3: Install Dependencies

1. Upgrade pip to the latest version:
   \`\`\`
   pip install --upgrade pip
   \`\`\`
2. Install the required packages:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`

### Step 4: Set Up the Database

1. Log in to MySQL:
   \`\`\`
   mysql -u root -p
   \`\`\`
2. Create a new database:
   \`\`\`
   CREATE DATABASE ais_ebikes_db;
   \`\`\`
3. Create a new MySQL user and grant privileges:
   \`\`\`
   CREATE USER 'ais_ebikes_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON ais_ebikes_db.* TO 'ais_ebikes_user'@'localhost';
   FLUSH PRIVILEGES;
   \`\`\`
4. Exit MySQL:
   \`\`\`
   EXIT;
   \`\`\`

### Step 5: Configure the Project

1. Create a `.env` file in the project root directory:
   \`\`\`
   touch .env
   \`\`\`
2. Open the `.env` file and add the following environment variables:
   \`\`\`
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_NAME=ais_ebikes_db
   DATABASE_USER=ais_ebikes_user
   DATABASE_PASSWORD=your_password
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
   \`\`\`
   Replace `your_secret_key` with a secure random string and `your_password` with the password you set for the MySQL user.

3. Update the `settings.py` file to use these environment variables for the database configuration.

### Step 6: Run Migrations

1. Make migrations:
   \`\`\`
   python manage.py makemigrations
   \`\`\`
2. Apply migrations:
   \`\`\`
   python manage.py migrate
   \`\`\`

### Step 7: Create a Superuser

Create an admin superuser:
\`\`\`
python manage.py createsuperuser
\`\`\`
Follow the prompts to set up your admin username and password.

### Step 8: Collect Static Files

Collect all static files:
\`\`\`
python manage.py collectstatic
\`\`\`

### Step 9: Run the Development Server

Start the Django development server:
\`\`\`
python manage.py runserver
\`\`\`

The application should now be running at `http://localhost:8000`.

### Step 10: Access the Application

- Open your web browser and go to `http://localhost:8000` to access the main application.
- To access the admin panel, go to `http://localhost:8000/admin` and log in with the superuser credentials you created.

### Troubleshooting

If you encounter any issues during setup:
1. Ensure all prerequisites are correctly installed.
2. Check that your virtual environment is activated.
3. Verify that your `.env` file contains the correct database credentials.
4. Make sure the MySQL service is running on your system.
5. If you encounter any package-related errors, try updating your packages:
   \`\`\`
   pip install --upgrade -r requirements.txt
   \`\`\`

For any persistent issues, please refer to our project's issue tracker on GitHub or contact our support team.

