# investments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Investment, Transaction
from admin_panel.models import AdminNotification

@receiver(post_save, sender=Investment)
def notify_admin_new_investment(sender, instance, created, **kwargs):
    if created:
        AdminNotification.objects.create(
            type='investment',
            title='New Investment Request',
            message=f"{instance.user.email} invested ${instance.amount} in {instance.plan.name}",
            link=f"/admin/investments/{instance.id}/change/",
            is_read=False
        )

@receiver(post_save, sender=Transaction)
def notify_admin_transaction(sender, instance, created, **kwargs):
    if created and instance.transaction_type == 'withdrawal':
        AdminNotification.objects.create(
            type='withdrawal',
            title='New Withdrawal Request',
            message=f"{instance.user.email} requested withdrawal of ${instance.amount}",
            link=f"/admin/transactions/{instance.id}/change/",
            is_read=False
        )