from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import throttling
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from defender import utils
from phonenumber_field.phonenumber import PhoneNumber
import random
import uuid
from .models import Profile
from .serializers import StartAuthSerializer, VerifyOTPSerializer, CompleteSignupSerializer, DefendedTokenObtainPairSerializer


def send_otp(phone, otp):
    print(f"send {otp} to {phone}")


class OTPSendingThrottle(throttling.BaseThrottle):
    def allow_request(self, request, view):
        # If the user is signing up, they can only recieve
        # a new OTP once the old one is expired.
        # If the user is already signed up, there is no
        # throttling for login (there is no unexpired OTP).
        phone = PhoneNumber.from_string(request.data["phone"], "IR")
        return not bool(cache.get(f"otp_{str(phone)}"))


class StartAuthView(APIView):
    """
    Handles the first step of authentication (POST).
    Expected request:
        {"phone": "<user_phone_number>"}
    Behavior:
    - If the phone belongs to an existing user, returns 200 with {"detail": ..., "mode": "login"} so the client proceeds to the login page.
    - If the phone is new, checks rate/lock state and, if allowed, generates a 6-digit OTP, caches it for 3 minutes, sends it to the phone, and returns 200 with {"detail": ..., "mode": "signup"} so the client proceeds to signup.
    - If the phone/ip is locked due to too many attempts, returns 403 with an explanatory {"detail": ...}.
    - If input validation fails, returns 400 with serializer errors.
    Notes:
    - A phone number can receive an OTP only once every 3 minutes.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPSendingThrottle]

    def post(self, request):
        serializer = StartAuthSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone"]
            if User.objects.filter(profile__phone=phone).exists():
                # Go to login when phone already exists
                return Response(
                    {"detail": "به نظر میرسه قبلاً ثبت‌نام کردی! انتقال به ورود...",
                     "mode": "login"},
                )
            # Start the signup process when phone doesn't exist
            ip = utils.get_ip(request)
            if utils.is_already_locked(request, username=f"signup:user:{str(phone)}") or utils.is_already_locked(request, username=f"signup:ip:{ip}"):
                detail = f"تعداد تلاش‌های اشتباهت از حد مجاز فراتر رفته. بعداً دوباره تلاش کن."
                return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
            otp = str(random.randint(100000, 999999))  # 6-digit OTP
            cache.set(f"otp_{str(phone)}", otp,
                      timeout=180)  # 3 min expiration
            send_otp(str(phone), otp)  # TODO: use Celery in the future
            return Response({"detail": "کد یک بار مصرف برات ارسال شد!", "mode": "signup"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    Accepts a phone number and an OTP to verify ownership of the phone as the first
    step of the signup flow. On successful verification, issues a short-lived
    temporary token which is used by the next step in the signup process.
    Expected request (application/json):
        {
            "phone": "<phone_number_as_string>",
            "otp": "<one_time_password_as_string>"
        }
    Successful response (HTTP 200):
        {
            "tmp_token": "<temporary_token_string>",
            "detail": "OTP verified successfully"
        }
        - The temporary token is generated and cached for subsequent signup steps on success,
          and it is valid for a short time (10 minutes).
        - The verified OTP is consumed/removed.
    Client errors:
        - HTTP 400: Invalid request payload (validation errors).
        - HTTP 401: Provided OTP is incorrect.
        - HTTP 410: Provided OTP has expired or is not present in the server cache.
    Rate limiting / locking:
        - The endpoint tracks unsuccessful attempts per phone number and per client IP.
        - If a single phone number receives 3 wrong OTP submissions, that phone is blocked for 1 hour.
        - If a single IP address submits 3 wrong phone+OTP combinations, that IP is blocked for 1 hour.
        - When blocked, the endpoint returns HTTP 403 with an explanatory message.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            ip = utils.get_ip(request)
            phone = str(serializer.validated_data["phone"])
            if utils.is_already_locked(request, username=f"signup:user:{phone}") or utils.is_already_locked(request, username=f"signup:ip:{ip}"):
                detail = f"تعداد تلاش‌های اشتباهت از حد مجاز فراتر رفته. بعداً دوباره تلاش کن."
                return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
            user_check, ip_check = True, True
            otp = serializer.validated_data["otp"]
            cached_otp = cache.get(f"otp_{phone}")
            if cached_otp:
                if cached_otp == otp:
                    # Generate a temporary token for the next step
                    token = str(uuid.uuid4())
                    # Link token to phone
                    cache.set(f"signup_token_{token}", phone, timeout=600)
                    cache.delete(f"otp_{phone}")
                    login_unsuccessful = False
                    response = Response(
                        {"tmp_token": token, "detail": "کد یک بار مصرف با موفقیت تایید شد!"}, status=status.HTTP_200_OK)
                else:
                    login_unsuccessful = True
                    response = Response(
                        {"detail": "کد وارد شده اشتباه است!"}, status=status.HTTP_401_UNAUTHORIZED)
                user_check = utils.check_request(
                    request, login_unsuccessful=login_unsuccessful, username=f"signup:user:{phone}")
                ip_check = utils.check_request(
                    request, login_unsuccessful=login_unsuccessful, username=f"signup:ip:{ip}")
            else:
                response = Response(
                    {"detail": "کد وارد شده منقضی شده است!"}, status=status.HTTP_410_GONE)
            if user_check and ip_check:
                return response
            detail = f"تعداد تلاش‌های اشتباهت از حد مجاز فراتر رفته. بعداً دوباره تلاش کن."
            return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
        response = Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class CompleteSignupView(APIView):
    """
    Finalize a user's signup by submitting the remaining profile information and a one-time signup token
    previously issued in the first step of signup (after phone verification). This endpoint creates
    the user account and associated profile, consumes the signup token, and returns JWT authentication tokens.
    Expected request (application/json):
        {
            "token": "<string>",        # Required. One-time token issued by the initial signup step.
            "first_name": "<string>",   # Required. User's given name.
            "last_name": "<string>",    # Required. User's family name.
            "email": "<string>",        # Required. User's email address.
            "password": "<string>"      # Required. Plain-text password for the new account.
        }
    Success Response (201 Created):
        {
            "detail": "<string>",     # Human-readable success message.
            "refresh": "<string>",    # JWT refresh token (use to obtain new access tokens).
            "access": "<string>"      # JWT access token for authenticated requests.
        }
    Failure Responses:
        - 400 Bad Request: Payload validation errors. Response body contains serializer errors keyed by field.
        - 401 Unauthorized: Token missing or expired.
    Behavior:
        - If the token is missing or expired (no phone found in cache), the endpoint responds with HTTP 401.
        - If the token is valid, a new user is created.
        - Upon successful creation, a JWT refresh token and corresponding access token are returned in the response.
    Notes:
        - Transport security (HTTPS) is required to protect the password in transit.
        - The endpoint issues JWTs (refresh and access). Clients should store the refresh token securely and
          use the access token for authenticated requests until it expires.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CompleteSignupSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]
            phone = cache.get(f"signup_token_{token}")
            if not phone:
                return Response({"detail": "توکن منقضی شده، لطفا دوباره تلاش کن!"}, status=status.HTTP_401_UNAUTHORIZED)
            first_name = serializer.validated_data["first_name"]
            last_name = serializer.validated_data["last_name"]
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            with transaction.atomic():
                user = User.objects.create_user(
                    username=phone, first_name=first_name, last_name=last_name, email=email, password=password)
                Profile.objects.create(
                    user=user, phone=PhoneNumber.from_string(phone, "IR"))
            cache.delete(f"signup_token_{token}")
            # On successful signup, sign the user in
            # by giving them JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "detail": "تبریک! با موفقیت ثبت‌نام شدی.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DefendedTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint for obtaining JWT access and refresh tokens with defensive
    rate-limiting and lockout checks applied per username and per IP address.

    Behavior:
        - If a single phone number receives 3 wrong password submissions, that phone is blocked for 1 hour.
        - If a single IP address submits 3 wrong phone+password combinations, that IP is blocked for 1 hour.
        - When blocked, the endpoint returns HTTP 403 with an explanatory message.
    Request (application/json):
            {
                "username": "<phone_number>",
                "password": "<password>"
            }
    Responses:
        200 OK
            {
                "access": "<access_token>",
                "refresh": "<refresh_token>"
            }
        403 Forbidden: Returned when a user- or IP-level lockout is in effect.
        400 / 401: Returned for malformed requests or invalid credentials.
    """

    def post(self, request):
        serializer = DefendedTokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            ip = utils.get_ip(request)
            username = str(serializer.validated_data["username"])  # validated & normalized phone number
            if utils.is_already_locked(request, username=f"login:user:{username}") or utils.is_already_locked(request, username=f"login:ip:{ip}"):
                detail = f"تعداد تلاش‌های اشتباهت از حد مجاز فراتر رفته. بعداً دوباره تلاش کن."
                return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
            login_unsuccessful = False
            request.data["username"] = username
            request.data["password"] = serializer.validated_data["password"]
            try:
                # run the original TokenObtainPairView.post
                response = super().post(request)
            except Exception as e:
                exception = e
                login_unsuccessful = True
            user_check = utils.check_request(
                request, login_unsuccessful=login_unsuccessful, username=f"login:user:{username}")
            ip_check = utils.check_request(
                request, login_unsuccessful=login_unsuccessful, username=f"login:ip:{ip}")
            if user_check and ip_check:
                if login_unsuccessful:
                    raise exception
                return response
            detail = f"تعداد تلاش‌های اشتباهت از حد مجاز فراتر رفته. بعداً دوباره تلاش کن."
            return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
