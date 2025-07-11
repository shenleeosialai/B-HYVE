# B-HYVE 🚀

A full-featured social media platform inspired by Modern social media platforms, built with Django and modern web technologies. This project demonstrates advanced backend and frontend techniques to create a scalable, media-rich social networking experience.

## 🌟 Key Features

- **Image Posts**: Upload, display, and interact with photos.
- **Likes & Comments**: Engage with posts through likes and threaded comments.
- **Follow System**: Follow and unfollow users to personalize your feed.
- **Stories**: Post ephemeral content that disappears after 24 hours.
- **Explore Page**: Discover trending posts based on hashtags and simple machine learning algorithms.
- **Advanced search and filtering on Explore**
- **Responsive Design**: Optimized for mobile and desktop views.

---

## ⚙️ Technologies & Skills Demonstrated

- **Django & Django REST Framework (DRF)** — Backend API and authentication
- **PostgreSQL** — Relational database for scalable data storage
- **Celery & Redis** — Asynchronous task queue for background jobs (e.g., story expiration)
- **Media Storage** — Efficient handling of user-uploaded images and videos
- **Async Views & Signals** — High performance event-driven architecture
- **User Authentication** — Secure login, signup, and session management
- **Machine Learning (Basic)** — Simple trending algorithm for the Explore page using hashtag popularity
- **Frontend:** HTML, CSS, JavaScript (with AJAX for dynamic updates)

---

## 🚧 Planned Improvements

- Real-time notifications using Django Channels / WebSockets
- Real-time chat using Django Channels / WebSockets
- Improved ML model for trending content

---

## 🔧 Setup & Installation

1. Clone the repo:
   https://github.com/shenleeosialai/B-HYVE
2. cd B-HYVE

## Create a virtual environment and install dependencies:

1.python -m venv env
2.source env/bin/activate
3.pip install -r requirements.txt

## Configure your PostgreSQL database:

1.python manage.py migrate
redis-server
2.celery -A bookmarks beat -l info
3.python manage.py runserver

🤝 Contributions
Contributions, issues, and feature requests are welcome! Please fork the repository and submit a pull request.

