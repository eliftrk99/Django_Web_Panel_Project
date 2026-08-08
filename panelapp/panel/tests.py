from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounting.models import Account, Category as AccountingCategory, Expense, Income
from account.models import UserProfile
from panel.models import Document, Message, Panel
from panel.views import build_reporting_context


class ScopeAndModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member', password='secret123')
        self.group = Group.objects.create(name='İl Başkanı')
        self.group.user_set.add(self.user)
        self.profile = UserProfile.objects.create(user=self.user, scope_region='Ankara', scope_district='Keçiören')

    def test_panels_are_filtered_by_scope_region(self):
        Panel.objects.create(title='Ankara Paneli', image='panels/ankara.jpg', description='A', scope_region='Ankara')
        Panel.objects.create(title='İstanbul Paneli', image='panels/istanbul.jpg', description='B', scope_region='İstanbul')

        visible_panels = Panel.objects.filter_for_user(self.user)

        self.assertEqual(visible_panels.count(), 1)
        self.assertEqual(visible_panels.get().title, 'Ankara Paneli')

    def test_messages_can_be_sent_and_read(self):
        recipient = User.objects.create_user(username='recipient', password='secret123')
        message = Message.objects.create(
            sender=self.user,
            recipient=recipient,
            subject='Merhaba',
            body='Talebim var.',
        )

        inbox = Message.objects.inbox_for_user(recipient)

        self.assertEqual(inbox.count(), 1)
        self.assertEqual(inbox.get().subject, message.subject)

    def test_reporting_context_contains_aggregated_totals(self):
        account = Account.objects.create(name='Nakit', type='cash', balance=Decimal('100.00'))
        income_category = AccountingCategory.objects.create(name='Aidat', type='income')
        expense_category = AccountingCategory.objects.create(name='Kira', type='expense')

        Income.objects.create(
            user=self.user,
            category=income_category,
            account=account,
            amount=Decimal('50.00'),
            description='Aidat',
            date=timezone.now().date(),
        )
        Expense.objects.create(
            user=self.user,
            category=expense_category,
            account=account,
            amount=Decimal('20.00'),
            description='Kira',
            date=timezone.now().date(),
        )

        context = build_reporting_context(self.user)

        self.assertEqual(context['income_total'], Decimal('50.00'))
        self.assertEqual(context['expense_total'], Decimal('20.00'))
        self.assertEqual(context['net_balance'], Decimal('30.00'))

    def test_documents_can_be_saved_and_listed(self):
        document = Document.objects.create(
            title='Duyuru Belgesi',
            description='Eğitim duyurusu',
            category='announcement',
            file='documents/duyuru.pdf',
            uploaded_by=self.user,
            scope_region='Ankara',
        )

        visible_documents = Document.objects.filter_for_user(self.user)

        self.assertEqual(visible_documents.count(), 1)
        self.assertEqual(visible_documents.get().title, document.title)

    def test_home_dashboard_exposes_recent_documents_and_messages(self):
        Document.objects.create(
            title='Son Belge',
            description='Önemli belge',
            category='announcement',
            file='documents/son.pdf',
            uploaded_by=self.user,
            scope_region='Ankara',
        )
        Message.objects.create(
            sender=self.user,
            recipient=self.user,
            subject='Son mesaj',
            body='İçerik',
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('recent_documents', response.context)
        self.assertIn('recent_messages', response.context)
        self.assertEqual(response.context['recent_documents'][0].title, 'Son Belge')
        self.assertEqual(response.context['recent_messages'][0].subject, 'Son mesaj')

    def test_profile_update_persists_user_details(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'firstname': 'Güncel',
            'lastname': 'Kullanıcı',
            'city': 'İstanbul',
            'province': 'Kadıköy',
            'birthDate': '1990-01-01',
            'phone': '05551234567',
            'cinsiyet': 'Erkek',
        })

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Güncel')
        self.assertEqual(self.user.last_name, 'Kullanıcı')

    def test_contact_form_redirects_after_submission(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Ali',
            'email': 'ali@example.com',
            'subject': 'Merhaba',
            'message': 'Test mesajı',
        })

        self.assertEqual(response.status_code, 302)
