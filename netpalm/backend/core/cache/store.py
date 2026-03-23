"""
CacheStore — typed wrapper around cachelib RedisCache.

Redis is used exclusively by this component; no other part of the
codebase should import Redis directly.
"""
from __future__ import annotations

import logging
from typing import Any

from cachelib import RedisCache

from netpalm.backend.core.confload.confload import NetpalmSettings

log = logging.getLogger(__name__)


class _DisabledCache:
    """No-op cache used when redis_cache_enabled=False."""

    def get(self, key: str) -> None:
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass

    def poison(self, host_port_key: str) -> bool:
        return False


class CacheStore:
    """
    Redis-backed response cache (cachelib).
    Redis scope is limited to this class.
    """

    def __init__(self, settings: NetpalmSettings) -> None:
        self._settings = settings
        self._enabled = settings.redis_cache_enabled
        self._default_ttl = settings.redis_cache_default_timeout

        if self._enabled:
            key_prefix = str(settings.redis_cache_key_prefix).strip() or "NETPALM"
            redis_kwargs: dict[str, Any] = {
                "host": settings.redis_server,
                "port": settings.redis_port,
                "password": settings.redis_key.get_secret_value() or None,
            }
            if settings.redis_tls_enabled:
                redis_kwargs.update(
                    ssl=True,
                    ssl_cert_reqs="required",
                    ssl_keyfile=settings.redis_tls_key_file,
                    ssl_certfile=settings.redis_tls_cert_file,
                    ssl_ca_certs=settings.redis_tls_ca_cert_file,
                )
            self._cache: Any = _ClearableCache(
                default_timeout=self._default_ttl,
                key_prefix=key_prefix,
                **redis_kwargs,
            )
            log.info("CacheStore: Redis cache enabled")
        else:
            self._cache = _DisabledCache()
            log.info("CacheStore: cache disabled")

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache.set(key, value, timeout=ttl or self._default_ttl)

    def poison(self, host_port_key: str) -> bool:
        """Invalidate all cache entries for a given host:port key."""
        if not self._enabled:
            return False
        # Normalise to first two segments: host:port
        parts = host_port_key.split(":")
        pattern = ":".join(parts[:2])
        log.debug(f"CacheStore.poison: clearing keys matching {pattern!r}")
        return bool(self._cache.clear_keys(pattern))


class _ClearableCache(RedisCache):
    """RedisCache subclass that exposes key-pattern deletion."""

    def keys(self, key_pattern: str = "") -> list[bytes]:
        prefix = f"{self.key_prefix}{key_pattern}*"
        return self._write_client.keys(prefix)

    def clear_keys(self, key_pattern: str) -> bool:
        if not key_pattern:
            raise ValueError("key_pattern must not be empty")
        keys = self.keys(key_pattern)
        if keys:
            return bool(self._write_client.delete(*keys))
        return False
