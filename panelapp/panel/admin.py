from django.contrib import admin
from .models import Panel, Category, Notification
from django.utils.safestring import mark_safe
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Panel kategorileri yönetimi"""
    list_display = ('name', 'slug', 'get_panel_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def get_panel_count(self, obj):
        count = obj.panel_set.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    get_panel_count.short_description = 'Panel Sayısı'


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    """Panel yönetimi"""
    list_display = ('title', 'get_image_preview', 'is_active', 'is_joined', 'get_categories', 'created_at')
    list_editable = ('is_active', 'is_joined')
    search_fields = ('title', 'slug', 'description')
    list_filter = ('is_active', 'is_joined', 'categories', 'created_at')
    readonly_fields = ('slug', 'get_image_preview_large', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'slug', 'image', 'get_image_preview_large')
        }),
        ('İçerik', {
            'fields': ('description',)
        }),
        ('Sınıflandırma', {
            'fields': ('categories',)
        }),
        ('Durum', {
            'fields': ('is_active', 'is_joined')
        }),
        ('Tarih Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'
    get_image_preview.short_description = 'Görsel'
    
    def get_image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="250" height="auto" style="border-radius: 5px; max-width: 100%;" />',
                obj.image.url
            )
        return 'Görsel yüklenmemiş'
    get_image_preview_large.short_description = 'Görsel Ön İzlemesi'
    
    def get_categories(self, obj):
        categories = obj.categories.all()
        if not categories:
            return '-'
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for cat in categories:
            html += f'<li>{cat.name}</li>'
        html += '</ul>'
        return mark_safe(html)
    get_categories.short_description = 'Kategoriler'
    
    actions = ['make_active', 'make_inactive', 'mark_as_joined', 'mark_as_not_joined']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} panel aktif hale getirildi.')
    make_active.short_description = 'Seçilen panelleri aktif yap'
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} panel pasif hale getirildi.')
    make_inactive.short_description = 'Seçilen panelleri pasif yap'
    
    def mark_as_joined(self, request, queryset):
        updated = queryset.update(is_joined=True)
        self.message_user(request, f'{updated} panel katılmış olarak işaretlendi.')
    mark_as_joined.short_description = 'Seçilen panelleri katılmış olarak işaretle'
    
    def mark_as_not_joined(self, request, queryset):
        updated = queryset.update(is_joined=False)
        self.message_user(request, f'{updated} panel katılmamış olarak işaretlendi.')
    mark_as_not_joined.short_description = 'Seçilen panelleri katılmamış olarak işaretle'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni nesne
            pass
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Bildirim yönetimi"""
    list_display = ('title', 'get_type_badge', 'get_recipients', 'get_read_count', 'created_at')
    list_filter = ('type', 'created_at', 'recipient')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'get_stats')
    filter_horizontal = ('recipient', 'is_read')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Bildirim Detayları', {
            'fields': ('title', 'message', 'type', 'get_stats')
        }),
        ('Alıcılar', {
            'fields': ('recipient', 'is_read')
        }),
        ('Tarih', {
            'fields': ('created_at',)
        }),
    )
    
    def get_type_badge(self, obj):
        colors = {
            1: 'gray',      # GENERAL
            2: 'red',       # WARNING
            3: 'blue',      # INFO
        }
        color = colors.get(obj.type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    get_type_badge.short_description = 'Tür'
    
    def get_recipients(self, obj):
        recipients = obj.recipient.all()
        if not recipients:
            return '-'
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for group in recipients:
            html += f'<li>{group.name}</li>'
        html += '</ul>'
        return mark_safe(html)
    get_recipients.short_description = 'Alıcı Grupları'
    
    def get_read_count(self, obj):
        read_count = obj.is_read.count()
        total_users = sum(g.user_set.count() for g in obj.recipient.all())
        return format_html(
            '<strong>{}/{}</strong>',
            read_count,
            total_users if total_users > 0 else 0
        )
    get_read_count.short_description = 'Okundu / Toplam'
    
    def get_stats(self, obj):
        read_count = obj.is_read.count()
        total_users = sum(g.user_set.count() for g in obj.recipient.all())
        unread_count = total_users - read_count if total_users > 0 else 0
        
        html = f'''
        <div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
            <p><strong>Toplam Alıcı:</strong> {total_users}</p>
            <p style="color: green;"><strong>Okunanlar:</strong> {read_count}</p>
            <p style="color: red;"><strong>Okunmayanlar:</strong> {unread_count}</p>
        </div>
        '''
        return mark_safe(html)
    get_stats.short_description = 'İstatistikler'
    
    actions = ['mark_all_as_read']
    
    def mark_all_as_read(self, request, queryset):
        for notification in queryset:
            notification.is_read.set(
                sum((list(g.user_set.all()) for g in notification.recipient.all()), [])
            )
        self.message_user(request, 'Seçilen bildirimler okundu olarak işaretlendi.')
    mark_all_as_read.short_description = 'Seçilen bildirimleri okundu olarak işaretle'
