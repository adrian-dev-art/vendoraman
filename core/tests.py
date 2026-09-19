import datetime
from django.test import TestCase, Client
from django.urls import reverse
from core.models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder
)


class VendoramanCoreTests(TestCase):
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
        self.client.login(username='andi_test', password='password123')
        response = self.client.get(reverse('planner_results', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_unlocked'])
        self.assertContains(response, self.vendor_profile.anonymized_code)
        self.assertContains(response, 'Buka Planner (Rp 150.000)')

    def test_paid_planner_unlock(self):
        self.client.login(username='andi_test', password='password123')
        post_resp = self.client.post(reverse('unlock_planner', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(post_resp.status_code, 302)
        self.assertTrue(self.plan.is_unlocked_for(self.customer))

        get_resp = self.client.get(reverse('planner_results', kwargs={'plan_id': self.plan.id}))
        self.assertTrue(get_resp.context['is_unlocked'])
        self.assertContains(get_resp, self.vendor_profile.business_name)
        self.assertContains(get_resp, 'Hitung Katering')
        self.assertContains(get_resp, 'Daftar Barang')
        self.assertContains(get_resp, 'Jadwal & Hitung Mundur')
        self.assertContains(get_resp, 'Batas Budget Maksimal')

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

    def test_booking_order_commission_calculation(self):
        # Create a booking order
        order = BookingOrder.objects.create(
            customer=self.customer,
            vendor=self.vendor_profile,
            package=self.package,
            event_date=datetime.date(2026, 12, 20),
            total_price=self.package.price,
            status='PENDING'
        )
        # Verify 10% commission fee taken from vendor
        expected_commission = round(50000000 * 0.10)
        expected_net = 50000000 - expected_commission
        self.assertEqual(order.commission_amount, expected_commission)
        self.assertEqual(order.vendor_net_amount, expected_net)
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.commission_status, 'PENDING')

    def test_booking_checkout_view_and_order_lifecycle(self):
        self.client.login(username='andi_test', password='password123')
        # Checkout POST
        checkout_resp = self.client.post(reverse('booking_checkout'), {
            'package_id': self.package.id,
            'plan_id': self.plan.id,
            'event_date': '2026-12-20',
            'notes': 'Mohon konfirmasi kesiapan menu catering.'
        })
        self.assertEqual(checkout_resp.status_code, 302)

        order = BookingOrder.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_price, self.package.price)
        self.assertEqual(order.status, 'PENDING')

        # Vendor confirms order
        self.client.login(username='vendor_test', password='password123')
        confirm_resp = self.client.post(reverse('update_order_status', kwargs={'order_id': order.id}), {
            'action': 'confirm'
        })
        self.assertEqual(confirm_resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'CONFIRMED')

        # Event completed
        complete_resp = self.client.post(reverse('update_order_status', kwargs={'order_id': order.id}), {
            'action': 'complete'
        })
        self.assertEqual(complete_resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'COMPLETED')
        self.assertEqual(order.commission_status, 'PAID')

    def test_vendor_and_admin_dashboard_metrics(self):
        # Create confirmed order
        order = BookingOrder.objects.create(
            customer=self.customer,
            vendor=self.vendor_profile,
            package=self.package,
            event_date=datetime.date(2026, 12, 20),
            total_price=self.package.price,
            status='COMPLETED'
        )

        # Vendor Dashboard check
        self.client.login(username='vendor_test', password='password123')
        v_resp = self.client.get(reverse('vendor_dashboard'))
        self.assertEqual(v_resp.status_code, 200)
        self.assertEqual(v_resp.context['gross_revenue'], 50000000)
        self.assertEqual(v_resp.context['total_commission_paid'], 5000000)
        self.assertEqual(v_resp.context['net_earnings'], 45000000)

        # Admin Dashboard check
        self.client.login(username='admin_test', password='password123')
        a_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(a_resp.status_code, 200)
        self.assertEqual(a_resp.context['total_gmv'], 50000000)
        self.assertEqual(a_resp.context['total_commission_revenue'], 5000000)

    def test_export_access_control_unlocked_required(self):
        # Anonymous user redirected
        resp_anon = self.client.get(reverse('export_planner_excel', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp_anon.status_code, 302)

        # Logged in but Free Planner (not unlocked)
        self.client.login(username='andi_test', password='password123')
        resp_free = self.client.get(reverse('export_planner_excel', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp_free.status_code, 302)
        self.assertIn(reverse('planner_results', kwargs={'plan_id': self.plan.id}), resp_free.url)

        resp_pdf_free = self.client.get(reverse('export_planner_pdf', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp_pdf_free.status_code, 302)

        resp_deck_free = self.client.get(reverse('planner_deck', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp_deck_free.status_code, 302)

    def test_paid_planner_excel_export_content(self):
        import io
        import openpyxl

        # Unlock Paid Planner
        PlannerAccess.objects.create(
            customer=self.customer, event_plan=self.plan, is_unlocked=True
        )
        self.client.login(username='andi_test', password='password123')

        resp = self.client.get(reverse('export_planner_excel', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename=', resp['Content-Disposition'])

        # Load workbook and verify sheets
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        sheet_names = wb.sheetnames
        self.assertIn('Budget & Bayar', sheet_names)
        self.assertIn('Direktori Vendor & PIC', sheet_names)
        self.assertIn('Jadwal & Rundown', sheet_names)
        self.assertIn('Hitung Katering', sheet_names)
        self.assertIn('Daftar Barang', sheet_names)
        self.assertIn('Tabungan', sheet_names)
        self.assertIn('Dashboard', sheet_names)
        self.assertEqual(sheet_names[0], 'Dashboard')

        # Dashboard: live KPI links + 3 charts
        dash = wb['Dashboard']
        self.assertIn('DASHBOARD RINGKASAN ACARA', str(dash['A1'].value))
        self.assertEqual(dash['A6'].value, "='Jadwal & Rundown'!A5")
        self.assertEqual(dash['F6'].value, "='Budget & Bayar'!G5")
        self.assertEqual(dash['K10'].value, "=Tabungan!E4")
        self.assertEqual(len(dash._charts), 4)
        titles = [c.title.tx.rich.p[0].r[0].t for c in dash._charts]
        self.assertIn('Target vs Realisasi per Kategori', titles)
        self.assertIn('Alokasi Anggaran (%)', titles)
        self.assertIn('Status Persiapan Acara', titles)
        # Plan wedding → chart ke-4 = progress tabungan
        self.assertIn('PROGRESS TABUNGAN ACARA', titles)
        self.assertEqual(dash['Q20'].value, 'Terkumpul')
        self.assertEqual(dash['R20'].value, '=Tabungan!C4')

        # Metadata kepemilikan tercatat di properti file
        self.assertEqual(wb.properties.creator, 'Adrian Muhamad Ghofur')
        self.assertEqual(wb.properties.lastModifiedBy, 'Adrian Muhamad Ghofur')
        self.assertIn('Adrian Muhamad Ghofur', wb.properties.description)

        # Verify Tabungan sheet without vault shows guidance
        tab_sheet = wb['Tabungan']
        tab_text = " ".join([str(cell.value) for row in tab_sheet.iter_rows() for cell in row if cell.value])
        self.assertIn("Belum ada tabungan", tab_text)

        # Verify vendor directory contains unmasked vendor name and contact
        vendor_sheet = wb['Direktori Vendor & PIC']
        vendor_text = " ".join([str(cell.value) for row in vendor_sheet.iter_rows() for cell in row if cell.value])
        self.assertIn(self.vendor_profile.business_name, vendor_text)
        self.assertIn(self.vendor_profile.contact_phone, vendor_text)

        # Verify Rundown & Timeline has monthly, weekly, and daily deadline tiers
        timeline_sheet = wb['Jadwal & Rundown']
        timeline_text = " ".join([str(cell.value) for row in timeline_sheet.iter_rows() for cell in row if cell.value])
        self.assertIn("Bulan:", timeline_text)
        self.assertIn("Minggu:", timeline_text)
        self.assertIn("Hari:", timeline_text)

        # Verify Checklist Logistik sheet
        logistics_sheet = wb['Daftar Barang']
        logistics_text = " ".join([str(cell.value) for row in logistics_sheet.iter_rows() for cell in row if cell.value])
        self.assertIn("Dokumen & Finansial", logistics_text)
        self.assertIn("Busana & Rias", logistics_text)
        self.assertIn("Teknis & Multimedia", logistics_text)

    def test_tabungan_sheet_with_vault_and_deposits(self):
        import io
        import openpyxl
        from core.services_export import generate_planner_pdf_deck

        vault = EventSavingsVault.objects.create(
            customer=self.customer,
            event_plan=self.plan,
            title='Tabungan Pernikahan',
            target_amount=100000000,
            current_amount=25000000,
            target_date=datetime.date(2026, 12, 1),
        )
        SavingsDeposit.objects.create(vault=vault, amount=10000000, notes='Setoran 1')
        SavingsDeposit.objects.create(vault=vault, amount=15000000, notes='Setoran 2')

        PlannerAccess.objects.create(
            customer=self.customer, event_plan=self.plan, is_unlocked=True
        )
        self.client.login(username='andi_test', password='password123')
        resp = self.client.get(reverse('export_planner_excel', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        ws = wb['Tabungan']
        txt = " ".join([str(c.value) for row in ws.iter_rows() for c in row if c.value])
        self.assertIn('Tabungan Pernikahan', txt)
        self.assertIn('Setoran 1', txt)
        self.assertIn('Setoran 2', txt)
        self.assertIn('TOTAL OTOMATIS', txt)

        # Formulas: collected total sums entries, KPI cards follow the table
        self.assertEqual(ws['C4'].value, f"=C{ws.max_row}")
        self.assertEqual(ws['E4'].value, "=IF(A4=0,0,C4/A4)")

        # PDF deck includes savings slide and still valid PDF
        pdf = generate_planner_pdf_deck(self.plan, [self.vendor_profile], {})
        self.assertTrue(pdf.startswith(b'%PDF-'))

    def test_paid_planner_pdf_deck_export(self):
        PlannerAccess.objects.create(
            customer=self.customer, event_plan=self.plan, is_unlocked=True
        )
        self.client.login(username='andi_test', password='password123')

        resp = self.client.get(reverse('export_planner_pdf', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', resp['Content-Disposition'])
        self.assertTrue(resp.content.startswith(b'%PDF-'))

    def test_paid_planner_web_deck_view(self):
        PlannerAccess.objects.create(
            customer=self.customer, event_plan=self.plan, is_unlocked=True
        )
        self.client.login(username='andi_test', password='password123')

        resp = self.client.get(reverse('planner_deck', kwargs={'plan_id': self.plan.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'planner/deck.html')
        self.assertContains(resp, 'Pernikahan Andi')
        self.assertContains(resp, self.vendor_profile.business_name)
        self.assertContains(resp, 'Jadwal Bulanan')
        self.assertContains(resp, 'Jadwal Mingguan')
        self.assertContains(resp, 'Jadwal Harian')

    def test_home_view_landing_page_rich_content(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'home.html')

        # Check vendor count per category
        self.assertContains(resp, 'Vendor Terkurasi')
        self.assertContains(resp, 'Pernikahan')

        # Check price range
        self.assertContains(resp, 'Harga Paket')
        self.assertContains(resp, '50.000.000')

        # Check city coverage
        self.assertContains(resp, 'Jangkauan Wilayah')
        self.assertContains(resp, 'Jakarta Selatan')

        # Check template buyers social proof counter
        self.assertContains(resp, 'Pengguna Master Planner')

        # Check client reviews
        self.assertContains(resp, 'Kisah Sukses')
        self.assertContains(resp, 'Andi Pratama')
        self.assertContains(resp, 'Sarah Meliana')
        self.assertContains(resp, 'Template Excel')
        self.assertContains(resp, 'Proteksi Escrow')

        # Check FAQs
        self.assertContains(resp, 'Pertanyaan yang Sering Diajukan (FAQ)')
        self.assertContains(resp, 'Milestone Escrow')

    def test_currency_tags_dot_formatting(self):
        from core.templatetags.currency_tags import intdot, rupiah
        self.assertEqual(intdot(100000), '100.000')
        self.assertEqual(intdot(4500000), '4.500.000')
        self.assertEqual(intdot(120000000), '120.000.000')
        self.assertEqual(rupiah(100000), 'Rp 100.000')
        self.assertEqual(rupiah(4500000), 'Rp 4.500.000')
        self.assertEqual(rupiah('120000000'), 'Rp 120.000.000')
        self.assertEqual(intdot(None), '')
        self.assertEqual(intdot(''), '')


class LaunchChecklistTests(TestCase):
    """Privacy, terms, robots, sitemap, SEO tags, honeypot anti-spam."""

    def setUp(self):
        self.category = EventCategory.objects.create(
            name='Pernikahan', slug='wedding', icon_name='heart')
        self.customer = CustomUser.objects.create_user(
            username='launch_user', email='launch@test.com', password='password123', role='CUSTOMER')
        self.vendor_user = CustomUser.objects.create_user(
            username='launch_vendor', email='launch_vendor@test.com', password='password123', role='VENDOR')
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Launch Catering',
            category=self.category,
            city='Jakarta',
            pic_name='PIC',
            contact_phone='081234567890',
            contact_email='launch@test.com',
            is_vetted=True,
            verification_status='APPROVED',
            description='Vendor contoh.')
        self.package = VendorPackage.objects.create(
            vendor=self.vendor_profile,
            name='Paket Contoh',
            price=10000000,
            pax_capacity=100,
            specifications='Menu utama')

    def test_legal_pages_render(self):
        for name, marker in (('privacy', 'Kebijakan Privasi'), ('terms', 'Syarat &amp; Ketentuan')):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, marker)
            # Linked from site footer
            home = self.client.get(reverse('home'))
            self.assertContains(home, reverse(name))

    def test_robots_and_sitemap(self):
        robots = self.client.get(reverse('robots'))
        self.assertEqual(robots.status_code, 200)
        self.assertEqual(robots['Content-Type'], 'text/plain')
        self.assertIn('Sitemap:', robots.content.decode())
        sm = self.client.get(reverse('sitemap'))
        self.assertEqual(sm.status_code, 200)
        content = sm.content.decode()
        for name in ('privacy', 'terms', reverse('home')):
            url = name if name.startswith('/') else reverse(name)
            self.assertIn(url, content)

    def test_seo_head_tags(self):
        resp = self.client.get(reverse('home'))
        html = resp.content.decode()
        self.assertIn('name="description"', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:image"', html)
        self.assertIn('og-cover.png', html)
        self.assertIn('favicon.svg', html)
        self.assertIn('rel="canonical"', html)
        self.assertIn('id="cookieBanner"', html)

    def test_static_brand_assets_exist(self):
        from django.contrib.staticfiles import finders
        for asset in ('img/favicon.svg', 'img/favicon.png', 'img/og-cover.png'):
            self.assertIsNotNone(finders.find(asset), f'missing static asset: {asset}')

    def test_registration_honeypot_blocks_bots(self):
        from core.forms import CustomerRegistrationForm, VendorRegistrationForm
        bad = CustomerRegistrationForm(data={
            'username': 'bot', 'email': 'b@b.com', 'phone_number': '081',
            'password1': 'xY9!kLm2#qWe', 'password2': 'xY9!kLm2#qWe',
            'website': 'http://spam.example',
        })
        self.assertFalse(bad.is_valid())
        self.assertIn('website', bad.errors)
        good = CustomerRegistrationForm(data={
            'username': 'human', 'email': 'h@h.com', 'phone_number': '081',
            'password1': 'xY9!kLm2#qWe', 'password2': 'xY9!kLm2#qWe',
            'website': '',
        })
        self.assertTrue(good.is_valid())
        vbad = VendorRegistrationForm(data={
            'username': 'bot2', 'email': 'b2@b.com', 'phone_number': '081',
            'password1': 'xY9!kLm2#qWe', 'password2': 'xY9!kLm2#qWe',
            'business_name': 'x', 'category': '', 'city': 'x',
            'pic_name': 'x', 'description': 'x', 'website': 'spam',
        })
        self.assertFalse(vbad.is_valid())
        self.assertIn('website', vbad.errors)

    def test_public_pages_no_broken_links(self):
        for name in ('home', 'privacy', 'terms', 'trust_guarantee',
                     'login', 'register_customer', 'register_vendor',
                     'planner_wizard', 'robots', 'sitemap'):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, f'broken page: {name}')
    def test_free_template_hidden_and_admin_gated(self):
        from core.models import FreeTemplateLead, FreeTemplateSettings
        # Anonymous → bounced to login (login required for free download)
        anon_dl = self.client.get(reverse('free_template_download'))
        self.assertEqual(anon_dl.status_code, 302)
        self.assertIn(reverse('login'), anon_dl.url)
        anon_page = self.client.get(reverse('free_template'))
        self.assertEqual(anon_page.status_code, 302)

        # Disabled by default → 404 even when logged in, NOT linked anywhere
        self.customer = CustomUser.objects.create_user(
            username='free_user', email='free@x.com', password='password123', role='CUSTOMER')
        self.client.login(username='free_user', password='password123')
        resp = self.client.get(reverse('free_template'))
        self.assertEqual(resp.status_code, 404)
        dl = self.client.get(reverse('free_template_download'))
        self.assertEqual(dl.status_code, 404)
        self.client.logout()
        home = self.client.get(reverse('home'))
        self.assertNotContains(home, reverse('free_template'))
        sm = self.client.get(reverse('sitemap'))
        self.assertNotContains(sm, reverse('free_template'))

        # Admin enables it → logged-in page, lead auto-recorded, blank file
        cfg = FreeTemplateSettings.get()
        cfg.is_enabled = True
        cfg.original_price = 15000
        cfg.save()
        self.client.login(username='free_user', password='password123')
        page = self.client.get(reverse('free_template'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Rp 0')
        self.assertContains(page, '15.000')
        self.assertContains(page, 'kosongan')
        self.assertContains(page, reverse('free_template_download'))
        self.assertTrue(FreeTemplateLead.objects.filter(email='free@x.com').exists())
        # Showcase + promo sections still there
        self.assertContains(page, 'Isi templatenya apa saja?')
        self.assertContains(page, 'Cara mengisinya gimana?')
        self.assertContains(page, 'PROMO LANGGANAN')

        file_resp = self.client.get(reverse('free_template_download'))
        self.assertEqual(file_resp.status_code, 200)
        self.assertEqual(
            file_resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_resp.content))
        self.assertIn('Dashboard', wb.sheetnames)
        # Blank: no vendor rows, vendor names anonymized
        ws2 = wb['Direktori Vendor & PIC']
        self.assertEqual(ws2.max_row, 6)
        ws1 = wb['Budget & Bayar']
        self.assertEqual(ws1.cell(row=15, column=5).value, '—')

        # Admin disables again → 404
        cfg.is_enabled = False
        cfg.save()
        self.assertEqual(self.client.get(reverse('free_template')).status_code, 404)

    def test_paid_template_pick_one_with_basic_vendors(self):
        import datetime
        import io
        import openpyxl
        from core.models import FreeTemplateSettings, Voucher, PaidTemplateDownload
        cfg = FreeTemplateSettings.get()
        cfg.is_enabled = True
        cfg.save()

        # Must login first
        anon = self.client.get(reverse('paid_template'))
        self.assertEqual(anon.status_code, 302)
        self.client.login(username='launch_user', password='password123')

        # Premium required → bounced to free page promo section
        no_premium = self.client.get(reverse('paid_template'))
        self.assertEqual(no_premium.status_code, 302)
        self.assertIn('#langganan', no_premium.url)

        # Redeem voucher → premium
        Voucher.objects.create(code='SHOPEE-PAID-30', duration_days=30, max_uses=5)
        self.client.post(reverse('free_template'), {
            'action': 'redeem', 'email': 'launch@test.com', 'code': 'SHOPEE-PAID-30'})

        # Picker lists categories
        picker = self.client.get(reverse('paid_template'))
        self.assertEqual(picker.status_code, 200)
        self.assertContains(picker, self.category.name)

        # Pick ONE category
        pick = self.client.post(reverse('paid_template'), {'category_id': self.category.id})
        self.assertEqual(pick.status_code, 302)
        self.assertTrue(PaidTemplateDownload.objects.filter(
            user__username='launch_user', event_category=self.category).exists())

        # Download: vendor list WITHOUT prices/packages/contacts
        dl = self.client.get(reverse('paid_template_download'))
        self.assertEqual(dl.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(dl.content))
        ws = wb['Direktori Vendor & PIC']
        text = " ".join([str(c.value) for r in ws.iter_rows() for c in r if c.value])
        self.assertIn(self.vendor_profile.business_name, text)
        self.assertIn('Lihat di aplikasi', text)
        self.assertNotIn(self.vendor_profile.contact_phone, text)
        self.assertNotIn(str(int(self.package.price)), text)

        # Cannot pick a second one
        other = self.client.post(reverse('paid_template'), {'category_id': self.category.id})
        self.assertEqual(other.status_code, 302)
        self.assertEqual(PaidTemplateDownload.objects.filter(user__username='launch_user').count(), 1)

    def test_floating_cta_and_ref_banner(self):
        from core.models import FreeTemplateSettings
        cfg = FreeTemplateSettings.get()
        cfg.is_enabled = True
        cfg.save()
        self.client.login(username='launch_user', password='password123')
        page = self.client.get(reverse('free_template'))
        # Floating CTA ke landing dengan penanda asal
        self.assertContains(page, 'id="lihatAplikasiFab"')
        self.assertContains(page, '/?ref=template-gratis')
        self.assertContains(page, 'Lihat Aplikasi')
        # Landing tanpa ref → tidak ada banner
        plain = self.client.get(reverse('home'))
        self.assertNotContains(plain, 'id="refBanner"')
        # Landing via tombol (dengan ref) → banner penyambutan tampil
        via = self.client.get(reverse('home') + '?ref=template-gratis')
        self.assertContains(via, 'id="refBanner"')
        self.assertContains(via, reverse('free_template'))

    def test_voucher_redeem_in_app(self):
        import datetime
        from core.models import FreeTemplateSettings, Voucher, VoucherRedemption
        cfg = FreeTemplateSettings.get()
        cfg.is_enabled = True
        cfg.save()
        self.client.login(username='launch_user', password='password123')
        v = Voucher.objects.create(code='SHOPEE-TEST-30', duration_days=30, max_uses=2)

        # Unknown code → error
        r1 = self.client.post(reverse('free_template'), {
            'action': 'redeem', 'email': 'vip@example.com', 'code': 'SALAH'})
        self.assertContains(r1, 'tidak dikenal')

        # Valid redeem → redemption created with correct expiry
        r2 = self.client.post(reverse('free_template'), {
            'action': 'redeem', 'email': 'vip@example.com', 'code': 'shopee-test-30'})
        self.assertEqual(r2.status_code, 302)
        red = VoucherRedemption.objects.get(email='vip@example.com')
        self.assertEqual(red.expires_at, datetime.date.today() + datetime.timedelta(days=30))
        v.refresh_from_db()
        self.assertEqual(v.used_count, 1)

        # Same e-mail + code again → rejected (quota habis / sudah dipakai)
        r3 = self.client.post(reverse('free_template'), {
            'action': 'redeem', 'email': 'vip@example.com', 'code': 'SHOPEE-TEST-30'})
        self.assertContains(r3, 'sudah dipakai')

        # Logged-in user redeem → premium_until set
        from core.models import CustomUser
        u = CustomUser.objects.create_user(username='vipuser', password='pw12345', role='CUSTOMER')
        v2 = Voucher.objects.create(code='SHOPEE-TEST-60', duration_days=60, max_uses=5)
        self.client.login(username='vipuser', password='pw12345')
        r4 = self.client.post(reverse('free_template'), {
            'action': 'redeem', 'email': 'vip@example.com', 'code': 'SHOPEE-TEST-60'})
        self.assertEqual(r4.status_code, 302)
        u.refresh_from_db()
        self.assertTrue(u.is_premium())
        self.assertEqual(u.premium_until, datetime.date.today() + datetime.timedelta(days=60))
