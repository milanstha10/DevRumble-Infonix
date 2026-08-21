# DevRumble-Infonix

HeroHealth/
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── config/                         # Main Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                       # 👤 Member 1
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── forms.py
│
├── health/                         # 🩺 Core health functionality
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── forms.py
│   └── services.py
│
├── ai_engine/                      # 🤖 Member 3
│   ├── __init__.py
│   ├── services.py
│   ├── prompts.py
│   ├── safety.py
│   └── utils.py
│
├── facilities/                     # 🏥 Member 4
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── services.py
│
├── templates/                      # 🎨 Member 2
│   ├── base.html
│   │
│   ├── home/
│   │   └── home.html
│   │
│   ├── health/
│   │   ├── consultation.html
│   │   ├── result.html
│   │   └── emergency.html
│   │
│   ├── facilities/
│   │   ├── facility_list.html
│   │   ├── facility_detail.html
│   │   └── map.html
│   │
│   └── accounts/
│       ├── login.html
│       └── register.html
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── responsive.css
│   │
│   ├── js/
│   │   ├── main.js
│   │   ├── consultation.js
│   │   └── map.js
│   │
│   └── images/
│       └── logo.png
│
├── media/                          # User uploads
│   └── health_queries/
│
└── data/
    └── facilities.json             # Initial Nepal healthcare data