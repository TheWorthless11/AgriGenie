"""
Custom middleware for AgriGenie.

DaphneSessionMiddleware — safety-net that guarantees the session is
persisted to the database and the session cookie is present on every
response that touched the session.  This fixes the known edge-case
where Django's built-in SessionMiddleware does not reliably set the
cookie on 302 redirect responses served by Daphne / ASGI.
"""

import asyncio
from asgiref.sync import iscoroutinefunction, sync_to_async
from django.conf import settings
from django.utils.decorators import sync_and_async_middleware


def _patch_session_cookie(request, response):
    """Ensure non-empty sessions are saved and the cookie is set."""
    session = getattr(request, "session", None)
    if session is None:
        return
    try:
        if session.session_key and not session.is_empty():
            session.save()
            cookie_name = settings.SESSION_COOKIE_NAME
            if cookie_name not in response.cookies:
                response.set_cookie(
                    cookie_name,
                    session.session_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    path=settings.SESSION_COOKIE_PATH,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE,
                )
    except Exception:
        pass


@sync_and_async_middleware
def DaphneSessionMiddleware(get_response):
    """
    Placed BEFORE Django's SessionMiddleware in MIDDLEWARE so on the
    *response* path it runs AFTER SessionMiddleware as a safety-net.
    Works under both WSGI and ASGI (Daphne).
    """
    if iscoroutinefunction(get_response):
        async def middleware(request):
            response = await get_response(request)
            await sync_to_async(_patch_session_cookie, thread_sensitive=True)(request, response)
            return response
    else:
        def middleware(request):
            response = get_response(request)
            _patch_session_cookie(request, response)
            return response

    return middleware
