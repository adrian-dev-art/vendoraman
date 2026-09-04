import datetime
from django.test import TestCase, Client
from django.urls import reverse
from core.models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder, EscrowMilestone, DisputeTicket
)


class VendoramaCoreTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin_test', email='admin@test.com', password='password123', role='ADMIN'
        )

        # Category
        self.category = EventCategory.objects.create(
            name='Pernikahan', slug='wedding', icon_name='heart'
        )

        # Customer
        self.customer = CustomUser.objects.create_user(
            username='andi_test', email='andi@test.com', password='password123', role='CUSTOMER'
        )

        # Vendor
        self.vendor_user = CustomUser.objects.create_user(
            username='vendor_test', email='vendor@test.com', password='password123', role='VENDOR'
        )
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Royal Nusantara Catering',
            category=self.category,
            city='Jakarta Selatan',
            pic_name='Chef Hartono',
            contact_phone='081234567890',
            contact_email='royal@test.com',
            is_vetted=True,
            verification_status='APPROVED',
            description='Spesialis catering pernikahan.'
        )
        self.package = VendorPackage.objects.create(
            vendor=self.vendor_profile,
            name='Paket Silver 500 Pax',
            price=50000000,
            pax_capacity=500,
            specifications='Menu utama 6 macam\n3 stall gubukan'
        )

        # Event Plan for customer
        self.plan = EventPlan.objects.create(
            customer=self.customer,
            title='Pernikahan Andi & Laras',
            event_category=self.category,
            event_date=datetime.date(2026, 12, 20),
            city='Jakarta Selatan',
            estimated_pax=500,
            budget_min=30000000,
            budget_max=80000000,
            selected_services=['catering']
        )

    def test_user_roles(self):
        self.assertTrue(self.customer.is_customer())
        self.assertFalse(self.customer.is_vendor_user())
        self.assertTrue(self.vendor_user.is_vendor_user())
        self.assertTrue(self.admin_user.is_platform_admin())

    def test_free_planner_anonymization(self):
        # Customer has not paid for planner unlock
        self.client.login(username='andi_test', password='password123')
        response = self.client.get(reverse('planner_results', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_unlocked'])
        # Anonymized code should be in the context
        self.assertContains(response, self.vendor_profile.anonymized_code)
        self.assertContains(response, 'Beli Planner (Rp 150.000)')

    def test_paid_planner_unlock(self):
        self.client.login(username='andi_test', password='password123')
        # Unlock planner
        post_resp = self.client.post(reverse('unlock_planner', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(post_resp.status_code, 302)
        self.assertTrue(self.plan.is_unlocked_for(self.customer))

        # View results with unlocked access
        get_resp = self.client.get(reverse('planner_results', kwargs={'plan_id': self.plan.id}))
        self.assertTrue(get_resp.context['is_unlocked'])
        self.assertContains(get_resp, self.vendor_profile.business_name)
        self.assertContains(get_resp, self.vendor_profile.contact_phone)

    def test_event_savings_vault_progress(self):
        vault = EventSavingsVault.objects.create(
            customer=self.customer,
            title='Tabungan Pernikahan',
            target_amount=100000000,
            current_amount=0,
            target_date=datetime.date(2026, 12, 1)
        )
        self.assertEqual(vault.progress_percentage, 0.0)

        # Deposit Rp 25.000.000 (25%)
        SavingsDeposit.objects.create(vault=vault, amount=25000000)
        vault.current_amount += 25000000
        vault.save()

        self.assertEqual(vault.progress_percentage, 25.0)
        self.assertEqual(vault.remaining_amount, 75000000)

    def test_escrow_milestones_and_release(self):
        order = BookingOrder.objects.create(
            customer=self.customer,
            vendor=self.vendor_profile,
            package=self.package,
            event_date=datetime.date(2026, 12, 20),
            total_price=self.package.price,
            escrow_status='HELD'
        )
        order.create_default_milestones()

        milestones = order.milestones.all().order_by('milestone_index')
        self.assertEqual(milestones.count(), 3)
        self.assertEqual(milestones[0].percentage, 30)
        self.assertEqual(milestones[1].percentage, 40)
        self.assertEqual(milestones[2].percentage, 30)

        # Total amount must match order price exactly
        total_milestones = sum(m.amount for m in milestones)
        self.assertEqual(total_milestones, self.package.price)

        # Release Milestone 1 (DP)
        self.client.login(username='andi_test', password='password123')
        release_resp = self.client.post(reverse('approve_milestone_payout', kwargs={
            'order_id': order.id,
            'milestone_id': milestones[0].id
        }))
        self.assertEqual(release_resp.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.escrow_status, 'MILESTONE_1_PAID')
        m1 = order.milestones.get(milestone_index=1)
        self.assertEqual(m1.status, 'RELEASED')

    def test_dispute_filing_freezes_escrow_and_admin_refund(self):
        order = BookingOrder.objects.create(
            customer=self.customer,
            vendor=self.vendor_profile,
            package=self.package,
            event_date=datetime.date(2026, 12, 20),
            total_price=self.package.price,
            escrow_status='HELD'
        )
        order.create_default_milestones()

        # Customer files dispute
        self.client.login(username='andi_test', password='password123')
        dispute_resp = self.client.post(reverse('file_dispute', kwargs={'order_id': order.id}), {
            'reason': 'Vendor tidak bisa dihubungi pada H-7 dan belum ada persiapan dekorasi.',
            'evidence_text': 'Screenshot chat WhatsApp centang 1.'
        })
        self.assertEqual(dispute_resp.status_code, 302)

        order.refresh_from_db()
        # Escrow must be frozen automatically!
        self.assertEqual(order.escrow_status, 'FROZEN')
        self.assertTrue(hasattr(order, 'dispute'))
        dispute = order.dispute
        self.assertEqual(dispute.status, 'OPEN')

        # Admin arbitrates and executes 100% financial refund
        self.client.login(username='admin_test', password='password123')
        arbitrate_resp = self.client.post(reverse('admin_dispute_detail', kwargs={'dispute_id': dispute.id}), {
            'action': 'REFUND',
            'admin_notes': 'Vendor terbukti lalai fatal. Dana di-refund 100% ke customer.'
        })
        self.assertEqual(arbitrate_resp.status_code, 302)

        order.refresh_from_db()
        dispute.refresh_from_db()
        self.vendor_profile.refresh_from_db()

        self.assertEqual(order.escrow_status, 'REFUNDED')
        self.assertEqual(dispute.status, 'REFUNDED_TO_CUSTOMER')
        self.assertTrue(dispute.penalty_applied)
        # Vendor must be suspended/penalized!
        self.assertEqual(self.vendor_profile.verification_status, 'SUSPENDED')
        self.assertFalse(self.vendor_profile.is_vetted)
