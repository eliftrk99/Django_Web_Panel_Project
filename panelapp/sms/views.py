from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import SMSLog
from .services import get_sms_service
import logging

logger = logging.getLogger(__name__)

@login_required
def send_sms(request):
    if request.method == 'POST':
        recipient = request.POST.get('recipient')
        message = request.POST.get('message')

        # Get SMS service
        sms_service = get_sms_service()

        try:
            # Send SMS using the service
            result = sms_service.send_sms(recipient, message)

            if result['success']:
                # Log kaydı oluştur
                SMSLog.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    message=message,
                    status='sent',
                    twilio_sid=result.get('message_id', '')
                )

                messages.success(request, 'SMS başarıyla gönderildi!')
                return redirect('sms:sms_history')
            else:
                # SMS sending failed
                error_msg = result.get('error', 'Bilinmeyen hata')
                logger.error(f"SMS sending failed: {error_msg}")

                SMSLog.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    message=message,
                    status='failed'
                )

                messages.error(request, f'SMS gönderilemedi: {error_msg}')

        except Exception as e:
            logger.error(f"Unexpected error in SMS sending: {str(e)}")
            SMSLog.objects.create(
                sender=request.user,
                recipient=recipient,
                message=message,
                status='failed'
            )
            messages.error(request, f'Beklenmeyen hata: {str(e)}')

    return render(request, 'sms/send_sms.html', {
        'sms_service_status': getattr(settings, 'SMS_SERVICE_TYPE', 'disabled')
    })

@login_required
def sms_history(request):
    sms_logs = SMSLog.objects.filter(sender=request.user).order_by('-created_at')

    # Calculate statistics
    sent_count = sms_logs.filter(status='sent').count()
    failed_count = sms_logs.filter(status='failed').count()
    pending_count = sms_logs.filter(status='pending').count()
    total_count = sms_logs.count()

    return render(request, 'sms/sms_history.html', {
        'sms_logs': sms_logs,
        'sms_service_status': getattr(settings, 'SMS_SERVICE_TYPE', 'disabled'),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'total_count': total_count,
    })
