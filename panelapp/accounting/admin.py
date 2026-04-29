from django.contrib import admin
from .models import Category, Account, Income, Expense, Transfer
from django.utils.html import format_html
from django.db.models import Sum
from django.contrib.admin.views.main import ChangeList


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'colored_type', 'description']
    list_filter = ['type']
    search_fields = ['name', 'description']
    ordering = ['type', 'name']

    def colored_type(self, obj):
        if obj.type == 'income':
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', obj.get_type_display())
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.get_type_display())
    colored_type.short_description = 'Tür'


class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'balance', 'currency', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'currency']
    search_fields = ['name', 'description']
    readonly_fields = ['balance']  # Bakiye otomatik hesaplanıyor
    ordering = ['-is_active', 'name']
    list_editable = ['is_active']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Toplam bakiye hesapla
        total_balance = qs.filter(is_active=True).aggregate(
            total=Sum('balance')
        )['total'] or 0
        self.total_balance = total_balance
        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_balance'] = getattr(self, 'total_balance', 0)
        return super().changelist_view(request, extra_context)


class IncomeAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'category', 'account', 'amount', 'currency', 'description_short']
    list_filter = ['date', 'category', 'account', 'currency', 'user']
    search_fields = ['description', 'source', 'user__username']
    date_hierarchy = 'date'
    ordering = ['-date']
    list_per_page = 25

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Açıklama'


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'category', 'account', 'amount', 'currency', 'description_short']
    list_filter = ['date', 'category', 'account', 'currency', 'user']
    search_fields = ['description', 'recipient', 'user__username']
    date_hierarchy = 'date'
    ordering = ['-date']
    list_per_page = 25

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Açıklama'


class TransferAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'from_account', 'to_account', 'amount', 'currency', 'description_short']
    list_filter = ['date', 'currency', 'from_account', 'to_account', 'user']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'
    ordering = ['-date']
    list_per_page = 25

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Açıklama'


# Modelleri admin paneline kaydet
admin.site.register(Category, CategoryAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Transfer, TransferAdmin)

# Admin panel başlığı
admin.site.site_header = "Muhasebe Yönetim Sistemi"
admin.site.site_title = "Muhasebe Admin"
admin.site.index_title = "Muhasebe Yönetimi"