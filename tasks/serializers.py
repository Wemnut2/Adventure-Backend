# tasks/serializers.py
from rest_framework import serializers
from .models import Task, UserTaskInvestment


class TaskSerializer(serializers.ModelSerializer):
    video_url_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = '__all__'
    
    def get_video_url_display(self, obj):
        if obj.video and obj.video.url:
            return obj.video.url
        return obj.video_url


class UserTaskInvestmentSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')
    task_description = serializers.ReadOnlyField(source='task.description')
    task_video = serializers.SerializerMethodField()
    task_video_url = serializers.ReadOnlyField(source='task.video_url')
    user_email = serializers.ReadOnlyField(source='user.email')
    days_remaining = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    profit = serializers.ReadOnlyField()
    
    def get_task_video(self, obj):
        """Safely get the video URL or return None"""
        try:
            if obj.task.video and obj.task.video.url:
                return obj.task.video.url
        except (ValueError, AttributeError):
            pass
        return None
    
    class Meta:
        model = UserTaskInvestment
        fields = [
            'id', 'user', 'user_email', 'task', 'task_title', 'task_description',
            'task_video', 'task_video_url', 'tier', 'amount', 'reward_amount', 
            'status', 'admin_notes', 'start_date', 'end_date', 'completed_date', 
            'created_at', 'updated_at', 'days_remaining', 'progress_percentage', 'profit'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']