import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "superkey777"

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'hms.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "superkey777"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=3)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = "redis://localhost:6379/0"

    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
    CELERY_TASK_IGNORE_RESULT = False
    CELERY_TASK_TRACK_STARTED = True

    CORS_ORIGINS = ["http://localhost:5173"]

    EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = "dhruvreddysripathi2006@gmail.com"
    MAIL_PASSWORD = "xqhvspkboqxtxtgp"

    MAIL_DEFAULT_SENDER = ("HMS Hospital", "dhruvreddysripathi2006@gmail.com")
