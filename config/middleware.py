import secrets

from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class ActiveUserRequiredMiddleware:
    """Terminate requests whose authenticated user was deactivated after session issuance."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and not user.is_active:
            logout(request)
            if request.headers.get("HX-Request") == "true":
                return HttpResponseForbidden("Account inactive.")
            return redirect("accounts:login")
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Attach per-request CSP nonce, Content-Security-Policy, and Permissions-Policy headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        nonce = secrets.token_urlsafe(16)
        request.csp_nonce = nonce
        response = self.get_response(request)

        if "Content-Security-Policy" not in response:
            csp = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "connect-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net"
            )
            response["Content-Security-Policy"] = csp
        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
