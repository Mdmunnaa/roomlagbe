# 🏠 RoomLagbe — Stay Marketplace Bangladesh

Airbnb-style stay marketplace for Bangladesh.

## Setup

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Migrations (SQLite ব্যবহার হয়, আলাদা কোনো DB সেটআপ লাগে না)
python manage.py makemigrations
python manage.py migrate

# 4. Superuser (Admin)
python manage.py createsuperuser

# 5. Run server
python manage.py runserver
```

## Deploy on PythonAnywhere
1. GitHub থেকে repo clone/pull করো PythonAnywhere Bash console-এ।
2. Virtualenv বানিয়ে `pip install -r requirements.txt` চালাও।
3. `python manage.py migrate` আর `python manage.py createsuperuser`।
4. **Web** ট্যাবে নতুন app বানাও (Manual config, Python 3.x) → Source code path আর Virtualenv path সেট করো।
5. WSGI ফাইল এডিট করে `core.wsgi.application` পয়েন্ট করাও।
6. Static/Media files ম্যাপিং:
   - URL `/static/` → Directory: `.../roomlagbe/staticfiles`
   - URL `/media/` → Directory: `.../roomlagbe/media`
7. Deploy-এর আগে একবার `python manage.py collectstatic` চালাও।
8. Reload করো — ব্যাস, লাইভ!

## URL Structure
- `/` — Homepage
- `/search/` — Search & Filter (amenities filter সহ)
- `/property/<slug>/` — Property Detail (booking calendar + map embed)
- `/property/<slug>/book/` — Booking calendar & inquiry
- `/inbox/` — In-app চ্যাট
- `/dashboard/` — Host Dashboard
- `/admin/` — Admin Panel
- `/login/`, `/register/`, `/register/host/` — Auth

## Tech Stack
- Django 4.2+ (SQLite)
- Bootstrap 5.3 + FontAwesome 6
- Flatpickr (booking calendar)
- Google Fonts (Poppins)

