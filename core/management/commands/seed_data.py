import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder, EscrowMilestone, DisputeTicket
)


class Command(BaseCommand):
    help = 'Populates the Vendorama database with realistic curated event vendors, multi-role users, escrow milestones, savings vaults, and dispute records.'

    def handle(self, *args, **options):
        self.stdout.write("[SEED] Starting Vendorama comprehensive database seeding...")

        # 1. Clean existing records
        DisputeTicket.objects.all().delete()
        EscrowMilestone.objects.all().delete()
        BookingOrder.objects.all().delete()
        SavingsDeposit.objects.all().delete()
        EventSavingsVault.objects.all().delete()
        PlannerAccess.objects.all().delete()
        EventPlan.objects.all().delete()
        VendorPackage.objects.all().delete()
        VendorProfile.objects.all().delete()
        EventCategory.objects.all().delete()
        CustomUser.objects.all().delete()

        # 2. Create Admin Account
        admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@vendorama.id',
            password='admin123',
            role='ADMIN',
            phone_number='081100000001'
        )
        self.stdout.write("  [+] Admin user created: admin / admin123")

        # 3. Create Event Categories
        categories_data = [
            {'name': 'Pernikahan (Wedding)', 'slug': 'wedding', 'icon_name': 'heart', 'description': 'Layanan lengkap akad, resepsi, busana pengantin, hingga paket catering eksklusif.'},
            {'name': 'Corporate Gathering & Gala', 'slug': 'corporate', 'icon_name': 'briefcase', 'description': 'Event korporasi, rapat tahunan, gala dinner, dan product launching profesional.'},
            {'name': 'Ulang Tahun & Perayaan', 'slug': 'birthday', 'icon_name': 'cake', 'description': 'Pesta sweet seventeen, perayaan anak, anniversary, dan pesta kejutan privat.'},
            {'name': 'Pameran, Bazaar & Festival', 'slug': 'exhibition', 'icon_name': 'store', 'description': 'Booth pameran, tenda roder, sound panggung besar, dan logistik festival publik.'},
            {'name': 'Seminar & Workshop', 'slug': 'seminar', 'icon_name': 'presentation', 'description': 'Ruang konferensi, proyektor LED videotron, seminar kit, dan konsumsi coffee break.'},
            {'name': 'Intimate Gathering', 'slug': 'intimate', 'icon_name': 'users', 'description': 'Makan malam privat, lamaran intim, dan temu keluarga dalam skala personal.'},
        ]
        cat_objs = {}
        for c in categories_data:
            cat_objs[c['slug']] = EventCategory.objects.create(**c)
        self.stdout.write(f"  [+] Created {len(cat_objs)} event categories.")

        # 4. Create Customers (3 Distinct Scenarios)
        # Customer 1: Planning wedding, saving in vault, free planner mode
        cust1 = CustomUser.objects.create_user(
            username='andi_customer',
            email='andi@gmail.com',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567891'
        )

        # Customer 2: Corporate event, paid planner unlocked, active escrow order
        cust2 = CustomUser.objects.create_user(
            username='budi_customer',
            email='budi.perkasa@corp.id',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567892'
        )

        # Customer 3: Exhibition, had dispute resolved with full financial refund
        cust3 = CustomUser.objects.create_user(
            username='citra_customer',
            email='citra.event@gmail.com',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567893'
        )
        self.stdout.write("  [+] Created 3 customer accounts: andi_customer, budi_customer, citra_customer (pass123)")

        # 5. Create Curated Vendors
        vendors_data = [
            {
                'username': 'vendor_catering',
                'email': 'contact@royalnusantara.co.id',
                'business_name': 'Royal Nusantara Gourmet Catering',
                'anonymized_code': 'VND-CAT-01',
                'category': cat_objs['wedding'],
                'city': 'Jakarta Selatan',
                'address': 'Jl. Kemang Raya No. 45, Jakarta Selatan',
                'pic_name': 'Chef Hartono Sutedjo',
                'contact_phone': '081388991122',
                'rating': 4.9,
                'total_completed_events': 48,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Spesialis hidangan Nusantara prasmanan premium dan stall gubukan berkelas internasional. Berpengalaman melayani hingga 2.000 porsi per event dengan standar higienis sertifikasi HACCP.',
                'packages': [
                    {
                        'name': 'Paket Prasmanan Royal Nusantara Silver',
                        'price': 45000000,
                        'pax_capacity': 500,
                        'specifications': 'Menu Utama 6 Macam (Daging Sapi Lada Hitam, Ayam Suwir Bali, Ikan Kakap Asam Manis, Sup Kimlo, Nasi Goreng Spesial, Nasi Putih)\n3 Pilihan Stall Gubukan (Sate Ayam 200 porsi, Siomay Bandung 200 porsi, Zuppa Soup 200 porsi)\nPuding Buah & Es Doger Premium\nService Kru 12 Orang & Meja Buffet Mewah'
                    },
                    {
                        'name': 'Paket Sultan Imperial Grand Buffet',
                        'price': 85000000,
                        'pax_capacity': 1000,
                        'specifications': 'Menu Utama 8 Macam Pilihan Chef\n5 Pilihan Stall Gubukan (Kambing Guling 2 Ekor, Dimsum, Bakwan Malang, Tempura, Gelato)\nFree Flow Mocktail & Soft Drinks\nDekorasi Meja Prasmanan Gold Floral & Waiter Profesional 20 Orang'
                    }
                ]
            },
            {
                'username': 'vendor_dekorasi',
                'email': 'studio@kencanaart.id',
                'business_name': 'Kencana Art & Stage Architecture',
                'anonymized_code': 'VND-DEC-02',
                'category': cat_objs['wedding'],
                'city': 'Jakarta Pusat',
                'address': 'Jl. Menteng Asri No. 12, Jakarta Pusat',
                'pic_name': 'Bramantyo Wicaksono',
                'contact_phone': '081255443322',
                'rating': 4.8,
                'total_completed_events': 36,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Studio desain artistik panggung pelaminan modern, gazebo kristal, dan instalasi lorong bunga segar aromatik untuk pernikahan indoor dan semi-outdoor.',
                'packages': [
                    {
                        'name': 'Modern Elegant Botanical Backdrop',
                        'price': 35000000,
                        'pax_capacity': 500,
                        'specifications': 'Pelaminan Lebar 10-12 Meter dengan Bunga Segar Pilihan\nGazebo Masuk Akrilik & Gate Kristal\nStanding Flower 6 Titik Jalan Pengantin\nLighting Sorot Spot Panggung 8 Titik'
                    },
                    {
                        'name': 'Royal Palace Traditional Majestic',
                        'price': 60000000,
                        'pax_capacity': 1000,
                        'specifications': 'Pelaminan Adat/Modern Ukuran 16-20 Meter Penuh Bunga Import\nMini Garden Depan Pelaminan dengan Air Mancur Mini\nKarpet Rose Petal & Welcome Gate Megah\nSet Kursi Pengantin & Orang Tua Jati Eksklusif'
                    }
                ]
            },
            {
                'username': 'vendor_foto',
                'email': 'hello@luminavisuals.com',
                'business_name': 'Lumina Visuals Cinematic Studio',
                'anonymized_code': 'VND-PHO-03',
                'category': cat_objs['corporate'],
                'city': 'Bandung',
                'address': 'Jl. Dago Atas No. 88, Bandung',
                'pic_name': 'Reza Pahlevi',
                'contact_phone': '081977665544',
                'rating': 4.9,
                'total_completed_events': 62,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Tim fotografer & sinematografer profesional bersertifikasi. Melayani dokumentasi event korporasi, gala dinner, dan wedding dengan output video teaser 60 detik Same-Day Edit (SDE).',
                'packages': [
                    {
                        'name': 'Paket Full Day Cinematic Documentation',
                        'price': 18000000,
                        'pax_capacity': 500,
                        'specifications': '2 Fotografer Senior & 2 Videografer 4K Cinema\nDrone Aerial 4K Coverage\nTeaser Video SDE 1 Menit Hari H\nHighlight Video 3-5 Menit & Dokumentasi Full 30 Menit\n1 Album Cetak Kolase Magnetik Eksklusif & Flashdisk Kayu'
                    }
                ]
            },
            {
                'username': 'vendor_sound',
                'email': 'sales@soundvibe.id',
                'business_name': 'SoundVibe Pro Audio & Concert Stage',
                'anonymized_code': 'VND-SND-04',
                'category': cat_objs['exhibition'],
                'city': 'Jakarta Barat',
                'address': 'Kawasan Niaga Puri No. 7, Jakarta Barat',
                'pic_name': 'Dedi Suhendra',
                'contact_phone': '081199887766',
                'rating': 4.7,
                'total_completed_events': 41,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Penyedia sound system line-array 10.000 hingga 30.000 watt, moving-head beam lighting, panggung rigging aluminium, dan genset silent berdaya tinggi.',
                'packages': [
                    {
                        'name': 'Rigging Stage & Sound System 10.000 Watt',
                        'price': 25000000,
                        'pax_capacity': 800,
                        'specifications': 'Sound System Line Array 10.000 Watt Aktif (Subwoofer + Monitor)\nLighting System (8 Moving Head Beam, 12 ParLED RGBW, Smoke Gun)\nDigital Mixer Midas 32 Channel & 4 Wireless Mic Shure\nOperator Audio & Lighting Bersertifikasi'
                    }
                ]
            },
            {
                'username': 'vendor_venue',
                'email': 'reservation@grandpelataran.com',
                'business_name': 'Grand Pelataran Luxury Ballroom',
                'anonymized_code': 'VND-VEN-05',
                'category': cat_objs['corporate'],
                'city': 'Bandung',
                'address': 'Jl. R.E. Martadinata No. 102, Bandung',
                'pic_name': 'Indira Wardhani',
                'contact_phone': '081233445566',
                'rating': 4.9,
                'total_completed_events': 75,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Ballroom bebas pilar seluas 1.500 m2 dengan langit-langit setinggi 8 meter bertabur lampu kristal. Dilengkapi videotron indoor 12x4 meter dan area parkir 300 mobil.',
                'packages': [
                    {
                        'name': 'Ballroom Rental Full Session (6 Jam)',
                        'price': 65000000,
                        'pax_capacity': 1000,
                        'specifications': 'Penggunaan Ballroom 6 Jam + 4 Jam Loading Preparation\nVideotron Indoor P2.5 Ukuran 12x4 Meter\n3 Ruang Rias VIP AC & Ruang Transit Keluarga\nKapasitas Listrik Gedung 100.000 Watt & Genset Cadangan'
                    }
                ]
            },
            {
                'username': 'vendor_mc',
                'email': 'management@harmonimusic.com',
                'business_name': 'Harmoni Acoustic Band & Professional MC',
                'anonymized_code': 'VND-ENT-06',
                'category': cat_objs['birthday'],
                'city': 'Surabaya',
                'address': 'Jl. Manyar Kertoarjo No. 18, Surabaya',
                'pic_name': 'Tommy Kurnia',
                'contact_phone': '081766554433',
                'rating': 4.9,
                'total_completed_events': 50,
                'is_vetted': True,
                'verification_status': 'APPROVED',
                'description': 'Duo MC dwibahasa (Indonesia - Inggris) berpengalaman memandu pesta formal dan santai, dipadukan format band akustik 5 personel (Vokal, Gitar, Keyboard, Saxophone, Bass/Cajon).',
                'packages': [
                    {
                        'name': 'MC Bilingual & Live Acoustic Ensemble',
                        'price': 12000000,
                        'pax_capacity': 300,
                        'specifications': '1 MC Utama Bilingual (English / Indonesian)\n5 Musisi Akustik (Vocalist, Keyboardist, Saxophonist, Acoustic Guitarist, Cajonist)\nSound Instrumen & Soundman Pribadi\nDurasi Penampilan 3 Jam (3 Set Live Performance)'
                    }
                ]
            },
            {
                'username': 'vendor_pending',
                'email': 'admin@bintangmudalighting.com',
                'business_name': 'Bintang Muda Audio & Rigging',
                'anonymized_code': 'VND-SND-07',
                'category': cat_objs['seminar'],
                'city': 'Bali',
                'address': 'Jl. Sunset Road No. 20, Kuta, Bali',
                'pic_name': 'Gede Sukaartha',
                'contact_phone': '081299887766',
                'rating': 5.0,
                'total_completed_events': 5,
                'is_vetted': False,
                'verification_status': 'PENDING',
                'description': 'Penyedia perlengkapan sound panggung baru mendaftar di Bali. Membutuhkan verifikasi audit tim Vendorama sebelum diizinkan melayani.',
                'packages': [
                    {
                        'name': 'Seminar Sound & Dual Mic System',
                        'price': 8000000,
                        'pax_capacity': 200,
                        'specifications': 'Sound System 3000 Watt, 4 Wireless Mic, 1 Sound Engineer.'
                    }
                ]
            },
            {
                'username': 'vendor_suspended',
                'email': 'owner@defaultdecor.id',
                'business_name': 'Surabaya Decor Kreasi (Suspended Demo)',
                'anonymized_code': 'VND-DEC-08',
                'category': cat_objs['exhibition'],
                'city': 'Surabaya',
                'address': 'Jl. Rungkut Asri No. 5, Surabaya',
                'pic_name': 'Oknum Pelanggar',
                'contact_phone': '081999999999',
                'rating': 2.5,
                'total_completed_events': 3,
                'is_vetted': False,
                'verification_status': 'SUSPENDED',
                'description': 'Vendor yang disanksi pembekuan akun akibat kasus keterlambatan fatal pada acara pameran Citra Event. Bukti ketegasan perlindungan platform.',
                'packages': [
                    {
                        'name': 'Booth Exhibition Standard',
                        'price': 20000000,
                        'pax_capacity': 400,
                        'specifications': 'Booth Partisi R8.'
                    }
                ]
            }
        ]

        vendor_profiles = {}
        for vd in vendors_data:
            v_user = CustomUser.objects.create_user(
                username=vd['username'],
                email=vd['email'],
                password='pass123',
                role='VENDOR',
                phone_number=vd['contact_phone']
            )
            v_prof = VendorProfile.objects.create(
                user=v_user,
                business_name=vd['business_name'],
                anonymized_code=vd['anonymized_code'],
                category=vd['category'],
                city=vd['city'],
                address=vd['address'],
                pic_name=vd['pic_name'],
                contact_phone=vd['contact_phone'],
                contact_email=vd['email'],
                rating=vd['rating'],
                total_completed_events=vd['total_completed_events'],
                is_vetted=vd['is_vetted'],
                verification_status=vd['verification_status'],
                description=vd['description']
            )
            vendor_profiles[vd['username']] = v_prof

            for pkg in vd['packages']:
                VendorPackage.objects.create(
                    vendor=v_prof,
                    name=pkg['name'],
                    price=pkg['price'],
                    pax_capacity=pkg['pax_capacity'],
                    specifications=pkg['specifications']
                )

        self.stdout.write(f"  [+] Created {len(vendor_profiles)} vendor profiles and packages.")

        # 6. Scenario 1: Andi Customer (Wedding, Free Planner, Active Savings Vault)
        plan1 = EventPlan.objects.create(
            customer=cust1,
            title='Pernikahan Andi & Laras',
            event_category=cat_objs['wedding'],
            event_date=datetime.date(2026, 12, 20),
            city='Jakarta Selatan',
            estimated_pax=500,
            budget_min=50000000,
            budget_max=120000000,
            selected_services=['catering', 'decoration', 'documentation']
        )
        vault1 = EventSavingsVault.objects.create(
            customer=cust1,
            event_plan=plan1,
            title='Tabungan Pernikahan Andi & Laras (Target IDR 80M)',
            target_amount=80000000,
            current_amount=35000000,
            target_date=datetime.date(2026, 12, 1)
        )
        SavingsDeposit.objects.create(vault=vault1, amount=15000000, notes='Setoran Pertama - Tabungan Gaji')
        SavingsDeposit.objects.create(vault=vault1, amount=10000000, notes='Setoran Kedua - Bonus Kantor')
        SavingsDeposit.objects.create(vault=vault1, amount=10000000, notes='Setoran Ketiga - Dana Bersama')

        # 7. Scenario 2: Budi Customer (Corporate, Paid Planner UNLOCKED, Active Escrow Order with 1 milestone released)
        plan2 = EventPlan.objects.create(
            customer=cust2,
            title='Annual Corporate Gala Dinner 2026 PT Perkasa',
            event_category=cat_objs['corporate'],
            event_date=datetime.date(2026, 11, 15),
            city='Bandung',
            estimated_pax=400,
            budget_min=40000000,
            budget_max=80000000,
            selected_services=['venue', 'documentation', 'catering']
        )
        PlannerAccess.objects.create(
            customer=cust2,
            event_plan=plan2,
            fee_paid=150000,
            is_unlocked=True
        )
        catering_pkg = vendor_profiles['vendor_catering'].packages.first()
        order2 = BookingOrder.objects.create(
            order_code='ORD-CORP-202611',
            customer=cust2,
            vendor=vendor_profiles['vendor_catering'],
            package=catering_pkg,
            event_date=datetime.date(2026, 11, 15),
            total_price=catering_pkg.price,
            escrow_status='MILESTONE_1_PAID',
            notes='Menu harap dihindarkan dari olahan kacang untuk 2 tamu VIP.'
        )
        order2.create_default_milestones()
        m1 = order2.milestones.get(milestone_index=1)
        m1.status = 'RELEASED'
        m1.released_at = timezone.now() - datetime.timedelta(days=10)
        m1.save()
        m2 = order2.milestones.get(milestone_index=2)
        m2.status = 'REQUESTED'  # Vendor has requested mid-term payout
        m2.save()

        # 8. Scenario 3: Citra Customer (Exhibition, Disputed & 100% Refunded Financial Guarantee Demo)
        plan3 = EventPlan.objects.create(
            customer=cust3,
            title='Bazaar Seni & Kerajinan Surabaya 2026',
            event_category=cat_objs['exhibition'],
            event_date=datetime.date(2026, 8, 25),
            city='Surabaya',
            estimated_pax=300,
            budget_min=15000000,
            budget_max=30000000,
            selected_services=['decoration', 'sound']
        )
        suspended_pkg = vendor_profiles['vendor_suspended'].packages.first()
        order3 = BookingOrder.objects.create(
            order_code='ORD-DSP-REFUNDED',
            customer=cust3,
            vendor=vendor_profiles['vendor_suspended'],
            package=suspended_pkg,
            event_date=datetime.date(2026, 8, 25),
            total_price=suspended_pkg.price,
            escrow_status='REFUNDED',
            notes='Pemasangan partisi booth bazaar.'
        )
        order3.create_default_milestones()
        DisputeTicket.objects.create(
            ticket_code='DSP-DEMO-001',
            order=order3,
            complainant=cust3,
            reason='Vendor tidak datang tepat waktu pada H-1 loading gedung dan barang partisi yang dikirim rusak tidak sesuai spesifikasi perjanjian.',
            evidence_text='Foto dokumentasi area panggung kosong pada H-1 dan chat WhatsApp vendor tidak dapat dihubungi.',
            status='REFUNDED_TO_CUSTOMER',
            admin_notes='Investigasi tim membuktikan vendor mangkir fatal. 100% dana Escrow Rp 20.000.000 telah dikembalikan ke rekening Citra Event. Akun vendor disuspensi permanen.',
            penalty_applied=True,
            resolved_at=timezone.now() - datetime.timedelta(days=5)
        )

        self.stdout.write(self.style.SUCCESS("[SUCCESS] Vendorama database has been successfully seeded!"))
        self.stdout.write("---------------------------------------------------------------")
        self.stdout.write("Credentials:")
        self.stdout.write("  - Admin:    admin / admin123 (Pusat Kendali Escrow & Arbitrase)")
        self.stdout.write("  - Customer: andi_customer / pass123 (Pernikahan, Free Planner, Tabungan Vault)")
        self.stdout.write("  - Customer: budi_customer / pass123 (Corporate, Paid Planner Unlocked, Order Aktif)")
        self.stdout.write("  - Customer: citra_customer / pass123 (Exhibition, 100% Financial Refund Dispute Demo)")
        self.stdout.write("  - Vendor:   vendor_catering / pass123 (Royal Nusantara Gourmet)")
        self.stdout.write("  - Vendor:   vendor_foto / pass123 (Lumina Visuals)")
        self.stdout.write("---------------------------------------------------------------")
