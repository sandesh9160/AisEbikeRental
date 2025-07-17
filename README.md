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

## 🧩 Tech Stack

| Layer         | Technology          |
|---------------|---------------------|
| Frontend      | HTML, CSS, Bootstrap |
| Backend       | Python, Django       |
| Database      | MySQL               |
| Auth & Admin  | Django Admin Panel  |

---

## 🏗️ Project Modules

### 🔸 `home/`
- Landing page with navigation and e-bike highlights

### 🔸 `riders/`
- Rider registration, login, dashboard, and booking system

### 🔸 `providers/`
- Vehicle owner dashboard, bike upload, earnings tracker

### 🔸 `admin/`
- Full control over users, bookings, earnings, approvals

### 🔸 `bookings/`
- Booking history, filters, and status updates

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
# Clone the repository
git clone https://github.com/your-username/ais-e-bikes-rentals.git
cd ais-e-bikes-rentals

# Create virtual environment
python -m venv venv
source venv/bin/activate  # (use venv\Scripts\activate on Windows)

# Install dependencies
pip install -r requirements.txt

**🗃️ Database Setup**

-- In MySQL
CREATE DATABASE ais_ebikes_db;
CREATE USER 'ais_ebikes_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ais_ebikes_db.* TO 'ais_ebikes_user'@'localhost';
FLUSH PRIVILEGES;

**🔐 Environment Configuration**

DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_NAME=ais_ebikes_db
DATABASE_USER=ais_ebikes_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=3306

Update settings.py to read from .env.

**🔄 Migrate & Run**

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Create admin account
python manage.py collectstatic    # Collect static files
python manage.py runserver
📍 Open: http://localhost:8000
