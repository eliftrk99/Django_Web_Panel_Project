from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from panel.models import Panel, Category, Notification, Document, Message
from django.db.models import Q, Exists, OuterRef, Sum
from django.utils.html import escape
import re
from accounting.models import Category as AccountingCategory, Account, Income, Expense, Transfer
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
import json
from datetime import date
from decimal import Decimal, InvalidOperation


def build_reporting_context(user):
    incomes = Income.objects.all()
    expenses = Expense.objects.all()

    if not (user.is_superuser or user.is_staff):
        incomes = incomes.filter(user=user)
        expenses = expenses.filter(user=user)

    income_total = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_balance = income_total - expense_total

    return {
        'income_total': income_total,
        'expense_total': expense_total,
        'net_balance': net_balance,
        'incomes': incomes.order_by('-date')[:10],
        'expenses': expenses.order_by('-date')[:10],
    }

# Helper function untuk menghitung unread notifications
def get_unread_notifications_count(user):
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient__in=user.groups.all()).exclude(is_read__in=[user]).count()

# Create your views here.
def index(request):
    visible_panels = Panel.objects.filter_for_user(request.user).filter(is_active=True) if request.user.is_authenticated else Panel.objects.none()

    context = {
        "panels": visible_panels,
        "categories": Category.objects.all(),
        "unread_notifications_count": get_unread_notifications_count(request.user),
        "recent_documents": Document.objects.filter_for_user(request.user).order_by('-created_at')[:3] if request.user.is_authenticated else [],
        "recent_messages": Message.objects.inbox_for_user(request.user).order_by('-created_at')[:3] if request.user.is_authenticated else [],
    }

    # Admin yetkisi olan kullanıcılar için muhasebe verilerini ekle
    if request.user.is_authenticated and request.user.is_staff:
        context.update({
            "accounting_categories": AccountingCategory.objects.all(),
            "accounts": Account.objects.filter(is_active=True),
            "recent_incomes": Income.objects.filter(user=request.user).order_by('-date')[:5],
            "recent_expenses": Expense.objects.filter(user=request.user).order_by('-date')[:5],
            "recent_transfers": Transfer.objects.filter(user=request.user).order_by('-date')[:5],
            "total_balance": sum(account.balance for account in Account.objects.filter(is_active=True)),
            "today": date.today()
        })

    return render(request, "panel/index.html", context)

def panels(request):
    context = {
        "panels": Panel.objects.filter_for_user(request.user).filter(is_active=True),
        "categories": Category.objects.all(),
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/panels.html", context)

def my_panels(request):
    if not request.user.is_authenticated:
        return redirect("home")
    context = {
        "panels": Panel.objects.filter_for_user(request.user).filter(is_joined=True),
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/my_panels.html", context)

def panel_details(request, slug):

    panel = Panel.objects.get(slug=slug)
    is_joined = panel.members.filter(pk=request.user.pk).exists() if request.user.is_authenticated else False

    return render(request, "panel/panel_details.html", {
        "panel": panel,
        "is_joined": is_joined,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    })


# Muhasebe işlemleri - sadece admin kullanıcıları için
@user_passes_test(lambda u: u.is_staff)
@require_POST
def add_income(request):
    """Gelir ekleme işlemi"""
    try:
        data = json.loads(request.body)

        # Veri tiplerini dönüştür
        try:
            amount = Decimal(str(data['amount']))
            category_id = int(data['category'])
            account_id = int(data['account'])
            transaction_date = date.fromisoformat(data['date'])
        except (ValueError, InvalidOperation, KeyError) as e:
            return JsonResponse({'success': False, 'message': f'Geçersiz veri formatı: {str(e)}'})

        # Kategori ve hesap kontrolü
        try:
            category = AccountingCategory.objects.get(id=category_id, type='income')
            account = Account.objects.get(id=account_id, is_active=True)
        except AccountingCategory.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Geçersiz gelir kategorisi'})
        except Account.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya aktif olmayan hesap'})

        income = Income.objects.create(
            user=request.user,
            category=category,
            account=account,
            amount=amount,
            source=data.get('source', ''),
            description=data['description'],
            date=transaction_date
        )
        return JsonResponse({
            'success': True,
            'message': 'Gelir başarıyla eklendi',
            'income': {
                'id': income.id,
                'category': income.category.name,
                'amount': str(income.amount),
                'description': income.description,
                'date': income.date.strftime('%d.%m.%Y')
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz JSON verisi'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Beklenmeyen hata: {str(e)}'})


@user_passes_test(lambda u: u.is_staff)
@require_POST
def add_expense(request):
    """Gider ekleme işlemi"""
    try:
        data = json.loads(request.body)

        # Veri tiplerini dönüştür
        try:
            amount = Decimal(str(data['amount']))
            category_id = int(data['category'])
            account_id = int(data['account'])
            transaction_date = date.fromisoformat(data['date'])
        except (ValueError, InvalidOperation, KeyError) as e:
            return JsonResponse({'success': False, 'message': f'Geçersiz veri formatı: {str(e)}'})

        # Kategori ve hesap kontrolü
        try:
            category = AccountingCategory.objects.get(id=category_id, type='expense')
            account = Account.objects.get(id=account_id, is_active=True)
        except AccountingCategory.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Geçersiz gider kategorisi'})
        except Account.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya aktif olmayan hesap'})

        expense = Expense.objects.create(
            user=request.user,
            category=category,
            account=account,
            amount=amount,
            recipient=data.get('recipient', ''),
            description=data['description'],
            date=transaction_date
        )
        return JsonResponse({
            'success': True,
            'message': 'Gider başarıyla eklendi',
            'expense': {
                'id': expense.id,
                'category': expense.category.name,
                'amount': str(expense.amount),
                'description': expense.description,
                'date': expense.date.strftime('%d.%m.%Y')
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz JSON verisi'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Beklenmeyen hata: {str(e)}'})


@user_passes_test(lambda u: u.is_staff)
@require_POST
def add_transfer(request):
    """Transfer işlemi"""
    try:
        data = json.loads(request.body)

        # Veri tiplerini dönüştür
        try:
            amount = Decimal(str(data['amount']))
            from_account_id = int(data['from_account'])
            to_account_id = int(data['to_account'])
            transaction_date = date.fromisoformat(data['date'])
        except (ValueError, InvalidOperation, KeyError) as e:
            return JsonResponse({'success': False, 'message': f'Geçersiz veri formatı: {str(e)}'})

        # Aynı hesaba transfer kontrolü
        if from_account_id == to_account_id:
            return JsonResponse({'success': False, 'message': 'Gönderen ve alan hesap aynı olamaz'})

        # Hesap kontrolü
        try:
            from_account = Account.objects.get(id=from_account_id, is_active=True)
            to_account = Account.objects.get(id=to_account_id, is_active=True)
        except Account.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Geçersiz veya aktif olmayan hesap'})

        # Yetersiz bakiye kontrolü
        if from_account.balance < amount:
            return JsonResponse({'success': False, 'message': f'Yetersiz bakiye. Mevcut bakiye: {from_account.balance} {from_account.currency}'})

        transfer = Transfer.objects.create(
            user=request.user,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            description=data['description'],
            date=transaction_date
        )
        return JsonResponse({
            'success': True,
            'message': 'Transfer başarıyla gerçekleştirildi',
            'transfer': {
                'id': transfer.id,
                'from_account': transfer.from_account.name,
                'to_account': transfer.to_account.name,
                'amount': str(transfer.amount),
                'description': transfer.description,
                'date': transfer.date.strftime('%d.%m.%Y')
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz JSON verisi'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Beklenmeyen hata: {str(e)}'})

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
    django_messages.success(request, 'Panel üyeliğiniz oluşturuldu.')
    return redirect("panel_details", slug=slug)

def leave_panel(request, slug):
    if not request.user.is_authenticated:
        return redirect("home")
    panel = Panel.objects.get(slug=slug)
    panel.members.remove(request.user)
    django_messages.info(request, 'Panel üyeliğiniz kaldırıldı.')
    return redirect("panel_details", slug=slug)

def search_panels(request):
    query = request.GET.get("q")
    context = {
        "panels": Panel.objects.filter_for_user(request.user).filter(is_active=True, title__icontains=query),
        "categories": Category.objects.all(),
        "search_query": query,
        "unread_notifications_count": get_unread_notifications_count(request.user)
    }
    return render(request, "panel/panels.html", context)

def about(request):
    context = {"unread_notifications_count": get_unread_notifications_count(request.user)}
    return render(request, "panel/about.html", context)


def documents(request):
    if not request.user.is_authenticated:
        return redirect("home")

    documents = Document.objects.filter_for_user(request.user)
    context = {
        'documents': documents,
        'unread_notifications_count': get_unread_notifications_count(request.user),
    }
    return render(request, 'panel/documents.html', context)


def messages(request):
    if not request.user.is_authenticated:
        return redirect("home")

    sent = Message.objects.outbox_for_user(request.user)
    inbox = Message.objects.inbox_for_user(request.user)
    context = {
        'sent_messages': sent,
        'inbox_messages': inbox,
        'unread_notifications_count': get_unread_notifications_count(request.user),
    }
    return render(request, 'panel/messages.html', context)


def send_message(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        recipient = User.objects.filter(username=request.POST.get('recipient')).first()
        if not recipient:
            django_messages.error(request, 'Alıcı bulunamadı.')
            return redirect('messages')

        Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=request.POST.get('subject', 'Yeni mesaj'),
            body=request.POST.get('body', ''),
        )
        django_messages.success(request, 'Mesaj gönderildi.')
        return redirect('messages')

    return redirect('messages')


def reports(request):
    if not request.user.is_authenticated:
        return redirect('login')

    context = build_reporting_context(request.user)
    context['unread_notifications_count'] = get_unread_notifications_count(request.user)
    return render(request, 'panel/reports.html', context)


def contact(request):
    if request.method == 'POST':
        django_messages.success(request, 'Mesajınız başarıyla iletildi.')
        return redirect('contact')

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