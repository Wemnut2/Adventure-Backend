# accounts/views.py
from django.utils import timezone  
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from .models import User, UserProfile, ActivityLog
from django.db.models import Q
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, 
    UpdateAccountInfoSerializer, UserProfileSerializer, ActivityLogSerializer, 
    ChallengeRegistrationSerializer, 
    ChallengeStatusUpdateSerializer,
    FeePaymentSerializer
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

## accounts/views.py - Update RegisterView
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Get or create profile instead of just create
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Set plain password for testing
        password = self.request.data.get('password')
        if password:
            user.plain_password = password
            user.save()
        
        ActivityLog.objects.create(
            user=user, 
            action="User registered", 
            ip_address=self.get_client_ip()
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            ActivityLog.objects.create(user=user, action="User logged in", ip_address=self.get_client_ip(request))
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            ActivityLog.objects.create(user=request.user, action="User logged out", ip_address=self.get_client_ip())
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

        
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # ← Handle status update — writes to UserProfile.challenge_status
        new_status = request.data.get('status')
        if new_status:
            try:
                instance.profile.challenge_status = new_status
                instance.profile.save()
            except Exception:
                pass

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        ActivityLog.objects.create(
            user=request.user,
            action="Updated profile",
            ip_address=self.get_client_ip()
        )

        return Response(serializer.data)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class UpdateAccountInfoView(generics.UpdateAPIView):
    serializer_class = UpdateAccountInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        ActivityLog.objects.create(user=request.user, action="Updated account information", ip_address=self.get_client_ip())
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip



class MyActivitiesView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ActivityLog.objects.none()
        
        queryset = ActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
        
        # Support ?search= query param
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(action__icontains=search) | Q(details__icontains=search)
            )
            return queryset  # No slice when searching
        
        return queryset[:20]  # Default: last 20

class CheckSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        is_subscribed = user.has_subscription()
        
        return Response({
            'is_subscribed': is_subscribed,
            'subscription_end_date': user.subscription_end_date,
            'subscription_active': user.is_subscribed and is_subscribed
        })


# accounts/views.py - Update all challenge views

class ChallengeRegistrationView(generics.RetrieveUpdateAPIView):
    serializer_class = ChallengeRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Auto-fill some fields from user data
        if not instance.full_name:
            instance.full_name = request.user.get_full_name() or request.user.username
        
        if not instance.contact_number and request.user.phone_number:
            instance.contact_number = request.user.phone_number
        
        self.perform_update(serializer)
        
        ActivityLog.objects.create(
            user=request.user,
            action="Updated challenge registration",
            details=f"Updated challenge information",
            ip_address=self.get_client_ip(request)
        )
        
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ChallengeStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        return Response({
            'challenge_status': profile.challenge_status,
            'start_date': profile.challenge_start_date,
            'end_date': profile.challenge_end_date,
            'total_prize': profile.total_prize,
            'registration_fee_paid': profile.registration_fee_paid,
            'insurance_fee_paid': profile.insurance_fee_paid,
            'challenge_completed_date': profile.challenge_completed_date,
            'reward_claimed': profile.challenge_reward_claimed
        })
    
    def post(self, request):
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        action = request.data.get('action')
        
        if action == 'start_challenge':
            if profile.registration_fee_paid and profile.insurance_fee_paid:
                profile.challenge_status = 'active'
                profile.challenge_start_date = timezone.now()
                profile.challenge_end_date = timezone.now() + timezone.timedelta(days=30)
                profile.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action="Started challenge",
                    details="Challenge started",
                    ip_address=self.get_client_ip(request)
                )
                
                return Response({'message': 'Challenge started successfully', 'status': 'active'})
            else:
                return Response({'error': 'Please pay all fees before starting the challenge'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'complete_challenge':
            if profile.challenge_status == 'active':
                profile.challenge_status = 'completed'
                profile.challenge_completed_date = timezone.now()
                profile.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action="Completed challenge",
                    details="Challenge completed successfully",
                    ip_address=self.get_client_ip(request)
                )
                
                return Response({'message': 'Challenge completed! You can now claim your reward', 'status': 'completed'})
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SubmitChallengeRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        serializer = ChallengeRegistrationSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Set challenge start date
            if not profile.challenge_start_date:
                profile.challenge_start_date = timezone.now()
            
            # Set participant signature
            if not profile.participant_signature:
                profile.participant_signature = f"Signed by {request.user.username}"
                profile.participant_signature_date = timezone.now()
            
            serializer.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action="Submitted challenge registration",
                details="Challenge registration form submitted",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': 'Challenge registration submitted successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ChallengeStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        profile = request.user.profile
        return Response({
            'challenge_status': profile.challenge_status,
            'start_date': profile.challenge_start_date,
            'end_date': profile.challenge_end_date,
            'total_prize': profile.total_prize,
            'registration_fee_paid': profile.registration_fee_paid,
            'insurance_fee_paid': profile.insurance_fee_paid,
            'challenge_completed_date': profile.challenge_completed_date,
            'reward_claimed': profile.challenge_reward_claimed
        })
    
    def post(self, request):
        profile = request.user.profile
        action = request.data.get('action')
        
        if action == 'start_challenge':
            if profile.registration_fee_paid and profile.insurance_fee_paid:
                profile.challenge_status = 'active'
                profile.challenge_start_date = timezone.now()
                profile.challenge_end_date = timezone.now() + timezone.timedelta(days=30)
                profile.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action="Started challenge",
                    details="Challenge started",
                    ip_address=self.get_client_ip(request)
                )
                
                return Response({'message': 'Challenge started successfully', 'status': 'active'})
            else:
                return Response({'error': 'Please pay all fees before starting the challenge'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'complete_challenge':
            if profile.challenge_status == 'active':
                profile.challenge_status = 'completed'
                profile.challenge_completed_date = timezone.now()
                profile.save()
                
                ActivityLog.objects.create(
                    user=request.user,
                    action="Completed challenge",
                    details="Challenge completed successfully",
                    ip_address=self.get_client_ip(request)
                )
                
                return Response({'message': 'Challenge completed! You can now claim your reward', 'status': 'completed'})
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AdminChallengeManagementView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        status_filter = request.query_params.get('status', None)
        queryset = UserProfile.objects.all()
        
        if status_filter:
            queryset = queryset.filter(challenge_status=status_filter)
        
        serializer = ChallengeRegistrationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def put(self, request, user_id):
        try:
            profile = UserProfile.objects.get(user__id=user_id)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChallengeStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            profile.challenge_status = serializer.validated_data['challenge_status']
            if 'admin_notes' in serializer.validated_data:
                profile.admin_notes = serializer.validated_data['admin_notes']
            if 'total_prize' in serializer.validated_data:
                profile.total_prize = serializer.validated_data['total_prize']
            
            # If completing challenge, set completion date
            if profile.challenge_status == 'completed' and not profile.challenge_completed_date:
                profile.challenge_completed_date = timezone.now()
            
            profile.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action="Admin updated challenge status",
                details=f"Updated challenge status to {profile.challenge_status} for user {profile.user.email}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({'message': 'Challenge status updated successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, user_id):
        """Approve fee payment"""
        try:
            profile = UserProfile.objects.get(user__id=user_id)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FeePaymentSerializer(data=request.data)
        if serializer.is_valid():
            fee_type = serializer.validated_data['fee_type']
            
            if fee_type == 'registration':
                profile.registration_fee_paid = True
                message = "Registration fee approved"
            else:
                profile.insurance_fee_paid = True
                message = "Insurance fee approved"
            
            profile.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action=f"Approved {fee_type} fee",
                details=f"Approved {fee_type} fee for user {profile.user.email}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({'message': message})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ChangePasswordView(APIView):  # ← Remove the indentation (should be at column 0)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        ActivityLog.objects.create(
            user=user,
            action="Changed password",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response({'message': 'Password changed successfully'})

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_activity(request, pk):
    """Delete a specific activity log entry for the authenticated user"""
    try:
        activity = ActivityLog.objects.get(id=pk, user=request.user)
        activity.delete()
        return Response(
            {'message': 'Activity deleted successfully'}, 
            status=status.HTTP_200_OK
        )
    except ActivityLog.DoesNotExist:
        return Response(
            {'error': 'Activity not found or you do not have permission to delete it'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )        