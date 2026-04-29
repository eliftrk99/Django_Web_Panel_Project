# SMS Modülü

Bu Django uygulaması, farklı SMS servis sağlayıcılarını destekleyen esnek bir SMS gönderme modülüdür.

## Özellikler

- **Çoklu Servis Desteği**: Twilio, Mock (test), Disabled (devre dışı) servisleri
- **Kolay Servis Değiştirme**: Settings ile tek satırda servis değiştirme
- **SMS Loglama**: Tüm gönderilen SMS'lerin veritabanında loglanması
- **Admin Panel Entegrasyonu**: SMS loglarının admin panelinden görüntülenmesi
- **Güvenlik**: Kullanıcı bazlı yetkilendirme

## Kurulum

### 1. Gereksinimler

```bash
pip install twilio  # Sadece Twilio kullanacaksanız
```

### 2. Settings Yapılandırması

`settings.py` dosyasına aşağıdaki ayarları ekleyin:

```python
# SMS Settings
SMS_SERVICE_TYPE = 'disabled'  # 'twilio', 'mock', 'disabled'

# Twilio ayarları (sadece Twilio kullanacaksanız)
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_number'
```

### 3. Servis Tipleri

#### Disabled (Devre Dışı)
```python
SMS_SERVICE_TYPE = 'disabled'
```
- SMS gönderimi tamamen devre dışı
- Test amaçlı kullanılabilir
- Gerçek SMS gönderilmez

#### Mock (Test Modu)
```python
SMS_SERVICE_TYPE = 'mock'
```
- SMS gönderimi simüle edilir
- Log dosyasına bilgi yazılır
- Gerçek SMS gönderilmez
- Test ve geliştirme için ideal

#### Twilio (Gerçek SMS)
```python
SMS_SERVICE_TYPE = 'twilio'
```
- Gerçek SMS gönderimi
- Twilio hesabınız olması gerekir
- Ücretli servis

### 4. Yeni Servis Sağlayıcı Ekleme

`sms/services.py` dosyasında yeni bir servis sınıfı oluşturun:

```python
class YourSMSService(SMSService):
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        # SMS gönderme mantığı
        pass

    def get_balance(self) -> Optional[float]:
        # Bakiye sorgulama (opsiyonel)
        pass
```

Sonra `get_sms_service()` fonksiyonunu güncelleyin.

## Kullanım

### Web Arayüzü

1. `/sms/send/` - SMS gönderme sayfası
2. `/sms/history/` - SMS geçmişi görüntüleme

### Programatik Kullanım

```python
from sms.services import get_sms_service

sms_service = get_sms_service()
result = sms_service.send_sms('+905xxxxxxxxx', 'Merhaba Dünya!')

if result['success']:
    print(f"SMS gönderildi. ID: {result['message_id']}")
else:
    print(f"Hata: {result['error']}")
```

## Güvenlik Notları

- Production ortamında Twilio credentials'larını environment variables olarak saklayın
- Telefon numarası validasyonu yapın
- Rate limiting uygulayın
- SMS maliyetlerini takip edin

## API Referansı

### SMSService Abstract Class

```python
class SMSService(ABC):
    @abstractmethod
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """SMS gönder"""
        pass

    @abstractmethod
    def get_balance(self) -> Optional[float]:
        """Bakiye sorgula"""
        pass
```

### Dönüş Formatı

`send_sms()` metodu şu formatta dict döner:

```python
{
    'success': bool,        # Başarılı mı?
    'message_id': str,      # Mesaj ID (opsiyonel)
    'error': str           # Hata mesajı (opsiyonel)
}
```

## Sorun Giderme

### SMS Gönderilmiyor

1. `SMS_SERVICE_TYPE` ayarını kontrol edin
2. Twilio kullanıyorsanız credentials'ları kontrol edin
3. Log dosyalarını kontrol edin
4. Twilio dashboard'dan hesap durumunu kontrol edin

### Import Hatası

Twilio paketinin yüklü olduğundan emin olun:

```bash
pip install twilio
```

### Settings Hatası

`SMS_SERVICE_TYPE` değerinin geçerli olduğundan emin olun: 'twilio', 'mock', 'disabled'