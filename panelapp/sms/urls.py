from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('send/', views.send_sms, name='send_sms'),
    path('history/', views.sms_history, name='sms_history'),
]