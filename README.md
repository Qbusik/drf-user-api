# 🔐 Django DRF User API

A backend REST API built with Django REST Framework providing user authentication, email verification, password reset via OTP, and Dockerized infrastructure.

---

## 🚀 Features

- Custom User model (email as login)
- JWT Authentication (SimpleJWT)
- Email verification via token link
- Password reset via 8-character OTP code
- Celery background tasks (email sending)
- Redis cache (OTP + cooldown handling)
- PostgreSQL database
- Docker & Docker Compose setup
- DRF Spectacular API documentation (Swagger)

---

## 🧱 Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker / Docker Compose
- SimpleJWT
- DRF Spectacular

---

## ⚙️ Project Setup (Docker)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Qbusik/drf-user-api.git
    ```

2.  **Configure Environment Variables:**

    ```bash
    copy .env.sample .env
    # then fill in your credentials
    ```

3.  **Build and Run Containers:**
    ```bash
    docker-compose up --build
    ```
    The application will be available at: `http://localhost:8000/`