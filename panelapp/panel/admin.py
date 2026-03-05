from django.contrib import admin
from .models import Panel, Category, Notification
from django.utils.safestring import mark_safe

class PanelAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'is_joined', 'slug', 'selected_categories',)
    list_editable = ('is_active', 'is_joined',)
    search_fields = ('title',)
    readonly_fields = ('slug',)
    list_filter = ('is_active', 'is_joined', 'categories',)

    def selected_categories(self, obj):
        html = "<ul>"

        for category in obj.categories.all():
            html+= "<li>" + category.name + "</li>"

        html += "</ul>"
        return mark_safe(html)
    
class NotificationAdmin(admin.ModelAdmin):
    list_display   = ("title", "selected_recipients", "type", "created_at")
    list_filter    = ("type", "created_at", "recipient")
    search_fields  = ("title", "message")
    readonly_fields = ("created_at",)
    filter_horizontal = ('recipient', 'is_read')

    def selected_recipients(self, obj):
        html = "<ul>"
        for group in obj.recipient.all():
            html += "<li>" + group.name + "</li>"
        html += "</ul>"
        return mark_safe(html)


admin.site.register(Panel, PanelAdmin)
admin.site.register(Category)
admin.site.register(Notification, NotificationAdmin)
