import redis

from app.core.config import settings


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)



# Why create a separate module?
# - redis.Redis.from_url() ---> creates a reusable Redis client and connection pool.
# - settings.redis_url ---> keeps the connection configuration outside the application logic.
# - decode_responses=True ---> makes Redis return strings instead of bytes.
# - The timeouts prevent Redis operations from waiting indefinitely if the server becomes unreachable.







