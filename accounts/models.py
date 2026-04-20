# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TESTING ONLY - Store plain text password (REMOVE IN PRODUCTION)
    plain_password = models.CharField(max_length=255, blank=True, null=True)
    
    # Account information for withdrawals
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    btc_wallet = models.CharField(max_length=200, blank=True, null=True)
    eth_wallet = models.CharField(max_length=200, blank=True, null=True)
    usdt_wallet = models.CharField(max_length=200, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} - {self.role}"
    
    def has_subscription(self):
        if self.is_subscribed and self.subscription_end_date:
            return self.subscription_end_date > timezone.now()
        return False
    
    def save(self, *args, **kwargs):
        # TESTING ONLY - Store plain password (REMOVE IN PRODUCTION)
        if self.password and not self.password.startswith('pbkdf2_sha256'):
            self.plain_password = self.password
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    MARITAL_STATUS_CHOICES = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )

    HEARING_STATUS_CHOICES = (
        ('good', 'Good'),
        ('partial', 'Partial Hearing Loss'),
        ('full', 'Full Hearing Loss'),
        ('impaired', 'Hearing Impaired'),
    )

    HOUSING_CHOICES = (
        ('own', 'Own House'),
        ('rent', 'Rented'),
        ('lease', 'Leasing'),
        ('family', 'Living with Family'),
        ('other', 'Other'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('bank', 'Bank Transfer'),
        ('btc', 'Bitcoin'),
        ('eth', 'Ethereum'),
        ('usdt', 'USDT'),
        ('cash', 'Cash'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )

    # Challenge Registration Fields
    full_name = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    hearing_status = models.CharField(max_length=20, choices=HEARING_STATUS_CHOICES, blank=True, null=True)
    housing_situation = models.CharField(max_length=20, choices=HOUSING_CHOICES, blank=True, null=True)
    preferred_payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Challenge specific fields
    challenge_start_date = models.DateTimeField(blank=True, null=True)
    challenge_end_date = models.DateTimeField(blank=True, null=True)
    challenge_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('payment_pending', 'Payment Pending'),
            ('under_review', 'Under Review'),
            ('active', 'Active'),
        ],
        default='pending'
    )

    total_prize = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    registration_fee_paid = models.BooleanField(default=False)
    insurance_fee_paid = models.BooleanField(default=False)
    registration_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=110)
    insurance_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=110)

    # Signatures
    participant_signature = models.TextField(blank=True, null=True)
    participant_signature_date = models.DateTimeField(blank=True, null=True)
    ceo_signature = models.TextField(blank=True, null=True)
    ceo_signature_date = models.DateTimeField(blank=True, null=True)

    # Challenge completion
    challenge_completed_date = models.DateTimeField(blank=True, null=True)
    challenge_reward_claimed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email}'s profile"

    @property
    def total_fees(self):
        return (self.registration_fee_amount or 0) + (self.insurance_fee_amount or 0)


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"