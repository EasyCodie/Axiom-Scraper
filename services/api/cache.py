"""Caching utilities using fastapi-cache2 backed by Redis."""

from typing import Any, Callable

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis.asyncio import Redis


def init_cache(redis: Redis | None) -> None:
    """Initialize FastAPI caching with Redis backend."""
    if redis:
        FastAPICache.init(RedisBackend(redis), prefix="axiom-cache")
    else:
        FastAPICache.init(InMemoryBackend(), prefix="axiom-cache")


def cached(ttl: int, namespace: str = "api") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory to cache route responses."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return cache(expire=ttl, namespace=namespace)(func)

    return decorator
