# Event Management System (Django)

This project implements an Event Management REST API with:
- JWT Authentication
- Event creation & editing (organizer only)
- RSVP support (Going / Maybe / Not Going)
- Reviews
- Custom permissions (private event access control)
- Basic frontend pages for login, event listing, RSVP, reviews

## Features
- Django REST Framework
- Django Filters for search & filtering
- JWT authentication
- Pagination, permissions, viewsets

## Setup Instructions

Create virtual environment:

python -m venv venv
venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt


Apply migrations:

python manage.py migrate


Create superuser:

python manage.py createsuperuser


Run the server:

python manage.py runserver

API Endpoints

/api/events/

/api/events/<id>/

/api/events/<id>/rsvp/

/api/events/<id>/reviews/

/api/token/ — JWT

/api/token/refresh/

Frontend Pages

/events/

/events/<id>/

/accounts/login/
