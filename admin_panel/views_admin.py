# admin_panel/views_admin.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.models import User
from investments.models import Investment, Transaction
from tasks.models import Task, UserTask
from django.db.models import Sum, Count

@staff_member_required
def admin_dashboard_custom(request):
    context = {
        'total_users': User.objects.count(),
        'active_subscriptions': User.objects.filter(is_subscribed=True).count(),
        'total_investments': Investment.objects.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0,
        'pending_tasks': UserTask.objects.filter(status='pending').count(),
        'pending_transactions': Transaction.objects.filter(status='pending').count(),
        'recent_users': User.objects.order_by('-created_at')[:10],
        'recent_transactions': Transaction.objects.order_by('-created_at')[:10],
    }
    return render(request, 'admin/dashboard_custom.html', context)