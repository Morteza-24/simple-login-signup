from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import StartAuthView, VerifyOTPView, CompleteSignupView, DefendedTokenObtainPairView


urlpatterns = [
    path('api/auth/start/', StartAuthView.as_view(), name='auth_start'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('api/auth/complete-signup/', CompleteSignupView.as_view(), name='auth_complete_signup'),
    path('api/token/', DefendedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
