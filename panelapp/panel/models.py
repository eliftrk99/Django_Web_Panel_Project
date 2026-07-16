from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(null=False, blank=True, unique=True, db_index=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Panel(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="panels")
    is_active = models.BooleanField(default=True)
    is_joined = models.BooleanField(default=False)
    description = RichTextField()
    slug = models.SlugField(null=False, blank=True, unique=True, db_index=True, editable=False)
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Panel'
        verbose_name_plural = 'Paneller'

    def __str__(self):
        return f"{self.title}"
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


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