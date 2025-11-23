from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from panel.models import Panel, Category

# Create your views here.
def index(request):
    context = {
        "panels": Panel.objects.filter(is_active=True),
        "categories": Category.objects.all()
    }
    return render(request, "panel/index.html", context)

def panels(request):
    context = {
        "panels": Panel.objects.all(),
        "categories": Category.objects.all()
    }
    return render(request, "panel/panels.html", context)

def my_panels(request):
    if not request.user.is_authenticated:
        return redirect("home")
    context = {
        "panels": Panel.objects.filter(is_joined=True)
    }
    return render(request, "panel/my_panels.html", context)

def panel_details(request, slug):

    panel = Panel.objects.get(slug=slug)

    return render(request, "panel/panel_details.html", {"panel": panel})

def panels_by_category(request, slug):
    context = {
        #2.seçenek: "panels": Category.objects.get(slug=slug).panel_set.all(),
        "panels": Category.objects.get(slug=slug).panel_set.filter(is_active=True),
        #"panels": Panel.objects.filter(is_active=True, category__slug=slug),
        "categories": Category.objects.all(),
        "selected_category": slug
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
        "search_query": query
    }
    return render(request, "panel/panels.html", context)

def about(request):
    return render(request, "panel/about.html")

def contact(request):
    return render(request, "panel/contact.html")

def notifications(request):
    if not request.user.is_authenticated:
        return redirect("home")
    return render(request, "panel/notifications.html")

def mark_notification_as_read(request, notification_id):
    if not request.user.is_authenticated:
        return redirect("home")
    notification = request.user.notifications.get(id=notification_id)
    notification.mark_as_read()
    return redirect("notifications")

def mark_notification_as_unread(request, notification_id):
    if not request.user.is_authenticated:
        return redirect("login")
    user = request.user
    notification = user.notifications.get(id=notification_id)
    notification.mark_as_unread()
    return redirect("notifications")

def mark_all_notifications_as_read(request):
    if not request.user.is_authenticated:
        return redirect("home")
    request.user.notifications.mark_all_as_read()
    return redirect("notifications")

def clear_notifications(request, notification_id):
    if not request.user.is_authenticated:
        return redirect("login")
    user = request.user
    notification = user.notifications.get(id=notification_id)
    notification.delete()
    return redirect("notifications")

def clear_all_notifications(request):
    if not request.user.is_authenticated:
        return redirect("home")
    request.user.notifications.clear()
    return redirect("notifications")

def unread_notifications_count(request):
    if not request.user.is_authenticated:
        return HttpResponse("0")
    count = request.user.notifications.unread_count
    return HttpResponse(str(count))