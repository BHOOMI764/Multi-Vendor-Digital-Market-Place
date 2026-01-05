# Digital Market (Django)

Small Django marketplace app. Contains product listing, purchases, user auth, and simple payment flow.

## Features
- User registration and login
- Create, edit, delete products
- View product detail and purchase history
- Simple payment success/failure pages

## Prerequisites
- Python 3.10+
- pip

## Quick setup
1. Create and activate a virtual environment (if not already):

   - Windows PowerShell

     ```powershell
     python -m venv env
     .\env\Scripts\Activate.ps1
     ```

2. Install dependencies (install Django and any listed libs):

   ```powershell
   pip install -r requirements.txt
   ```

   If `requirements.txt` is missing, install Django and common deps manually:

   ```powershell
   pip install django requests stripe
   ```

3. Apply migrations and create a superuser:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Run the development server:

   ```powershell
   python manage.py runserver
   ```

Open http://127.0.0.1:8000/ in your browser.

## Project layout
- `mysite/` — Django project config (`settings.py`, `urls.py`, `wsgi.py`)
- `myapp/` — main app with models, views, templates
- `uploads/` — uploaded media (if used)

## Templates
Templates live under `myapp/templates/myapp/` and include pages such as `index.html`, `detail.html`, `dashboard.html`, `login.html`, and `register.html`.

## Notes
- This README is a minimal guide to get the app running locally. For production deployment, configure static/media settings, a production-ready database, and secure SECRET_KEY and Stripe/API credentials.

## Need help?
If you want, I can also:
- add a `requirements.txt` generated from your virtualenv
- add `Procfile`/deployment notes
- document environment variables used by payments
