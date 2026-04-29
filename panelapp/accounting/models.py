from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    """Gelir/Gider kategorileri"""
    CATEGORY_TYPES = [
        ('income', 'Gelir'),
        ('expense', 'Gider'),
    ]

    name = models.CharField(max_length=100, verbose_name='Kategori Adı')
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, verbose_name='Tür')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Renk')  # Hex color
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')

    class Meta:
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class Account(models.Model):
    """Cari hesaplar"""
    ACCOUNT_TYPES = [
        ('bank', 'Banka Hesabı'),
        ('cash', 'Nakit'),
        ('credit_card', 'Kredi Kartı'),
        ('other', 'Diğer'),
    ]

    name = models.CharField(max_length=100, verbose_name='Hesap Adı')
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, verbose_name='Hesap Türü')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Bakiye')
    currency = models.CharField(max_length=3, default='TRY', verbose_name='Para Birimi')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')

    class Meta:
        verbose_name = 'Cari Hesap'
        verbose_name_plural = 'Cari Hesaplar'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.balance} {self.currency})"


class Transaction(models.Model):
    """Temel işlem sınıfı"""
    TRANSACTION_TYPES = [
        ('income', 'Gelir'),
        ('expense', 'Gider'),
        ('transfer', 'Transfer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name='İşlem Türü')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Tutar')
    currency = models.CharField(max_length=3, default='TRY', verbose_name='Para Birimi')
    description = models.TextField(verbose_name='Açıklama')
    date = models.DateField(default=timezone.now, verbose_name='Tarih')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')

    class Meta:
        abstract = True
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.currency}"


class Income(Transaction):
    """Gelir işlemleri"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                limit_choices_to={'type': 'income'},
                                verbose_name='Kategori')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Hesap')
    source = models.CharField(max_length=100, blank=True, verbose_name='Kaynak')

    class Meta:
        verbose_name = 'Gelir'
        verbose_name_plural = 'Gelirler'

    def save(self, *args, **kwargs):
        # Gelir eklendiğinde hesap bakiyesini güncelle
        if self.pk is None:  # Yeni kayıt
            self.account.balance += self.amount
            self.account.save()
        else:  # Güncelleme
            old_income = Income.objects.get(pk=self.pk)
            difference = self.amount - old_income.amount
            self.account.balance += difference
            self.account.save()
        super().save(*args, **kwargs)


class Expense(Transaction):
    """Gider işlemleri"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                limit_choices_to={'type': 'expense'},
                                verbose_name='Kategori')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Hesap')
    recipient = models.CharField(max_length=100, blank=True, verbose_name='Alıcı')

    class Meta:
        verbose_name = 'Gider'
        verbose_name_plural = 'Giderler'

    def save(self, *args, **kwargs):
        # Gider eklendiğinde hesap bakiyesini güncelle
        if self.pk is None:  # Yeni kayıt
            self.account.balance -= self.amount
            self.account.save()
        else:  # Güncelleme
            old_expense = Expense.objects.get(pk=self.pk)
            difference = self.amount - old_expense.amount
            self.account.balance -= difference
            self.account.save()
        super().save(*args, **kwargs)


class Transfer(models.Model):
    """Hesaplar arası transfer"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                    related_name='transfers_from',
                                    verbose_name='Gönderen Hesap')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                  related_name='transfers_to',
                                  verbose_name='Alan Hesap')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Tutar')
    currency = models.CharField(max_length=3, default='TRY', verbose_name='Para Birimi')
    description = models.TextField(verbose_name='Açıklama')
    date = models.DateField(default=timezone.now, verbose_name='Tarih')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')

    class Meta:
        verbose_name = 'Transfer'
        verbose_name_plural = 'Transferler'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Transfer: {self.from_account.name} → {self.to_account.name} ({self.amount} {self.currency})"

    def save(self, *args, **kwargs):
        # Transfer yapıldığında hesap bakiyelerini güncelle
        if self.pk is None:  # Yeni kayıt
            self.from_account.balance -= self.amount
            self.to_account.balance += self.amount
            self.from_account.save()
            self.to_account.save()
        else:  # Güncelleme
            old_transfer = Transfer.objects.get(pk=self.pk)
            # Eski transferi geri al
            old_transfer.from_account.balance += old_transfer.amount
            old_transfer.to_account.balance -= old_transfer.amount
            # Yeni transferi uygula
            self.from_account.balance -= self.amount
            self.to_account.balance += self.amount
            self.from_account.save()
            self.to_account.save()
        super().save(*args, **kwargs)