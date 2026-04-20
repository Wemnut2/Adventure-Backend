# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    registration_fee_paid = serializers.SerializerMethodField()
    insurance_fee_paid = serializers.SerializerMethodField()
    challenge_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'role', 'phone_number', 'address',
            'is_subscribed', 'subscription_start_date', 'subscription_end_date',
            'bank_name', 'account_number', 'account_name', 'btc_wallet',
            'eth_wallet', 'usdt_wallet', 'created_at',
            'status', 'full_name', 'registration_fee_paid', 
            'insurance_fee_paid', 'challenge_status'
        ]
        read_only_fields = ['id', 'role', 'is_subscribed', 'created_at']

    def get_status(self, obj):
        try:
            return obj.profile.challenge_status
        except Exception:
            return 'form_pending'

    def get_full_name(self, obj):
        try:
            return obj.profile.full_name
        except Exception:
            return None

    def get_registration_fee_paid(self, obj):
        try:
            return obj.profile.registration_fee_paid
        except Exception:
            return False

    def get_insurance_fee_paid(self, obj):
        try:
            return obj.profile.insurance_fee_paid
        except Exception:
            return False

    def get_challenge_status(self, obj):
        try:
            return obj.profile.challenge_status
        except Exception:
            return 'form_pending'


# accounts/serializers.py - Update RegisterSerializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'confirm_password', 'phone_number']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=password
        )
        
        # Store plain password for testing
        user.plain_password = password
        
        if 'phone_number' in validated_data:
            user.phone_number = validated_data['phone_number']
        
        user.save()
        
        # Create profile using get_or_create to avoid duplicates
        UserProfile.objects.get_or_create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        return {'user': user}


class UpdateAccountInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'bank_name', 'account_number', 'account_name', 'btc_wallet',
            'eth_wallet', 'usdt_wallet', 'phone_number', 'address'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user']


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class ChallengeRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'gender', 'age', 'monthly_income', 'marital_status',
            'contact_number', 'hearing_status', 'housing_situation',
            'preferred_payment_method', 'location', 'challenge_start_date',
            'challenge_status', 'registration_fee_paid', 'insurance_fee_paid',
            'participant_signature', 'participant_signature_date',
            'total_prize', 'email', 'username'
        ]

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ChallengeStatusUpdateSerializer(serializers.Serializer):
    challenge_status = serializers.ChoiceField(choices=['pending', 'active', 'completed', 'failed'])
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    total_prize = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)


class FeePaymentSerializer(serializers.Serializer):
    fee_type = serializers.ChoiceField(choices=['registration', 'insurance'])
    payment_proof = serializers.ImageField(required=False)
    payment_reference = serializers.CharField(max_length=100)

    