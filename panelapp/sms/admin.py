from django.contrib import admin
from .models import SMSLog

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipient', 'message']
    readonly_fields = ['twilio_sid', 'sent_at']
