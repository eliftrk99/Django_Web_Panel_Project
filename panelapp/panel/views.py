from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from panel.models import Panel, Category, Notification
from django.db.models import Q, Exists, OuterRef
from django.utils.html import escape
import re

# Helper function untuk menghitung unread notifications
def get_unread_notifications_count(user):
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient__in=user.groups.all()).exclude(is_read__in=[user]).count()

# Create your views here.
def index(request):
    context = {
        "panels": Panel.objects.filter(is_active=True),
        "categories": Category.objects.all(),
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/index.html", context)

def panels(request):
    context = {
        "panels": Panel.objects.all(),
        "categories": Category.objects.all(),
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/panels.html", context)

def my_panels(request):
    if not request.user.is_authenticated:
        return redirect("home")
    context = {
        "panels": Panel.objects.filter(is_joined=True),
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/my_panels.html", context)

def panel_details(request, slug):

    panel = Panel.objects.get(slug=slug)

    return render(request, "panel/panel_details.html", {
        "panel": panel,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    })

def panels_by_category(request, slug):
    context = {
        #2.seçenek: "panels": Category.objects.get(slug=slug).panel_set.all(),
        "panels": Category.objects.get(slug=slug).panel_set.filter(is_active=True),
        #"panels": Panel.objects.filter(is_active=True, category__slug=slug),
        "categories": Category.objects.all(),
        "selected_category": slug,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/panels.html", context)

def join_panel(request, slug):
    if not request.user.is_authenticated:
        return redirect("home")
    panel = Panel.objects.get(slug=slug)
    panel.members.add(request.user)
    return redirect("panel_details", slug=slug)

def leave_panel(request, slug):
    if not request.user.is_authenticated:
        return redirect("home")
    panel = Panel.objects.get(slug=slug)
    panel.members.remove(request.user)
    return redirect("panel_details", slug=slug)

def search_panels(request):
    query = request.GET.get("q")
    context = {
        "panels": Panel.objects.filter(is_active=True, title__icontains=query),
        "categories": Category.objects.all(),
        "search_query": query,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/panels.html", context)

def about(request):
    context = {"unread_notifications_count": get_unread_notifications_count(request.user)}
    return render(request, "panel/about.html", context)

def contact(request):
    context = {"unread_notifications_count": get_unread_notifications_count(request.user)}
    return render(request, "panel/contact.html", context)

def notifications(request):
    if not request.user.is_authenticated:
        return redirect("home")
    
    notifications = Notification.objects.filter(
        recipient__in=request.user.groups.all()
    ).annotate(
        is_read_by_user=Exists(
            Notification.is_read.through.objects.filter(
                notification=OuterRef('pk'),
                user=request.user
            )
        )
    )
    
    ctx = {
        "notifications": notifications,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/notifications.html", ctx)

def mark_notification_as_read(request, notification_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
    
    try:
        notification = Notification.objects.filter(recipient__in=request.user.groups.all()).get(id=notification_id)
        notification.is_read.add(request.user)
        unread_count = get_unread_notifications_count(request.user)
        
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Bildirim okundu olarak işaretlendi.',
                'unread_count': unread_count
            })
        else:
            messages.success(request, "Bildirim okundu olarak işaretlendi.")
            return redirect("notifications")
    except Notification.DoesNotExist:
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({'success': False, 'message': 'Bildirim bulunamadı.'}, status=404)
        else:
            messages.error(request, "Bildirim bulunamadı.")
            return redirect("notifications")

def mark_notification_as_unread(request, notification_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
    
    try:
        user = request.user
        notification = Notification.objects.filter(recipient__in=user.groups.all()).get(id=notification_id)
        notification.is_read.remove(request.user)
        unread_count = get_unread_notifications_count(request.user)
        
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Bildirim okunmamış olarak işaretlendi.',
                'unread_count': unread_count
            })
        else:
            messages.success(request, "Bildirim okunmamış olarak işaretlendi.")
            return redirect("notifications")
    except Notification.DoesNotExist:
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({'success': False, 'message': 'Bildirim bulunamadı.'}, status=404)
        else:
            messages.error(request, "Bildirim bulunamadı.")
            return redirect("notifications")

def mark_all_notifications_as_read(request):
    if not request.user.is_authenticated:
        return redirect("home")
    notifications = Notification.objects.filter(recipient__in=request.user.groups.all()).exclude(is_read__in=[request.user])
    count = 0
    for notification in notifications:
        notification.is_read.add(request.user)
        count += 1
    if count > 0:
        messages.success(request, f"{count} bildirim okundu olarak işaretlendi.")
    else:
        messages.info(request, "Okunmamış bildirim bulunmamaktadır.")
    return redirect("notifications")

def clear_notifications(request, notification_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
    
    try:
        user = request.user
        notification = Notification.objects.filter(recipient__in=user.groups.all()).get(id=notification_id)
        notification.delete()
        unread_count = get_unread_notifications_count(request.user)
        
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Bildirim silindi.',
                'unread_count': unread_count
            })
        else:
            messages.success(request, "Bildirim silindi.")
            return redirect("notifications")
    except Notification.DoesNotExist:
        if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
            return JsonResponse({'success': False, 'message': 'Bildirim bulunamadı.'}, status=404)
        else:
            messages.error(request, "Bildirim bulunamadı.")
            return redirect("notifications")

def clear_all_notifications(request):
    if not request.user.is_authenticated:
        return redirect("home")
    notifications = Notification.objects.filter(recipient__in=request.user.groups.all())
    count = notifications.count()
    notifications.delete()
    if count > 0:
        messages.success(request, f"{count} bildirim silindi.")
    else:
        messages.info(request, "Silinecek bildirim bulunmamaktadır.")
    return redirect("notifications")

def unread_notifications_count(request):
    if not request.user.is_authenticated:
        return HttpResponse("0")
    count = Notification.objects.filter(recipient__in=request.user.groups.all()).exclude(is_read__in=[request.user]).count()
    return HttpResponse(str(count))

def search_request(request):
    q = request.GET.get('q')
    
    panels = Panel.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))
    categories = Category.objects.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    users = User.objects.filter(Q(username__icontains=q) | Q(email__icontains=q))

    # Highlight fonksiyonu
    def highlight_text(text, query):
        if not text or not query:
            return text
        # Case-insensitive olarak arama terimini <mark> ile sar
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<mark>{query}</mark>', escape(str(text)))
    
    # Panellere highlight ekle
    for panel in panels:
        panel.title_highlighted = highlight_text(panel.title, q)
        panel.description_highlighted = highlight_text(panel.description, q) if panel.description else ""
    
    # Kategorilere highlight ekle
    for cat in categories:
        cat.name_highlighted = highlight_text(cat.name, q)

    context = {
        'q': q,
        'panels': panels,
        'categories': categories,
        'users': users,
        'unread_notifications_count': get_unread_notifications_count(request.user)
    }
    return render(request, 'search/search_results.html', context)