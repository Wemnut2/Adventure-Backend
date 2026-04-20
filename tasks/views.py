# tasks/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Task, UserTaskInvestment
from .serializers import TaskSerializer, UserTaskInvestmentSerializer
from accounts.models import ActivityLog


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """View for users to see available tasks"""
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserTaskInvestmentViewSet(viewsets.ModelViewSet):
    """View for users to invest in tasks"""
    serializer_class = UserTaskInvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserTaskInvestment.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def invest(self, request, pk=None):
        """User invests in a task with selected tier"""
        task = Task.objects.get(id=pk)
        tier = request.data.get('tier', 'bronze')
        
        # Get price and reward based on tier
        if tier == 'bronze':
            amount = task.bronze_price
            reward = task.bronze_reward
        elif tier == 'silver':
            amount = task.silver_price
            reward = task.silver_reward
        elif tier == 'gold':
            amount = task.gold_price
            reward = task.gold_reward
        else:
            return Response({'error': 'Invalid tier'}, status=400)
        
        # Create investment
        investment = UserTaskInvestment.objects.create(
            user=request.user,
            task=task,
            tier=tier,
            amount=amount,
            reward_amount=reward,
            status='pending'
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action=f"Invested in {task.title} ({tier} tier) - ${amount}",
            ip_address=self.get_client_ip(request)
        )
        
        serializer = self.get_serializer(investment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        investment = self.get_object()
        if investment.status == 'pending':
            investment.status = 'cancelled'
            investment.save()
            return Response({'status': 'cancelled'})
        return Response({'error': 'Cannot cancel'}, status=400)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')