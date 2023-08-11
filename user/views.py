from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

import binascii
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import reverse, get_object_or_404
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.conf import settings

from .serializers import UserRegistrationSerializer


User = get_user_model()


class MyTokenObtainSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username

        return token


class TokenObtainView(TokenObtainPairView):
    serializer_class = MyTokenObtainSerializer


class UserRegistration(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reg_serializer = UserRegistrationSerializer(data=request.data)

        if reg_serializer.is_valid():
            new_user = reg_serializer.save()
            if new_user:
                # Generate verification token
                token_generator = default_token_generator
                uid = urlsafe_base64_encode(force_str(new_user.pk).encode())
                token = token_generator.make_token(new_user)

                # Send verification email
                verification_link = reverse(
                    "verify_email", kwargs={"uidb64": uid, "token": token}
                )
                verification_url = verification_link.replace(
                    "/api/user/", settings.FRONT_END
                )
                print(verification_url, "------------------")
                email_subject = "Verify your email address"
                email_body_html = render_to_string(
                    "verification_email.html",
                    {"user": new_user, "verification_url": verification_url},
                )
                email_body_text = strip_tags(email_body_html)

                # Create the email message
                email_message = EmailMultiAlternatives(
                    email_subject,
                    email_body_text,
                    "t4technow@gmail.com",
                    [new_user.email],
                )
                email_message.attach_alternative(email_body_html, "text/html")

                try:
                    # Send the email
                    email_message.send()
                except Exception as e:
                    new_user.delete()
                    return Response(
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        data={"message": "could not send email"},
                    )

                return Response(status=status.HTTP_201_CREATED)

        return Response(reg_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlacklistTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class VerifyEmail(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs["uidb64"]
        token = kwargs["token"]
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            if user.is_active:
                response_data = {
                    "email": user.email,
                }
                return Response(status=status.HTTP_409_CONFLICT, data=response_data)
            else:
                user.is_active = True
                user.save()
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                response_data = {
                    "access": str(access_token),
                    "refresh": str(refresh),
                }

                return Response(status=status.HTTP_200_OK, data=response_data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data="user does not exist")
