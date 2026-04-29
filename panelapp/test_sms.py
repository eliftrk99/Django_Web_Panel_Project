#!/usr/bin/env python
"""
SMS Modülü Test Scripti

Bu script SMS modülünün farklı servislerde nasıl çalıştığını test eder.
"""

import os
import sys
import django

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panelapp.settings')
django.setup()

from sms.services import get_sms_service, TwilioSMSService, MockSMSService, DisabledSMSService

def test_service(service_name, service):
    """Belirli bir SMS servisini test et"""
    print(f"\n=== {service_name} Servisi Testi ===")

    # Test SMS gönderimi
    test_number = "+905551234567"
    test_message = "Bu bir test SMS mesajıdır."

    print(f"Test Numarası: {test_number}")
    print(f"Test Mesajı: {test_message}")

    result = service.send_sms(test_number, test_message)
    print(f"Sonuç: {result}")

    # Bakiye kontrolü
    balance = service.get_balance()
    if balance is not None:
        print(f"Bakiye: {balance}")
    else:
        print("Bakiye bilgisi mevcut değil")

def main():
    print("SMS Modülü Test Scripti")
    print("=" * 50)

    # Mevcut ayarlı servisi test et
    print("\n1. Mevcut Ayarlı Servis Testi:")
    current_service = get_sms_service()
    service_type = type(current_service).__name__
    test_service(f"Mevcut ({service_type})", current_service)

    # Farklı servisleri test et
    print("\n2. Tüm Servislerin Testi:")

    # Mock servis
    mock_service = MockSMSService()
    test_service("Mock", mock_service)

    # Disabled servis
    disabled_service = DisabledSMSService()
    test_service("Disabled", disabled_service)

    # Twilio servis (sadece credentials varsa)
    try:
        from django.conf import settings
        if (hasattr(settings, 'TWILIO_ACCOUNT_SID') and
            hasattr(settings, 'TWILIO_AUTH_TOKEN') and
            hasattr(settings, 'TWILIO_PHONE_NUMBER') and
            settings.TWILIO_ACCOUNT_SID and
            settings.TWILIO_AUTH_TOKEN and
            settings.TWILIO_PHONE_NUMBER):
            twilio_service = TwilioSMSService(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER
            )
            test_service("Twilio", twilio_service)
        else:
            print("\nTwilio servisi test edilemedi - credentials eksik")
    except Exception as e:
        print(f"\nTwilio servisi test edilemedi: {e}")

    print("\n" + "=" * 50)
    print("Test tamamlandı!")

if __name__ == "__main__":
    main()