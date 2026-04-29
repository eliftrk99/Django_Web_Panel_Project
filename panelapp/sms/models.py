from django.db import models
from django.contrib.auth.models import User

class SMSLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Gönderildi'),
        ('failed', 'Başarısız'),
        ('pending', 'Bekliyor'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Gönderen')
    recipient = models.CharField(max_length=15, verbose_name='Alıcı Numarası')
    message = models.TextField(verbose_name='Mesaj')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Durum')
    twilio_sid = models.CharField(max_length=100, blank=True, null=True, verbose_name='Twilio SID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='Gönderilme Tarihi')
    
    class Meta:
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.recipient} - {self.status}"
