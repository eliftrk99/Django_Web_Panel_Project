from django.urls import path
from . import views

# http://127.0.0.1:8000/              => homepage
# http://127.0.0.1:8000/index         => homepage
# http://127.0.0.1:8000/panels        => panels
# http://127.0.0.1:8000/panels/3      => panels-details
# http://127.0.0.1:8000/my_panels     => my_panels

urlpatterns = [
    path("", views.index, name="home"),
    path("index", views.index),
    path("panels", views.panels, name="panels"),
    path("category/<slug:slug>", views.panels_by_category, name="panels_by_category"),
    path("panels/<slug:slug>", views.panel_details, name="panel_details"),
    path("my_panels", views.my_panels, name="my_panels"),
    path("panels/<slug:slug>/join", views.join_panel, name="join_panel"),
    path("panels/<slug:slug>/leave", views.leave_panel, name="leave_panel"),
    path("search_panels", views.search_panels, name="search_panels"),
    path("about", views.about, name="about"),
    path("contact", views.contact, name="contact"),
    path("notifications", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/mark_as_read", views.mark_notification_as_read, name="mark_notification_as_read"),
    path("notifications/<int:notification_id>/mark_as_unread", views.mark_notification_as_unread, name="mark_notification_as_unread"),
    path("notifications/mark_all_as_read", views.mark_all_notifications_as_read, name="mark_all_as_read"),
    path("notifications/clear", views.clear_notifications, name="clear_notifications"),
    path("notifications/clear_all", views.clear_all_notifications, name="clear_all_notifications"),
    path("notifications/unread_notifications_count", views.unread_notifications_count, name="unread_notifications_count"),
    path("search/", views.search_request, name="search"),
]