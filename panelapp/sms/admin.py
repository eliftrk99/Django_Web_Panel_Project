from django.contrib import admin
from .models import SMSLog
from django.utils.html import format_html


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    """SMS gönderi logları yönetimi"""
    list_display = ('created_at', 'sender', 'recipient', 'get_status_badge', 'message_preview', 'twilio_status')
    list_filter = ('status', 'created_at', 'sender')
    search_fields = ('recipient', 'message', 'sender__username')
    readonly_fields = ('twilio_sid', 'sent_at', 'created_at', 'get_full_message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Gönderen Bilgileri', {
            'fields': ('sender', 'created_at')
        }),
        ('Alıcı Bilgileri', {
            'fields': ('recipient',)
        }),
        ('Mesaj', {
            'fields': ('message', 'get_full_message')
        }),
        ('Durum', {
            'fields': ('status', 'twilio_sid', 'sent_at')
        }),
    )
    
    def get_status_badge(self, obj):
        """Durum rengini göster"""
        colors = {
            'sent': 'green',
            'failed': 'red',
            'pending': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        
        icons = {
            'sent': '✓',
            'failed': '✗',
            'pending': '⋯',
        }
        icon = icons.get(obj.status, '?')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Durum'
    
    def message_preview(self, obj):
        """Mesajın ilk 50 karakterini göster"""
        preview = obj.message[:50] + ('...' if len(obj.message) > 50 else '')
        return preview
    message_preview.short_description = 'Mesaj Ön İzlemesi'
    
    def get_full_message(self, obj):
        """Tam mesajı readonly alanında göster"""
        return obj.message
    get_full_message.short_description = 'Tam Mesaj'
    
    def twilio_status(self, obj):
        """Twilio durum bilgisini göster"""
        if obj.twilio_sid:
            return format_html(
                '<code style="background-color: #f0f0f0; padding: 5px; border-radius: 3px;">{}</code>',
                obj.twilio_sid
            )
        return format_html('<span style="color: gray;">-</span>')
    twilio_status.short_description = 'Twilio SID'
    
    actions = ['mark_as_sent', 'mark_as_failed', 'mark_as_pending']
    
    def mark_as_sent(self, request, queryset):
        """Toplu olarak gönderilen olarak işaretle"""
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} SMS gönderildi olarak işaretlendi.')
    mark_as_sent.short_description = 'Gönderilen olarak işaretle'
    
    def mark_as_failed(self, request, queryset):
        """Toplu olarak başarısız olarak işaretle"""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} SMS başarısız olarak işaretlendi.')
    mark_as_failed.short_description = 'Başarısız olarak işaretle'
    
    def mark_as_pending(self, request, queryset):
        """Toplu olarak beklemede olarak işaretle"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} SMS beklemede olarak işaretlendi.')
    mark_as_pending.short_description = 'Beklemede olarak işaretle'
    
    def has_add_permission(self, request):
        """SMS loglarının admin üzerinden elle eklenmesini engelle"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Sadece superuser'lar silebilsin"""
        return request.user.is_superuser
