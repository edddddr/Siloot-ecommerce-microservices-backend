from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserRole
from users.services import publish_user_created, log_login_attempt


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "role")

    def create(self, validated_data):
        password = validated_data.pop("password")


        user = User.objects.create_user(password=password, **validated_data)
        
        user.save()

        publish_user_created(user)

        return user




class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])

        if not user:
            log_login_attempt(data["email"], False)
            raise serializers.ValidationError("Invalid credentials")
        
        log_login_attempt(data["email"], True)
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role if user.role else None
        refresh["email"] = user.email

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }