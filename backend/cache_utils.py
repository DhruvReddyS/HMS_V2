import json
from functools import wraps
from flask import request
from redis_client import redis_client

DEFAULT_TTL = 60


def _make_cache_key(prefix: str = "") -> str:
    path = request.path
    args = "&".join(f"{k}={v}" for k, v in sorted(request.args.items()))
    base = f"{path}?{args}" if args else path
    return f"API:{prefix}:{base}" if prefix else f"API:{base}"


def cache_set(key: str, value, ttl: int = DEFAULT_TTL):
    redis_client.setex(key, ttl, json.dumps(value))


def cache_get(key: str):
    raw = redis_client.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_delete_pattern(pattern: str):
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break


def cached(prefix: str = "", ttl: int = DEFAULT_TTL):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import jsonify, Response

            if request.method != "GET":
                return fn(*args, **kwargs)

            key = _make_cache_key(prefix=prefix)
            cached_value = cache_get(key)
            if cached_value is not None:
                return jsonify(cached_value)

            result = fn(*args, **kwargs)

            if isinstance(result, tuple):
                payload = result[0]
                status = result[1] if len(result) > 1 else 200
                if isinstance(payload, dict) and status == 200:
                    cache_set(key, payload, ttl)
                return result

            if isinstance(result, dict):
                cache_set(key, result, ttl)
                from flask import jsonify as _jsonify
                return _jsonify(result)

            if isinstance(result, Response):
                return result

            return result

        return wrapper

    return decorator
