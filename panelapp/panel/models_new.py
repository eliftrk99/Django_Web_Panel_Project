from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(null=False, blank=True, unique=True, db_index=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PanelQuerySet(models.QuerySet):
    def filter_for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_superuser or user.is_staff:
            return self.all()

        profile = getattr(user, 'profile', None)
        if not profile:
            return self.none()

        region = (profile.scope_region or '').strip()
        district = (profile.scope_district or '').strip()

        filters = Q(scope_region__in=['', region]) | Q(scope_region__isnull=True)
        if district:
            filters &= Q(scope_district__in=['', district]) | Q(scope_district__isnull=True)

        return self.filter(filters)


class PanelManager(models.Manager.from_queryset(PanelQuerySet)):
    pass


class Panel(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="panels")
    is_active = models.BooleanField(default=True)
    is_joined = models.BooleanField(default=False)
    description = RichTextField()
    slug = models.SlugField(null=False, blank=True, unique=True, db_index=True, editable=False)
    categories = models.ManyToManyField(Category, blank=True)
    scope_region = models.CharField(max_length=100, blank=True, default='')
    scope_district = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')

    objects = PanelManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Panel'
        verbose_name_plural = 'Paneller'

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class DocumentQuerySet(models.QuerySet):
    def filter_for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_superuser or user.is_staff:
            return self.all()

        profile = getattr(user, 'profile', None)
        if not profile:
            return self.none()

        region = (profile.scope_region or '').strip()
        district = (profile.scope_district or '').strip()

        filters = Q(scope_region__in=['', region]) | Q(scope_region__isnull=True)
        if district:
            filters &= Q(scope_district__in=['', district]) | Q(scope_district__isnull=True)

        return self.filter(filters)


class DocumentManager(models.Manager.from_queryset(DocumentQuerySet)):
    pass


class Document(models.Model):
    CATEGORY_CHOICES = (
        ('announcement', 'Duyuru'),
        ('education', 'Eğitim'),
        ('report', 'Rapor'),
        ('other', 'Diğer'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    file = models.FileField(upload_to='documents')
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='documents')
    scope_region = models.CharField(max_length=100, blank=True, default='')
    scope_district = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = DocumentManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Belge'
        verbose_name_plural = 'Belgeler'

    def __str__(self):
        return self.title


class MessageQuerySet(models.QuerySet):
    def inbox_for_user(self, user):
        return self.filter(recipient=user)

    def outbox_for_user(self, user):
        return self.filter(sender=user)


class MessageManager(models.Manager.from_queryset(MessageQuerySet)):
    pass


class Message(models.Model):
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = MessageManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mesaj'
        verbose_name_plural = 'Mesajlar'

    def __str__(self):
        return self.subject


class Notification(models.Model):
    GENERAL    = 1
    WARNING    = 2
    INFO       = 3
    TYPE_CHOICES = (
        (GENERAL, "Genel"),
        (WARNING, "Uyarı"),
        (INFO,    "Bilgi"),
    )

    recipient   = models.ManyToManyField(
                      Group,
                      related_name="notifications",
                  )
    title       = models.CharField(max_length=200)
    message     = models.TextField()
    type        = models.PositiveSmallIntegerField(
                      choices=TYPE_CHOICES,
                      default=GENERAL,
                  )
    is_read     = models.ManyToManyField(
                      get_user_model(),
                      related_name="read_notifications",
                      blank=True,
                  )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        recipients = ", ".join([g.name for g in self.recipient.all()])
        return f"{self.title} → {recipients}"
