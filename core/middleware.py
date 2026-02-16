"""
Security headers middleware for Cedrus.

Adds security headers to ALL responses (including static files when served
via WhiteNoise). Works alongside Django's SecurityMiddleware and the Nginx
security headers in production for defence-in-depth.

Addresses OWASP ZAP findings:
- [10038] Content Security Policy (CSP) Header Not Set
- [10063] Permissions Policy Header Not Set
- [10036] Server Leaks Version Information
- [90004] Insufficient Site Isolation Against Spectre Vulnerability
- [10021] X-Content-Type-Options Header Missing (on static files)
"""

from __future__ import annotations


class SecurityHeadersMiddleware:
    """Add security headers to every HTTP response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ── Content Security Policy ──────────────────────────────────────
        # Allows self + CDN domains used by the Carbon Design System,
        # Google Fonts, and Bootstrap Icons.
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://1.www.s81c.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
                "https://1.www.s81c.com https://cdn.jsdelivr.net; "
                "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'self'"
            )

        # ── Permissions Policy ───────────────────────────────────────────
        # Disable browser features the application does not use.
        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), "
                "gyroscope=(), accelerometer=()"
            )

        # ── Cross-Origin-Opener-Policy (Spectre mitigation) ─────────────
        # Django ≥4.0 sets this via SECURE_CROSS_ORIGIN_OPENER_POLICY,
        # but we ensure it's present on ALL responses including static.
        if "Cross-Origin-Opener-Policy" not in response:
            response["Cross-Origin-Opener-Policy"] = "same-origin"

        # ── X-Content-Type-Options ───────────────────────────────────────
        # Django's SecurityMiddleware sets this for views, but static
        # file responses may bypass middleware in dev mode.
        if "X-Content-Type-Options" not in response:
            response["X-Content-Type-Options"] = "nosniff"

        # ── Hide server version information ──────────────────────────────
        # Prevent leaking Gunicorn / Django dev server version.
        response["Server"] = "Cedrus"

        return response
