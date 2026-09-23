import urllib.parse

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthMiddleware:
    """
    Authenticate WebSocket connections using a JWT access token.

    WebSocket URL example:

    ws://127.0.0.1:8000/ws/chat/1/?token=<JWT_ACCESS_TOKEN>
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):

        # Default user
        scope["user"] = AnonymousUser()

        # Get query string
        query_string = scope.get(
            "query_string",
            b""
        ).decode()

        query_params = urllib.parse.parse_qs(
            query_string
        )

        token_list = query_params.get("token")

        if not token_list:

            return await self.inner(
                scope,
                receive,
                send
            )

        token = token_list[0]

        try:

            user = await self.get_user_from_token(
                token
            )

            scope["user"] = user

        except Exception:

            scope["user"] = AnonymousUser()

        return await self.inner(
            scope,
            receive,
            send
        )

    @database_sync_to_async
    def get_user_from_token(self, token):

        authentication = JWTAuthentication()

        validated_token = (
            authentication.get_validated_token(
                token
            )
        )

        return authentication.get_user(
            validated_token
        )