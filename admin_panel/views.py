# admin_panel/views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, Q
from django.utils import timezone
from accounts.models import User, ActivityLog, UserProfile
from investments.models import InvestmentPlan, UserInvestment, InvestmentTransaction
from tasks.models import Task, UserTaskInvestment  # Changed from UserTask
from .models import AdminAction, SystemSettings
from .serializers import (
    UserManagementSerializer, UserInvestmentSerializer, InvestmentPlanSerializer, 
    TaskManagementSerializer, AdminActionSerializer, SystemSettingsSerializer,
    DashboardStatsSerializer, ChallengeParticipantSerializer, InvestmentTransactionSerializer,
    UserTaskInvestmentSerializer  # Added this import
)
from .permissions import IsAdminUser


class AdminTaskInvestmentViewSet(viewsets.ModelViewSet):
    """Admin view for managing user task investments"""
    permission_classes = [IsAdminUser]
    serializer_class = UserTaskInvestmentSerializer
    queryset = UserTaskInvestment.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a pending task investment and start countdown"""
        investment = self.get_object()
        
        if investment.status != 'pending':
            return Response({'error': 'Investment already processed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'active'
        investment.admin_notes = request.data.get('admin_notes', 'Investment verified')
        investment.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Verify Task Investment",
            target_user=investment.user,
            details=f"Verified {investment.task.title} ({investment.tier}) - ${investment.amount}"
        )
        
        return Response({
            'status': 'activated',
            'message': f'Investment verified! 30-day countdown started for {investment.task.title}.',
            'end_date': investment.end_date
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending task investment"""
        investment = self.get_object()
        investment.status = 'cancelled'
        investment.admin_notes = request.data.get('reason', 'Investment rejected')
        investment.save()
        return Response({'status': 'rejected'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark an active task investment as completed"""
        investment = self.get_object()
        
        if investment.status != 'active':
            return Response({'error': 'Only active investments can be completed'},
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'completed'
        investment.completed_date = timezone.now()
        investment.save()
        
        return Response({
            'status': 'completed',
            'total_return': investment.reward_amount,
            'profit': investment.profit
        })


class AdminInvestmentManagementViewSet(viewsets.ModelViewSet):
    """Admin view for managing user investments"""
    permission_classes = [IsAdminUser]
    serializer_class = UserInvestmentSerializer
    queryset = UserInvestment.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def verify_investment(self, request, pk=None):
        """Admin verifies the investment and starts the countdown"""
        investment = self.get_object()
        
        if investment.status != 'pending':
            return Response({'error': 'Investment already processed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Activate the investment
        investment.status = 'active'
        investment.verified_by = request.user
        investment.verified_at = timezone.now()
        investment.admin_notes = request.data.get('admin_notes', 'Investment verified')
        investment.save()
        
        # Log the action
        AdminAction.objects.create(
            admin=request.user,
            action_type="Verify Investment",
            target_user=investment.user,
            details=f"Verified investment of ${investment.amount} in {investment.plan.name}"
        )
        
        return Response({
            'status': 'activated',
            'message': 'Investment verified! 30-day countdown started.',
            'end_date': investment.end_date
        })
    
    @action(detail=True, methods=['post'])
    def reject_investment(self, request, pk=None):
        """Admin rejects the investment"""
        investment = self.get_object()
        investment.status = 'cancelled'
        investment.admin_notes = request.data.get('reason', 'Investment rejected')
        investment.save()
        
        return Response({'status': 'rejected', 'message': 'Investment rejected'})
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Admin marks investment as completed"""
        investment = self.get_object()
        
        if investment.status != 'active':
            return Response({'error': 'Only active investments can be completed'},
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'completed'
        investment.completed_date = timezone.now()
        investment.total_profit = investment.expected_return_amount - investment.amount
        investment.save()
        
        return Response({
            'status': 'completed',
            'total_return': investment.expected_return_amount,
            'message': 'Investment completed. User can now withdraw.'
        })


class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = DashboardStatsSerializer
    
    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        subscribed_users = User.objects.filter(is_subscribed=True).count()
        active_investments = UserInvestment.objects.filter(status='active').count()
        total_volume = UserInvestment.objects.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
        completed_tasks = UserTaskInvestment.objects.filter(status='completed').count()  # Changed from UserTask
        pending_approvals = UserInvestment.objects.filter(status='payment_review').count()
        challenge_participants = UserProfile.objects.exclude(challenge_status='pending').exclude(full_name__isnull=True).count()
        
        recent_users = User.objects.order_by('-created_at')[:10]
        recent_activities = ActivityLog.objects.order_by('-created_at')[:20]
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'subscribed_users': subscribed_users,
            'active_investments': active_investments,
            'total_volume': total_volume,
            'completed_tasks': completed_tasks,
            'pending_approvals': pending_approvals,
            'challenge_participants': challenge_participants,
            'recent_users': UserManagementSerializer(recent_users, many=True).data,
            'recent_activities': list(recent_activities.values('user__email', 'action', 'created_at'))
        }
        
        serializer = self.get_serializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def toggle_subscription(self, request, pk=None):
        user = self.get_object()
        user.is_subscribed = not user.is_subscribed
        if user.is_subscribed:
            user.subscription_start_date = timezone.now()
            user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
        user.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Toggle Subscription",
            target_user=user,
            details=f"Subscription status changed to {user.is_subscribed}"
        )
        
        return Response({'status': 'updated', 'is_subscribed': user.is_subscribed})
    
    @action(detail=True, methods=['post'])
    def update_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role in ['user', 'admin', 'super_admin']:
            user.role = new_role
            user.save()
            
            AdminAction.objects.create(
                admin=request.user,
                action_type="Update Role",
                target_user=user,
                details=f"Role updated to {new_role}"
            )
            
            return Response({'status': 'updated', 'role': user.role})
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_user(self, request, pk=None):
        user = self.get_object()
        user_email = user.email
        user.delete()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Delete User",
            details=f"Deleted user: {user_email}"
        )
        
        return Response({'status': 'deleted'})


class AdminInvestmentPlanViewSet(viewsets.ModelViewSet):
    """Admin view for managing investment plans"""
    permission_classes = [IsAdminUser]
    serializer_class = InvestmentPlanSerializer
    queryset = InvestmentPlan.objects.all().order_by('-created_at')



class AdminUserInvestmentViewSet(viewsets.ModelViewSet):
    """Admin view for managing user investments"""
    permission_classes = [IsAdminUser]
    serializer_class = UserInvestmentSerializer
    queryset = UserInvestment.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a pending investment and start countdown"""
        investment = self.get_object()
        
        if investment.status != 'pending':
            return Response({'error': 'Investment already processed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'active'
        investment.admin_notes = request.data.get('admin_notes', 'Investment verified')
        investment.save()
        
        # Create admin action log
        AdminAction.objects.create(
            admin=request.user,
            action_type="Verify Investment",
            target_user=investment.user,
            details=f"Verified investment of ${investment.amount} in {investment.plan.name}"
        )
        
        return Response({
            'status': 'activated',
            'message': f'Investment verified! {investment.plan.duration_days}-day countdown started.',
            'end_date': investment.end_date
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending investment"""
        investment = self.get_object()
        
        if investment.status != 'pending':
            return Response({'error': 'Investment already processed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'cancelled'
        investment.admin_notes = request.data.get('reason', 'Investment rejected')
        investment.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Reject Investment",
            target_user=investment.user,
            details=f"Rejected investment of ${investment.amount}. Reason: {investment.admin_notes}"
        )
        
        return Response({'status': 'rejected', 'message': 'Investment rejected'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark an active investment as completed"""
        investment = self.get_object()
        
        if investment.status != 'active':
            return Response({'error': 'Only active investments can be completed'},
                          status=status.HTTP_400_BAD_REQUEST)
        
        investment.status = 'completed'
        investment.completed_date = timezone.now()
        investment.total_profit = investment.expected_return_amount - investment.amount
        investment.save()
        
        AdminAction.objects.create(
            admin=request.user,
            action_type="Complete Investment",
            target_user=investment.user,
            details=f"Marked investment as completed. Total return: ${investment.expected_return_amount}"
        )
        
        return Response({
            'status': 'completed',
            'total_return': investment.expected_return_amount,
            'message': 'Investment marked as completed.'
        })

# admin_panel/views.py - Make sure AdminTaskViewSet is properly configured
from tasks.models import Task
from tasks.serializers import TaskSerializer

class AdminTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TaskSerializer
    queryset = Task.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        task = serializer.save()
        AdminAction.objects.create(
            admin=self.request.user,
            action_type="Create Task",
            details=f"Created task: {task.title}"
        )
        return task


class AdminTransactionViewSet(viewsets.ModelViewSet):
    queryset = InvestmentTransaction.objects.all().order_by('-created_at')
    serializer_class = InvestmentTransactionSerializer
    permission_classes = [IsAdminUser]


class SystemSettingsViewSet(viewsets.ModelViewSet):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        key = request.query_params.get('key')
        try:
            setting = SystemSettings.objects.get(key=key)
            return Response({'key': setting.key, 'value': setting.value})
        except SystemSettings.DoesNotExist:
            return Response({'error': 'Setting not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing challenge participants
    """
    permission_classes = [IsAdminUser]
    serializer_class = ChallengeParticipantSerializer
    
    def get_queryset(self):
        """Return all user profiles that have challenge registrations"""
        return UserProfile.objects.exclude(
            challenge_status='pending'
        ).exclude(
            full_name__isnull=True
        ).exclude(
            full_name=''
        ).order_by('-challenge_start_date')
    
    @action(detail=True, methods=['post'])
    def approve_fee(self, request, pk=None):
        """Approve registration or insurance fee"""
        try:
            profile = UserProfile.objects.get(user__id=pk)
            fee_type = request.data.get('fee_type')
            
            if fee_type == 'registration':
                profile.registration_fee_paid = True
                message = "Registration fee approved"
            elif fee_type == 'insurance':
                profile.insurance_fee_paid = True
                message = "Insurance fee approved"
            else:
                return Response(
                    {'error': 'Invalid fee type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            profile.save()
            
            AdminAction.objects.create(
                admin=request.user,
                action_type="Approve Challenge Fee",
                target_user=profile.user,
                details=f"Approved {fee_type} fee for challenge participant"
            )
            
            return Response({
                'message': message,
                'status': 'success'
            })
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        """Update challenge status and prize"""
        try:
            profile = UserProfile.objects.get(user__id=pk)
            new_status = request.data.get('challenge_status')
            total_prize = request.data.get('total_prize')
            
            if new_status:
                profile.challenge_status = new_status
                
                if new_status == 'active' and not profile.challenge_start_date:
                    profile.challenge_start_date = timezone.now()
                    profile.challenge_end_date = timezone.now() + timezone.timedelta(days=60)
                
                if new_status == 'completed':
                    profile.challenge_completed_date = timezone.now()
                
                if new_status == 'failed':
                    profile.challenge_status = 'failed'
            
            if total_prize:
                profile.total_prize = total_prize
            
            profile.save()
            
            AdminAction.objects.create(
                admin=request.user,
                action_type="Update Challenge Status",
                target_user=profile.user,
                details=f"Updated challenge status to {new_status} with prize ${total_prize}"
            )
            
            return Response({
                'message': f'Challenge status updated to {new_status}',
                'challenge_status': profile.challenge_status
            })
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )