from django.conf import settings
import redis

def redis_connection(decode=False):
    return(redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DATABASE,
        decode_responses=decode
    ))
