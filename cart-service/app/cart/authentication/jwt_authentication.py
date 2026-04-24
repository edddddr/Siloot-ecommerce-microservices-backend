import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class SimpleUser:
    """A lightweight user object for microservices"""
    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(
                token,
                settings.AUTH_PUBLIC_KEY,
                algorithms=["RS256"],
            )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Invalid token payload")

            # RETURN A SIMPLE OBJECT INSTEAD OF A RAW ID
            return (SimpleUser(user_id), None)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except (jwt.InvalidTokenError, IndexError):
            raise AuthenticationFailed("Invalid token")