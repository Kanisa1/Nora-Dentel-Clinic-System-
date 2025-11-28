# Nora Dental Clinic System

A comprehensive dental clinic management system built with Django REST Framework and React.

## Features

### User Roles
- **Admin**: Full system access
- **Receptionist**: Patient registration and scheduling
- **Doctor**: Medical records, prescriptions, and tariff selection
- **Cashier**: Invoice management and payment processing
- **Finance**: Financial reports and analytics

### Core Modules
- **Patient Management**: Registration with insurance percentage tracking
- **Medical Records**: Complete patient visit documentation
- **Tariff System**: Configurable acts/procedures for billing
- **Invoice Generation**: Auto-generated from doctor-selected tariffs
- **Payment Processing**: Multiple payment methods support
- **Pharmacy**: Drug management and prescription dispensing
- **Store/Inventory**: Stock management and tracking

### Reports
- Daily Summary Report
- Monthly Financial Report
- Doctor Income Report
- Insurance Claims Report
- HMIS (Health Management Information System) Report
- IDSR (Integrated Disease Surveillance and Response) Report

## Tech Stack

### Backend
- Django 5.x
- Django REST Framework
- MySQL (configurable, defaults to SQLite for development)

### Frontend
- React 18 with TypeScript
- React Router for navigation
- Axios for API calls

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL (optional, SQLite works for development)

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (optional for production):
```bash
export DJANGO_SECRET_KEY='your-secret-key'
export DB_ENGINE='django.db.backends.mysql'
export DB_NAME='clinic_db'
export DB_USER='your_user'
export DB_PASSWORD='your_password'
export DB_HOST='localhost'
export DB_PORT='3306'
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## API Endpoints

### Authentication
- `GET /api/users/me/` - Get current user
- `GET /api/users/doctors/` - List all doctors

### Patients
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create patient
- `GET /api/patients/{id}/` - Get patient details
- `PATCH /api/patients/{id}/` - Update patient
- `DELETE /api/patients/{id}/` - Delete patient

### Tariffs
- `GET /api/tariffs/` - List tariffs
- `POST /api/tariffs/` - Create tariff
- `GET /api/tariffs/{id}/` - Get tariff details

### Medical Records
- `GET /api/medical-records/` - List records
- `POST /api/medical-records/` - Create record
- `POST /api/medical-records/{id}/create_invoice/` - Generate invoice from record

### Invoices
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/{id}/add_payment/` - Add payment
- `POST /api/invoices/{id}/cancel/` - Cancel invoice

### Reports
- `GET /api/reports/daily/` - Daily report
- `GET /api/reports/monthly/` - Monthly report
- `GET /api/reports/doctor-income/` - Doctor income report
- `GET /api/reports/insurance/` - Insurance report
- `GET /api/reports/hmis/` - HMIS report
- `GET /api/reports/idsr/` - IDSR report
- `GET /api/dashboard/` - Dashboard summary

## License

MIT License
