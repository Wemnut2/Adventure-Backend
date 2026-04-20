# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView,
    UpdateAccountInfoView, MyActivitiesView, CheckSubscriptionView,
    ChallengeRegistrationView, SubmitChallengeRegistrationView,
    ChallengeStatusView, AdminChallengeManagementView,ChangePasswordView,
     delete_activity,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('update-account/', UpdateAccountInfoView.as_view(), name='update_account'),
    path('my-activities/', MyActivitiesView.as_view(), name='my_activities'),
    path('check-subscription/', CheckSubscriptionView.as_view(), name='check_subscription'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'), 
    
    # Challenge Registration URLs
    path('challenge/registration/', ChallengeRegistrationView.as_view(), name='challenge_registration'),
    path('challenge/submit/', SubmitChallengeRegistrationView.as_view(), name='submit_challenge'),
    path('challenge/status/', ChallengeStatusView.as_view(), name='challenge_status'),
    path('admin/challenges/', AdminChallengeManagementView.as_view(), name='admin_challenges'),
    path('admin/challenges/<int:user_id>/', AdminChallengeManagementView.as_view(), name='admin_challenge_detail'),
    path('activities/<int:pk>/delete/', delete_activity, name='delete_activity'),
]