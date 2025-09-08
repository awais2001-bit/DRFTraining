from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # default to anonymous
        scope['user'] = AnonymousUser()

        # extract cookie header
        cookie_header = dict(scope['headers']).get(b'cookie', b'').decode()
        cookies = dict(kv.strip().split('=') for kv in cookie_header.split(';') if '=' in kv)
        token = cookies.get('access')

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await database_sync_to_async(User.objects.get)(id=payload["user_id"])
                scope['user'] = user
            except Exception:
                scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)


# Helper to add easily to routing
def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
