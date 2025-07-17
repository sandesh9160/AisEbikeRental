# 🚲 AIS E-Bikes Rentals Platform

A powerful, scalable, and user-friendly **e-bike rental system** that connects riders with e-bike providers. Built with **Python**, **Django**, **MySQL**, and styled using **Bootstrap**, this platform simplifies short-term vehicle rentals and promotes eco-friendly urban mobility.

---

## 🎯 Purpose

- 🔓 Simplify short-term access to electric bikes.
- 👨‍👩‍👧‍👦 Serve solo riders and families alike.
- 💰 Help vehicle owners earn passive income.
- 🌱 Promote green, sustainable transportation.

---

## 🚀 Features

- 🧑‍💼 User-friendly interfaces for Riders & Providers
- 🔐 Secure registration and login system
- 🚴 E-bike listing, booking, and management
- 📊 Dashboard for Riders, Providers, and Admin
- ⏱️ Daily rentals & weekly subscription plans
- 🔍 Booking history & availability tracking
- 📝 Vehicle registration with document verification
- 💸 Automated earnings and platform fee tracking

---

## 📸 Screenshots

### Home Page
![Home Page](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/homepage.png)

### Login Page
![Login Page](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/loginpage.png)

### Signup Page
![Signup Page](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/signuppage.png)

### Available E-Bikes
![Available E-Bikes](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/available_ebikes.png)

### Rider Dashboard
![Rider Dashboard 1](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/riderdashboard_1.png)
![Rider Dashboard 2](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/riderdashboard_2.png)
![Rider Dashboard 3](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/riderdashboard_3.png)

### Book E-Bike
![Book E-Bike](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/book_ebike.png)

### Payment Page
![Payment Page](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/payementpage.png)

### Payment Confirmation
![Payment Confirmation](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/payement_conformpage.png)

### Receipt
![Receipt](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/recipt.png)

### Provider Dashboard
![Provider Dashboard 1](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/providerdashboard_1.png)
![Provider Dashboard 2](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/providerdashboard_2.png)

### Add E-Bike Page
![Add E-Bike Page](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/add_ebikepage.png)

### Admin Dashboard
![Admin Dashboard 1](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/admin_dashboard1.png)
![Admin Dashboard 2](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/admin_dashboard2.png)
![Admin Dashboard 3](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/admin_dashboard3.png)
![Admin Dashboard 4](https://raw.githubusercontent.com/sandesh9160/AisEbikeRental/main/screenshots/admin_dashboard4.png)

---

## 🧩 Tech Stack

| Layer         | Technology           |
|---------------|---------------------|
| Frontend      | HTML, CSS, Bootstrap |
| Backend       | Python, Django       |
| Database      | MySQL               |
| Auth & Admin  | Django Admin Panel  |

---

## 🏗️ Project Modules

### 🔸 `core/`
- Home, About, Authentication (Login/Signup), Profile Management, Notifications

### 🔸 `riders/`
- Rider registration, login, dashboard, booking system, payment

### 🔸 `vehicle_providers/`
- Vehicle owner dashboard, bike upload, earnings tracker, vehicle registration

### 🔸 `admin_dashboard/`
- Admin dashboard for managing users, bookings, and vehicles

---

## 🧭 Application Flow

Home → Register/Login → Browse E-Bikes → Book or Upload → Dashboard → Manage & Track

---

## 🛠️ Local Setup Instructions

### ✅ Prerequisites

- Python 3.8+
- MySQL 5.7+
- Git
- pip (Python package installer)

---

### 📦 Installation

```bash
git clone https://github.com/sandesh9160/AisEbikeRental.git
cd AisEbikeRental
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

---

### 🗃️ Database Setup

In MySQL:
```sql
CREATE DATABASE ais_ebikes_db;
CREATE USER 'ais_ebikes_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ais_ebikes_db.* TO 'ais_ebikes_user'@'localhost';
FLUSH PRIVILEGES;
```

---

### 🔐 Environment Configuration

Create a `.env` file in the project root:
```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_NAME=ais_ebikes_db
DATABASE_USER=ais_ebikes_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
```
Update `settings.py` to read from `.env`.

---

### 🔄 Migrate & Run

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Create admin account
python manage.py collectstatic    # Collect static files
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
screenshots/             # Project screenshots for documentation
templates/               # HTML templates for all apps
requirements.txt         # Python dependencies
manage.py                # Django management script
db.sqlite3               # SQLite database (default, for development)
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

For more details, see the [GitHub repository](https://github.com/sandesh9160/AisEbikeRental). 