# 🚲 AIS E-Bikes Rentals Platform

A powerful, scalable, and user-friendly **e-bike rental system** that connects riders with e-bike providers. Built with **Python**, **Django**, and styled using **Bootstrap**, this platform simplifies short-term vehicle rentals and promotes eco-friendly urban mobility.

---

## 🎯 Purpose

* 🔓 Simplify short-term access to electric bikes.
* 👨‍👩‍👧‍👦 Serve solo riders and families alike.
* 💰 Help vehicle owners earn passive income.
* 🌱 Promote green, sustainable transportation.

---

## 🚀 Features

* 🧑‍💼 User-friendly interfaces for Riders & Providers
* 🔐 Secure registration and login system
* 🚴 E-bike listing, booking, and management
* 📊 Dashboard for Riders, Providers, and Admin
* ⏱️ Daily rentals & weekly subscription plans
* 🔍 Booking history & availability tracking
* 📝 Vehicle registration with document verification
* 💸 Automated earnings and platform fee tracking
* 📱 Mobile number and email-based registration
* 🖼️ Profile image upload for users
* 🔔 Notification system for bookings and updates

---

## 🧩 Tech Stack

| Layer        | Technology           |
| ------------ | -------------------- |
| Frontend     | HTML, CSS, Bootstrap |
| Backend      | Python, Django       |
| Database     | SQLite (default)     |
| Auth & Admin | Django Admin Panel   |

---

## 🏗️ Project Modules

### 🔸 `core/`
* Home, About, Authentication (Login/Signup), Profile Management

### 🔸 `riders/`
* Rider registration, login, dashboard, and booking system
* Booking confirmation and payment

### 🔸 `vehicle_providers/`
* Vehicle owner dashboard, bike upload, earnings tracker
* Vehicle registration and management

### 🔸 `admin_dashboard/`
* Admin dashboard for managing users, bookings, and vehicles

---

## 🧭 Application Flow

Home → Register/Login → Browse E-Bikes → Book or Upload → Dashboard → Manage & Track

---

## 🛠️ Local Setup Instructions

### ✅ Prerequisites

* Python 3.8+
* Git
* pip (Python package installer)

---

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/sandesh9160/AIS_EBikes_Rental.git
cd AIS_EBikes_Rental

# (Optional) Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 🔄 Migrate & Run

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Create admin account
python manage.py runserver
```

📍 Open: http://localhost:8000

---

## 📂 Project Structure

```
admin_dashboard/         # Admin-specific views and models
ais_ebike_rental/        # Project settings and configuration
core/                    # Core app: home, auth, profile, notifications
riders/                  # Rider-specific features
vehicle_providers/       # Vehicle provider features
media/                   # Uploaded images and documents
templates/               # HTML templates for all apps
requirements.txt         # Python dependencies
manage.py                # Django management script
db.sqlite3               # SQLite database (default)
```

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 🌐 Live Demo

*No live deployment yet. Run locally as described above.*

---

## ✨ Credits

Developed by Sandesh Kenchugundi and contributors.

---

For more details, see the [GitHub repository](https://github.com/sandesh9160/AIS_EBikes_Rental). 