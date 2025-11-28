# redis_client.py
import os
import redis

# Separate DB index for caching (Celery likely using db 0)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,  # Store strings, not bytes
)
