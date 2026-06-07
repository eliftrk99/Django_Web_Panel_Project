# Django Web Panel Projesi

Bu proje, Django tabanlı bir yönetim paneli ve kullanıcı platformu sağlayan bir web uygulamasıdır.

## Projenin Temel Görevleri

- Kullanıcı kaydı, giriş ve profil yönetimi
- Panel içeriği oluşturma, düzenleme ve görüntüleme
- Panel kategorileri ve slug yapısı yönetimi
- SMS gönderme servisleri ve bildirim sistemi
- Muhasebe/vergi işlemleri için temel modellemeler
- Dosya yükleme ve medya yönetimi
- Temel statik içerik, şablon ve frontend düzenlemeleri

## Modüller

- `account`: kullanıcı kaydı, giriş, profil ve hesap yönetimi
- `panel`: yönetim paneli içeriği, kategoriler, bildirimler ve panel detayları
- `sms`: SMS gönderme servisleri ve ilgili testler
- `accounting`: muhasebe ile ilgili model ve şablon yapısı

## Proje Yapısı

- `panelapp/`: Django proje ayarları, URL yönlendirmeleri ve ASGI/WSGI yapılandırması
- `static/`: CSS, JS ve görsel dosyaları
- `templates/`: ortak şablonlar ve kısmi bileşenler
- `uploads/`: kullanıcı yüklemeleri için dosya dizinleri

## Geliştirme Notları

- Django migrations kullanılarak model değişiklikleri sürdürülmektedir
- Projeye ek özellikler ve iyileştirmeler devam etmektedir

