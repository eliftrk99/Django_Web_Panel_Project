from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'province', 'scope_region', 'scope_district')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'city', 'province', 'scope_region', 'scope_district')


# User ve Group admin'i customize et
class CustomUserAdmin(BaseUserAdmin):
    """Django User modelini iyileştirilmiş admin paneli"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Kişisel Bilgiler', {'fields': ('username', 'email', 'first_name', 'last_name', 'password')}),
        ('İzinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Tarih Bilgileri', {'fields': ('date_joined', 'last_login')}),
    )


class CustomGroupAdmin(BaseGroupAdmin):
    """Group modelini iyileştirilmiş admin paneli"""
    list_display = ('name', 'get_permissions_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'İzin Sayısı'


# Varsayılan User ve Group admin'lerini değiştir
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)
