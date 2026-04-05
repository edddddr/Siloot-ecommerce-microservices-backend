import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer
from .tokens import InternalServiceToken
from rest_framework.throttling import ScopedRateThrottle

import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(
            "Registration attempt",
            extra={
                "ip": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "email": request.data.get("email"),  # Useful for debugging sign-up issues
            }
        )

        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            logger.info(
                "User registered successfully", 
                extra={"email": request.data.get("email")}
            )

            return Response({"message": "User registered"}, status=status.HTTP_201_CREATED)

        except Exception as e:

            logger.error(
                "Registration failed", 
                extra={
                    "error": str(e),
                    "ip": request.META.get("REMOTE_ADDR")
                }
            )
            raise


class LoginView(APIView):
    
        permission_classes = [AllowAny]
        throttle_classes = [ScopedRateThrottle]
        throttle_scope = "login"

        def post(self, request):
            
            # with tracer.start_as_current_span("login-span"):
            logger.info(
                "Login attempt ",
                extra={
                        "ip": request.META.get("REMOTE_ADDR"),
                        "user_agent": request.META.get("HTTP_USER_AGENT"),
                    })


            try: 
                serializer = LoginSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                return Response(serializer.validated_data)

            except Exception as e:
                logger.error("Login failed", extra={"error": str(e)})
                raise

class LogoutView(APIView):
    def post(self, request):

        current_user_id = request.user.id if request.user.is_authenticated else "Anonymous"

        logger.info(
            "Logout attempt",
            extra={
                "user_id": current_user_id,
                "ip": request.META.get("REMOTE_ADDR"),
            }
        )

        try:
            refresh_token = request.data["refresh"]
            if not refresh_token:
                logger.warning("Logout failed: No refresh token provided")
                return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(
                "User logged out successfully",
                extra={"user_id": current_user_id}
            )
            return Response(status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            logger.error(
                "Logout error",
                extra={
                    "error": str(e),
                    "user_id": current_user_id
                }
            )
            return Response({"error": "Invalid or already blacklisted token"}, status=status.HTTP_400_BAD_REQUEST)



class InternalTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        logger.info(
            "Internal token request received",
            extra={
                "service_name": service_name,
                "ip": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
            }
        )

        shared_secret = request.headers.get("X-Internal-Secret")

        if shared_secret != os.getenv("INTERNAL_SERVICE_SECRET"):
            logger.warning(
                "Unauthorized internal access attempt",
                extra={
                    "service_name": service_name,
                    "ip": request.META.get("REMOTE_ADDR"),
                }
            )
            return Response({"error": "Unauthorized"}, status=403)
        
        service_name = request.data.get("service_name")

        if not service_name:
            logger.error("Internal token request failed: missing service_name")
            return Response({"error": "service_name required"}, status=400)
        
        try:
            # Generate the token
            token = InternalServiceToken.for_service(service_name)

            # 4. Log successful token generation
            logger.info(
                "Internal token generated successfully",
                extra={"service_name": service_name}
            )
            return Response({"access": str(token)})

        except Exception as e:
            logger.error(
                "Failed to generate internal token",
                extra={"service_name": service_name, "error": str(e)}
            )
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
