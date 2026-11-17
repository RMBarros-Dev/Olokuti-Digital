import hashlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

from apps.audit.services import record_event


def get_client_ip(request) -> str:
    """Extract client IP safely, trusting X-Forwarded-For only when explicitly enabled."""
    remote_addr = request.META.get("REMOTE_ADDR", "127.0.0.1") or "127.0.0.1"
    if not getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        return remote_addr
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if not forwarded_for:
        return remote_addr
    hops = [part.strip() for part in forwarded_for.split(",") if part.strip()]
    if not hops:
        return remote_addr
    trusted_hops = max(1, int(getattr(settings, "TRUSTED_PROXY_HOPS", 1)))
    index = max(0, len(hops) - trusted_hops)
    return hops[index]


def check_rate_limit(
    request,
    scope: str,
    *,
    limit: int,
    window_seconds: int,
    identifier: str = "",
) -> tuple[bool, int]:
    """Increment a temporary fixed-window counter and report (blocked, retry_after_seconds)."""
    client_ip = get_client_ip(request)
    raw_key = f"{scope}:{client_ip}:{identifier.lower().strip()}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    cache_key = f"rl:{scope}:{digest}"

    cache.add(cache_key, 0, timeout=window_seconds)
    try:
        count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window_seconds)
        count = 1

    if count > limit:
        if count == limit + 1:
            record_event(
                user=getattr(request, "user", None),
                action="rate_limited",
                entity="security.RateLimit",
                entity_id=scope,
                details={"scope": scope, "limit": limit, "window_seconds": window_seconds},
            )
        return True, window_seconds
    return False, 0


def rate_limit_response(retry_after: int, message: str = "Too many requests. Try again later."):
    response = HttpResponse(message, status=429, content_type="text/plain; charset=utf-8")
    response["Retry-After"] = str(max(1, int(retry_after)))
    return response
