import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask Secret Key
    SECRET_KEY = "superkey777"

    # SQLite Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'hms.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Secret
    JWT_SECRET_KEY = "superkey777"

    # Upload directory
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max upload size

    # Redis Cache (optional)
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = "redis://localhost:6379/0"

    # CORS allowed origins
    CORS_ORIGINS = ["http://localhost:5173"]
