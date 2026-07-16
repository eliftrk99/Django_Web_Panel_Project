from django.contrib import admin
from .models import Category, Account, Income, Expense, Transfer
from django.utils.html import format_html
from django.db.models import Sum
from django.contrib.admin.views.main import ChangeList


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Gelir/Gider kategorileri yönetimi"""
    list_display = ['name', 'type_badge', 'colored_type', 'get_transaction_count']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['type', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'type', 'color')
        }),
        ('Açıklama', {
            'fields': ('description',)
        }),
        ('Tarih Bilgileri', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def type_badge(self, obj):
        """Tür bilgisini rengli badge olarak göster"""
        if obj.type == 'income':
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">📈 {}</span>',
                obj.get_type_display()
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">📉 {}</span>',
                obj.get_type_display()
            )
    type_badge.short_description = 'Tür (Badge)'
    
    def colored_type(self, obj):
        if obj.type == 'income':
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', obj.get_type_display())
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.get_type_display())
    colored_type.short_description = 'Tür'
    
    def get_transaction_count(self, obj):
        income_count = Income.objects.filter(category=obj).count()
        expense_count = Expense.objects.filter(category=obj).count()
        
        if obj.type == 'income':
            return format_html('<strong style="color: green;">{} işlem</strong>', income_count)
        else:
            return format_html('<strong style="color: red;">{} işlem</strong>', expense_count)
    get_transaction_count.short_description = 'İşlem Sayısı'


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Cari hesaplar yönetimi"""
    list_display = ['name', 'type_badge', 'balance_formatted', 'currency', 'is_active_badge', 'created_at']
    list_filter = ['type', 'is_active', 'currency', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'balance_display']
    list_editable = ['is_active']
    ordering = ['-is_active', 'name']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'type', 'currency', 'is_active')
        }),
        ('Bakiye', {
            'fields': ('balance', 'balance_display'),
            'classes': ('wide',)
        }),
        ('Açıklama', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Tarih Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def type_badge(self, obj):
        """Hesap türünü badge olarak göster"""
        type_colors = {
            'bank': '#2196F3',
            'cash': '#4CAF50',
            'credit_card': '#FF9800',
            'other': '#9C27B0',
        }
        color = type_colors.get(obj.type, '#757575')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Hesap Türü'
    
    def balance_formatted(self, obj):
        """Bakiyeyi formatlı olarak göster"""
        if obj.balance >= 0:
            return format_html(
                '<strong style="color: green;">+ {:.2f}</strong>',
                obj.balance
            )
        else:
            return format_html(
                '<strong style="color: red;">- {:.2f}</strong>',
                abs(obj.balance)
            )
    balance_formatted.short_description = 'Bakiye'
    
    def balance_display(self, obj):
        """Bakiye bilgisini readonly alanda göster"""
        return format_html(
            '<div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px; font-size: 16px; font-weight: bold;">'
            '{:.2f} {}'
            '</div>',
            obj.balance,
            obj.currency
        )
    balance_display.short_description = 'Mevcut Bakiye'
    
    def is_active_badge(self, obj):
        """Aktif durumunu badge olarak göster"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">✓ Aktif</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">✗ Pasif</span>'
            )
    is_active_badge.short_description = 'Durum'
    
    def changelist_view(self, request, extra_context=None):
        """Toplam bakiyeyi list view'da göster"""
        extra_context = extra_context or {}
        total_balance = Account.objects.filter(is_active=True).aggregate(
            total=Sum('balance')
        )['total'] or 0
        extra_context['total_balance'] = f'{total_balance:.2f}'
        return super().changelist_view(request, extra_context)


class IncomeExpenseBaseAdmin(admin.ModelAdmin):
    """Gelir ve Gider admin'inin temel sınıfı"""
    list_filter = ['date', 'category', 'account', 'currency', 'user', 'created_at']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'amount_display']
    ordering = ['-date', '-created_at']
    
    def amount_display(self, obj):
        """Tutarı formatlı olarak göster"""
        return format_html(
            '<div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px; font-size: 16px; font-weight: bold;">'
            '{:.2f} {}'
            '</div>',
            obj.amount,
            obj.currency
        )
    amount_display.short_description = 'Tutar'


@admin.register(Income)
class IncomeAdmin(IncomeExpenseBaseAdmin):
    """Gelir işlemleri yönetimi"""
    list_display = ['date', 'user', 'category', 'account', 'amount_formatted', 'currency', 'source_display', 'created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('user', 'date', 'created_at')
        }),
        ('Kategori ve Hesap', {
            'fields': ('category', 'account', 'source')
        }),
        ('Tutar', {
            'fields': ('amount', 'currency', 'amount_display')
        }),
        ('Açıklama', {
            'fields': ('description',)
        }),
    )
    
    def amount_formatted(self, obj):
        """Tutarı yeşil olarak göster"""
        return format_html(
            '<strong style="color: green;">+ {:.2f}</strong>',
            obj.amount
        )
    amount_formatted.short_description = 'Tutar'
    
    def source_display(self, obj):
        """Kaynağı göster"""
        return obj.source or '-'
    source_display.short_description = 'Kaynak'
    
    actions = ['group_by_category', 'export_incomes']
    
    def group_by_category(self, request, queryset):
        """Kategoriye göre grup bilgileri"""
        from django.db.models import Sum
        categories = queryset.values('category__name').annotate(total=Sum('amount'))
        msg = ', '.join([f"{c['category__name']}: {c['total']}" for c in categories])
        self.message_user(request, f'Kategoriye göre toplamlar: {msg}')
    group_by_category.short_description = 'Kategoriye göre toplamları göster'
    
    def export_incomes(self, request, queryset):
        """Gelir bilgilerini CSV olarak dışa aktar"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="gelirler.csv"'
        response.write('\ufeff')  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow(['Tarih', 'Kullanıcı', 'Kategori', 'Hesap', 'Tutar', 'Para Birimi', 'Kaynak', 'Açıklama'])
        
        for income in queryset:
            writer.writerow([
                income.date,
                income.user.username,
                income.category.name,
                income.account.name,
                income.amount,
                income.currency,
                income.source,
                income.description,
            ])
        
        return response
    export_incomes.short_description = 'CSV olarak dışa aktar'


@admin.register(Expense)
class ExpenseAdmin(IncomeExpenseBaseAdmin):
    """Gider işlemleri yönetimi"""
    list_display = ['date', 'user', 'category', 'account', 'amount_formatted', 'currency', 'payment_method_display', 'created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('user', 'date', 'created_at')
        }),
        ('Kategori ve Hesap', {
            'fields': ('category', 'account', 'payment_method')
        }),
        ('Tutar', {
            'fields': ('amount', 'currency', 'amount_display')
        }),
        ('Açıklama', {
            'fields': ('description',)
        }),
    )
    
    def amount_formatted(self, obj):
        """Tutarı kırmızı olarak göster"""
        return format_html(
            '<strong style="color: red;">- {:.2f}</strong>',
            obj.amount
        )
    amount_formatted.short_description = 'Tutar'
    
    def payment_method_display(self, obj):
        """Ödeme yöntemini göster"""
        return obj.payment_method or '-'
    payment_method_display.short_description = 'Ödeme Yöntemi'
    
    actions = ['export_expenses']
    
    def export_expenses(self, request, queryset):
        """Gider bilgilerini CSV olarak dışa aktar"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="giderler.csv"'
        response.write('\ufeff')  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow(['Tarih', 'Kullanıcı', 'Kategori', 'Hesap', 'Tutar', 'Para Birimi', 'Ödeme Yöntemi', 'Açıklama'])
        
        for expense in queryset:
            writer.writerow([
                expense.date,
                expense.user.username,
                expense.category.name,
                expense.account.name,
                expense.amount,
                expense.currency,
                expense.payment_method,
                expense.description,
            ])
        
        return response
    export_expenses.short_description = 'CSV olarak dışa aktar'


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Transfer işlemleri yönetimi"""
    list_display = ['date', 'user', 'from_account', 'to_account', 'amount_formatted', 'currency', 'created_at']
    list_filter = ['date', 'from_account', 'to_account', 'currency', 'created_at']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'amount_display']
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('user', 'date', 'created_at')
        }),
        ('Transfer Bilgileri', {
            'fields': ('from_account', 'to_account', 'amount', 'currency', 'amount_display')
        }),
        ('Açıklama', {
            'fields': ('description',)
        }),
    )
    
    def amount_formatted(self, obj):
        """Tutarı mavi olarak göster"""
        return format_html(
            '<strong style="color: blue;">→ {:.2f}</strong>',
            obj.amount
        )
    amount_formatted.short_description = 'Tutar'
    
    def amount_display(self, obj):
        """Tutarı formatted olarak göster"""
        return format_html(
            '<div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px; font-size: 16px; font-weight: bold;">'
            '{:.2f} {}'
            '</div>',
            obj.amount,
            obj.currency
        )
    amount_display.short_description = 'Transfer Tutarı'


# Django Admin site özelleştirmesi
admin.site.site_header = 'Panel Yönetim Paneli'
admin.site.site_title = 'Yönetim Paneli'
admin.site.index_title = 'Hoşgeldiniz'
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