# investments/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import InvestmentPlan, UserInvestment, InvestmentTransaction
from .serializers import (
    InvestmentPlanSerializer, 
    UserInvestmentSerializer, 
    InvestmentTransactionSerializer
)
from accounts.models import ActivityLog


class InvestmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """View for users to see available investment plans"""
    queryset = InvestmentPlan.objects.filter(is_active=True)
    serializer_class = InvestmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserInvestmentViewSet(viewsets.ModelViewSet):
    """View for users to manage their investments"""
    serializer_class = UserInvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserInvestment.objects.none()
        return UserInvestment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        investment = serializer.save(user=self.request.user, status='pending')
        
        ActivityLog.objects.create(
            user=self.request.user,
            action=f"Requested investment of ${investment.amount} in {investment.plan.name}",
            ip_address=self.get_client_ip()
        )
        
        return investment
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        investment = self.get_object()
        if investment.status == 'pending':
            investment.status = 'cancelled'
            investment.save()
            return Response({'status': 'cancelled', 'message': 'Investment cancelled'})
        return Response({'error': 'Cannot cancel this investment'}, status=400)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


class InvestmentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """View for users to see their investment transactions"""
    serializer_class = InvestmentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InvestmentTransaction.objects.none()
        return InvestmentTransaction.objects.filter(
            user_investment__user=self.request.user
        ).order_by('-created_at')