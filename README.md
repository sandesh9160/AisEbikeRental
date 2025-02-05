# AIS_EBikes_Rental

## Overview

The Bike Rental Platform is a web-based application that allows users to rent bikes for various durations, daily, and weekly rentals. The platform provides an intuitive interface for browsing available bikes, making reservations, and  Administrators can manage bike inventory, monitor rentals, and generate reports.

## Features

- **Riders:**
  - Browse available bikes with detailed information.
  - Reserve bikes for  daily, or weekly durations.
  - View rental history and manage current rentals.
  **Vehicle  Providers:**
  - Manage bikes,transcations.
  - Add bikes,see current bookings

- **Admin Features:**
  - Manage bike inventory (add, update, remove bikes).
  - View and manage all user rentals.
  - Generate rental reports and analytics.

## Technologies Used

- **Frontend:** HTML5, CSS3, Bootsrap
- **Backend:** Python (Django)
- **Database:** SQLite3


## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/sandesh9160/bike-rental-platform.git
   cd bike-rental-platform

  Set Up the Backend:

  ## Install Python dependencies:
    bash
    pip install -r requirements.txt
2. **Configure the database settings in backend/settings.py.**
3. Run database migrations
   python manage.py migrate
4.Create a superuser for admin access:
bash
python manage.py createsuperuser
5.Run the Application:
python manage.py runserver
Access the application at **http://localhost:8000.**


