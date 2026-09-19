import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder
)


class Command(BaseCommand):
    help = 'Populates the Vendorama database with 24+ realistic curated event vendors, multi-role users, commission-based booking orders, and savings vaults.'

    def handle(self, *args, **options):
        self.stdout.write("[SEED] Starting Vendorama comprehensive database seeding...")

        # 1. Clean existing records
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

        # 4. Create Customers
        cust1 = CustomUser.objects.create_user(
            username='andi_customer',
            email='andi@gmail.com',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567891'
        )

        cust2 = CustomUser.objects.create_user(
            username='budi_customer',
            email='budi.perkasa@corp.id',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567892'
        )

        cust3 = CustomUser.objects.create_user(
            username='citra_customer',
            email='citra.event@gmail.com',
            password='pass123',
            role='CUSTOMER',
            phone_number='081234567893'
        )
        self.stdout.write("  [+] Created 3 customer accounts: andi_customer, budi_customer, citra_customer (pass123)")

        # 5. Create 24 Curated Vendors from design system catalog
        raw_vendors = [
            {
                'username': 'anargya_estate',
                'email': 'contact@anargyaestate.com',
                'business_name': 'Anargya Estate Bandung',
                'code': 'VND-VEN-01',
                'cat': cat_objs['wedding'],
                'city': 'Bandung',
                'address': 'Jl. Dago Giri No. 102, Bandung',
                'pic': 'Arif Wicaksana',
                'phone': '081233441101',
                'rating': 4.8,
                'events': 52,
                'desc': 'Kebun outdoor dengan kapasitas hingga 400 tamu, pemandangan perbukitan asri, dan fasilitas villa transit keluarga.',
                'packages': [
                    {'name': 'Paket Sunset Garden Wedding', 'price': 45000000, 'pax': 300, 'specs': 'Sewa venue kebun 8 jam\nLighting kebun & fairy lights\nVilla transit pengantin 2 kamar'},
                    {'name': 'Paket Exclusive Hills Full Estate', 'price': 120000000, 'pax': 500, 'specs': 'Eksklusif seluruh area estate 2 hari 1 malam\nFasilitas 4 villa privat\nGenset 40 kVA & kebersihan penuh'}
                ]
            },
            {
                'username': 'griya_cempaka',
                'email': 'info@griyacempaka.id',
                'business_name': 'Griya Cempaka Hall',
                'code': 'VND-VEN-02',
                'cat': cat_objs['corporate'],
                'city': 'Jakarta',
                'address': 'Jl. Cempaka Putih Raya No. 45, Jakarta Pusat',
                'pic': 'Hendra Setiawan',
                'phone': '081233441102',
                'rating': 4.5,
                'events': 44,
                'desc': 'Gedung serbaguna indoor dengan tata ruang fleksibel, cocok untuk acara korporat, gala dinner, maupun resepsi keluarga.',
                'packages': [
                    {'name': 'Half Day Hall Rental', 'price': 25000000, 'pax': 300, 'specs': 'Gedung indoor AC 5 jam\nSound standard & 4 mic wireless\nKursi banquet 200 buah'},
                    {'name': 'Full Day Corporate Grand Ballroom', 'price': 70000000, 'pax': 800, 'specs': 'Pemakaian gedung 10 jam\nVideotron panggung 8x3 meter\nRuang VIP meeting & transit'}
                ]
            },
            {
                'username': 'balenio_rooftop',
                'email': 'hello@baleniorooftop.com',
                'business_name': 'Balenio Sky Rooftop',
                'code': 'VND-VEN-03',
                'cat': cat_objs['intimate'],
                'city': 'Surabaya',
                'address': 'Mayjen Sungkono No. 89, Surabaya',
                'pic': 'Jessica Natalie',
                'phone': '081233441103',
                'rating': 4.6,
                'events': 38,
                'desc': 'Rooftop modern dengan pemandangan cakrawala kota Surabaya, sangat populer untuk acara lamaran, dinner intim, dan perayaan privat.',
                'packages': [
                    {'name': 'Intimate Rooftop Soiree', 'price': 18000000, 'pax': 80, 'specs': 'Area rooftop semi-outdoor 4 jam\nBar & mocktail lounge\nSound ambience & lighting gantung'},
                    {'name': 'Golden Hour Sunset Package', 'price': 50000000, 'pax': 150, 'specs': 'Eksklusif rooftop privat 6 jam\nDekorasi kanopi neon & bunga kering\nDJ equipment & sound system'}
                ]
            },
            {
                'username': 'rasa_nusantara',
                'email': 'order@rasanusantaracatering.co.id',
                'business_name': 'Rasa Nusantara Gourmet Catering',
                'code': 'VND-CAT-04',
                'cat': cat_objs['wedding'],
                'city': 'Jakarta',
                'address': 'Jl. Tebet Barat No. 12, Jakarta Selatan',
                'pic': 'Chef Hartono Sutedjo',
                'phone': '081388991122',
                'rating': 4.7,
                'events': 78,
                'desc': 'Paket prasmanan dan buffet dengan menu nusantara autentik, fleksibel menyesuaikan jumlah tamu dan standar higienis bersertifikasi.',
                'packages': [
                    {'name': 'Paket Prasmanan Selera Nusantara', 'price': 28000000, 'pax': 300, 'specs': 'Menu utama 5 macam lauk\n2 stall gubukan (Sate & Siomay)\nDessert pudding & es kopyor'},
                    {'name': 'Paket Royal Imperial Banquet', 'price': 65000000, 'pax': 600, 'specs': 'Menu utama 7 macam pilihan chef\n4 stall gubukan premium (Kambing Guling, Zuppa, Dimsum, Bakso)\nPelayanan waiter 16 orang'}
                ]
            },
            {
                'username': 'cita_rasa_elok',
                'email': 'info@citarasaelok.com',
                'business_name': 'Cita Rasa Elok Fine Dining',
                'code': 'VND-CAT-05',
                'cat': cat_objs['corporate'],
                'city': 'Bandung',
                'address': 'Jl. Progo No. 25, Bandung',
                'pic': 'Chef Marcelina',
                'phone': '081233441105',
                'rating': 4.9,
                'events': 61,
                'desc': 'Fine dining plating dan canapé elegan untuk acara formal dan korporat, dekorasi meja disertakan dengan konsep aesthetic.',
                'packages': [
                    {'name': '4-Course Plated Gala Dinner', 'price': 35000000, 'pax': 100, 'specs': 'Set menu 4-course fine dining\nMeja banquet table runner floral\nButler service berpengalaman'},
                    {'name': 'Grand VIP Presidential Plating', 'price': 60000000, 'pax': 200, 'specs': 'Set menu 5-course steak & seafood\nWine glasses & premium chinaware\nLive acoustic backdrop accompaniment'}
                ]
            },
            {
                'username': 'dapur_selera_ibu',
                'email': 'dapurseleraibu@gmail.com',
                'business_name': 'Dapur Selera Ibu Katering',
                'code': 'VND-CAT-06',
                'cat': cat_objs['birthday'],
                'city': 'Yogyakarta',
                'address': 'Jl. Kaliurang KM 8, Yogyakarta',
                'pic': 'Ibu Sri Rahayu',
                'phone': '081233441106',
                'rating': 4.4,
                'events': 34,
                'desc': 'Katering rumahan khas Jogja dengan cita rasa gurih otentik dan harga bersahabat, cocok untuk tasyakuran dan acara keluarga.',
                'packages': [
                    {'name': 'Paket Prasmanan Guyub Rukun', 'price': 8000000, 'pax': 150, 'specs': 'Nasi gurih, gudeg komplit, opor ayam\nEs dawet ayu & buah potong segar\nMeja saji prasmanan tradisional'},
                    {'name': 'Paket Kenduri Spesial', 'price': 20000000, 'pax': 350, 'specs': 'Menu prasmanan 6 jenis lauk\nStall bakso & sate klathak\nFree delivery wilayah DIY'}
                ]
            },
            {
                'username': 'kembang_senja',
                'email': 'studio@kembangsenj合う.id',
                'business_name': 'Kembang Senja Decor',
                'code': 'VND-DEC-07',
                'cat': cat_objs['wedding'],
                'city': 'Bandung',
                'address': 'Jl. Cihampelas No. 190, Bandung',
                'pic': 'Nadia Larasati',
                'phone': '081233441107',
                'rating': 4.8,
                'events': 57,
                'desc': 'Dekorasi bunga segar lokal & impor dengan konsep tematik custom, mulai dari gaya botanical rustic hingga modern minimalist.',
                'packages': [
                    {'name': 'Botanical Minimalist Backdrop', 'price': 22000000, 'pax': 300, 'specs': 'Backdrop pelaminan bunga segar 8 meter\nStanding flower 4 titik jalan\nLighting sorot spotlight stage'},
                    {'name': 'Grand Floral Paradise', 'price': 55000000, 'pax': 600, 'specs': 'Pelaminan megah 14 meter penuh mawar & hydrangea\nGazebo entrance lorong bunga segar\nSet meja akad nikah & photo booth custom'}
                ]
            },
            {
                'username': 'petal_co',
                'email': 'aloha@petalandco.bali.com',
                'business_name': 'Petal & Co Floral Design',
                'code': 'VND-DEC-08',
                'cat': cat_objs['wedding'],
                'city': 'Bali',
                'address': 'Jl. Raya Seminyak No. 40, Bali',
                'pic': 'Wayana Putri',
                'phone': '081233441108',
                'rating': 4.9,
                'events': 72,
                'desc': 'Spesialis dekorasi outdoor tropis dan cliff-top wedding di Bali, banyak dipercaya untuk pernikahan impian dan intimate destination.',
                'packages': [
                    {'name': 'Tropical Boho Beachfront Arch', 'price': 35000000, 'pax': 100, 'specs': 'Arch pelaminan bambu & palm fronds\nKarpet kelopak bunga rose petal sepanjang altar\nHand bouquet pengantin & corsage'},
                    {'name': 'Luxury Cliffside Floral Installation', 'price': 90000000, 'pax': 250, 'specs': 'Instalasi kanopi bunga gantung di atas meja makan\nLighting ambient warm sunset & chandelier\nFull bridal table centerpiece & chair decor'}
                ]
            },
            {
                'username': 'dekor_hemat_ceria',
                'email': 'dekorceria@gmail.com',
                'business_name': 'Dekor Hemat Ceria',
                'code': 'VND-DEC-09',
                'cat': cat_objs['birthday'],
                'city': 'Semarang',
                'address': 'Jl. Pandanaran No. 56, Semarang',
                'pic': 'Doni Prasetya',
                'phone': '081233441109',
                'rating': 4.3,
                'events': 29,
                'desc': 'Dekorasi balon, styrofoam 3D, dan backdrop sederhana berbiaya hemat untuk ulang tahun anak, sweet seventeen, dan tasyakuran.',
                'packages': [
                    {'name': 'Paket Balon Backdrop Tematik', 'price': 4500000, 'pax': 50, 'specs': 'Arch balon warna custom & banner cetak\nMeja cake & display makanan penutup\nLighting ring light selfie'},
                    {'name': 'Paket Pesta Sweet 17 Glamour', 'price': 12000000, 'pax': 100, 'specs': 'Backdrop glitter & neon sign nama\nInstalasi balon organik & karpet merah\nStanding photo booth instagramable'}
                ]
            },
            {
                'username': 'cahaya_abadi_photo',
                'email': 'team@cahayaabadi.photo',
                'business_name': 'Cahaya Abadi Photography',
                'code': 'VND-PHO-10',
                'cat': cat_objs['wedding'],
                'city': 'Jakarta',
                'address': 'Jl. Fatmawati No. 77, Jakarta Selatan',
                'pic': 'Bagas Pratama',
                'phone': '081233441110',
                'rating': 4.8,
                'events': 68,
                'desc': 'Tim dokumentasi foto & video sinematik, termasuk drone pilot berlisensi dan layanan video teaser Same-Day Edit (SDE).',
                'packages': [
                    {'name': 'Silver Cinematic Coverage', 'price': 15000000, 'pax': 300, 'specs': '2 Fotografer & 1 Videografer\nLiputan 8 jam kerja\nHighlight video 3 menit & album 100 foto'},
                    {'name': 'Royal Drone & Same-Day Edit Teaser', 'price': 35000000, 'pax': 800, 'specs': '3 Fotografer & 2 Videografer 4K Cinema\nDrone aerial view 4K\nVideo SDE 60 detik tayang saat resepsi\n2 Album cetak magnetik kulit eksklusif'}
                ]
            },
            {
                'username': 'momentum_studio',
                'email': 'hello@momentumstudio.id',
                'business_name': 'Momentum Studio Visual',
                'code': 'VND-PHO-11',
                'cat': cat_objs['seminar'],
                'city': 'Surabaya',
                'address': 'Jl. Dharmahusada No. 34, Surabaya',
                'pic': 'Ferry Santoso',
                'phone': '081233441111',
                'rating': 4.6,
                'events': 42,
                'desc': 'Paket foto candid dan liputan acara harian dengan harga bersahabat untuk corporate gathering, wisuda, dan seminar.',
                'packages': [
                    {'name': 'Event Half Day Documentation', 'price': 6000000, 'pax': 150, 'specs': '1 Fotografer senior 4 jam\nSemua foto warna diedit (color graded)\nGoogle Drive transfer link dalam 48 jam'},
                    {'name': 'Conference & Seminar Pro Pack', 'price': 16000000, 'pax': 400, 'specs': '2 Fotografer & 1 Videografer full day\nVideo rekaman materi sesi seminar\nFoto dokumentasi formal pembicara & peserta'}
                ]
            },
            {
                'username': 'frame_feels',
                'email': 'booking@frameandfeels.com',
                'business_name': 'Frame & Feels Editorial Studio',
                'code': 'VND-PHO-12',
                'cat': cat_objs['wedding'],
                'city': 'Bali',
                'address': 'Jl. Pantai Batu Bolong, Canggu, Bali',
                'pic': 'Satria Mandala',
                'phone': '081233441112',
                'rating': 4.9,
                'events': 83,
                'desc': 'Gaya dokumentasi editorial majalah mode dan candid emosional, sangat diminati untuk destination wedding di pulau dewata.',
                'packages': [
                    {'name': 'Editorial Storytelling Pack', 'price': 22000000, 'pax': 100, 'specs': '2 Fotografer editorial bergaya analog & digital\nLiputan persiapan hingga resepsi malam\n100 Lembar fine art prints box'},
                    {'name': 'Cinematic Film & Full Wedding Day', 'price': 40000000, 'pax': 200, 'specs': '3 Fotografer & 2 Sinematografer\nFilm sinematik wedding 10 menit berlisensi musik\nFoto teaser 20 frame dalam 24 jam'}
                ]
            },
            {
                'username': 'mc_ardian',
                'email': 'ardian.wicaksana@mcpro.id',
                'business_name': 'MC Ardian Wicaksana & Associates',
                'code': 'VND-ENT-13',
                'cat': cat_objs['corporate'],
                'city': 'Jakarta',
                'address': 'Jl. Rasuna Said Kav. 8, Jakarta Selatan',
                'pic': 'Ardian Wicaksana',
                'phone': '081233441113',
                'rating': 4.7,
                'events': 95,
                'desc': 'Master of Ceremony (MC) berpengalaman bilingual Indonesia-Inggris untuk acara formal korporasi, konferensi internasional, dan gala dinner.',
                'packages': [
                    {'name': 'MC Formal Corporate & Seminar (4 Jam)', 'price': 5000000, 'pax': 300, 'specs': '1 MC Senior Bilingual\nBriefing materi & rundown H-3\nPenguasaan tata protokoler kenegaraan/BUMN'},
                    {'name': 'MC Grand Gala Dinner & Awarding Night', 'price': 12000000, 'pax': 700, 'specs': 'Duo MC (Pria & Wanita) 6 Jam\nIce breaking cerdas & pembagian award\nKoordinasi panggung bersama tim EO'}
                ]
            },
            {
                'username': 'sanggar_lentera',
                'email': 'sanggarlentera@gmail.com',
                'business_name': 'Sanggar Seni Lentera Nusantara',
                'code': 'VND-ENT-14',
                'cat': cat_objs['wedding'],
                'city': 'Yogyakarta',
                'address': 'Jl. Tamansari No. 14, Yogyakarta',
                'pic': 'Roro Endang',
                'phone': '081233441114',
                'rating': 4.5,
                'events': 37,
                'desc': 'Pertunjukan tari tradisional Jawa (Cucuk Lampah, Bedhaya), tari kreasi modern nusantara, dan gamelan live untuk prosesi adat sakral.',
                'packages': [
                    {'name': 'Prosesi Cucuk Lampah & Tari Kirab', 'price': 5500000, 'pax': 300, 'specs': '4 Penari kirab pengantin berkostum lengkap\n1 Tokoh cucuk lampah / manggolo yudo\nGamelan playback & instruksi prosesi adat'},
                    {'name': 'Paket Kirab Agung Gamelan Live', 'price': 14000000, 'pax': 600, 'specs': '8 Penari & 12 Pengrawit gamelan slendro pelog\nTari Bedhaya penyambutan tamu VIP\nBusana adat keraton resmi'}
                ]
            },
            {
                'username': 'live_band_harmoni',
                'email': 'harmoniband@musician.id',
                'business_name': 'Live Band Harmoni Acoustic & Brass',
                'code': 'VND-ENT-15',
                'cat': cat_objs['wedding'],
                'city': 'Bandung',
                'address': 'Jl. Dipati Ukur No. 44, Bandung',
                'pic': 'Rian Perkasa',
                'phone': '081233441115',
                'rating': 4.6,
                'events': 49,
                'desc': 'Live music akustik intim hingga full band 7-piece dengan seksi tiup saxophone untuk memeriahkan resepsi pernikahan dan anniversary.',
                'packages': [
                    {'name': 'Acoustic Quartet (4 Personel)', 'price': 8000000, 'pax': 200, 'specs': 'Vokal, Gitar Akustik, Keyboard, Bass/Cajon\n3 Set lagu (3x45 menit)\nSound instrumen pribadi'},
                    {'name': 'Full Entertainment Big Band', 'price': 25000000, 'pax': 600, 'specs': '7 Musisi (2 Vokal, Saxophone, Drum, Bass, Gitar, Keyboard)\nPlaylist lagu custom favorit klien\nInteraksi panggung & MC pendamping'}
                ]
            },
            {
                'username': 'titimangsa_wo',
                'email': 'plan@titimangsawo.com',
                'business_name': 'Titimangsa Wedding & Event Organizer',
                'code': 'VND-EO-16',
                'cat': cat_objs['wedding'],
                'city': 'Jakarta',
                'address': 'Kebayoran Baru No. 33, Jakarta Selatan',
                'pic': 'Rini Kusumastuti',
                'phone': '081233441116',
                'rating': 4.8,
                'events': 88,
                'desc': 'Layanan perencanaan pernikahan menyeluruh (full planning) dari penentuan konsep, kurasi vendor, penjadwalan anggaran hingga eksekusi hari-H.',
                'packages': [
                    {'name': 'Wedding Day Coordination (Hari-H)', 'price': 22000000, 'pax': 500, 'specs': 'Tim 8 orang kru profesional on-site\nTechnical meeting dengan seluruh vendor\nManajemen rundown dari subuh hingga selesai'},
                    {'name': 'Full Service Wedding Planning & Design', 'price': 95000000, 'pax': 1000, 'specs': 'Pendampingan konsultasi 6 bulan intensif\nNegosiasi harga ke seluruh vendor mitra\nTim hari-H 14 orang & asisten pribadi pengantin'}
                ]
            },
            {
                'username': 'sinergi_eo',
                'email': 'projects@sinergievent.com',
                'business_name': 'Sinergi Event Solutions Surabaya',
                'code': 'VND-EO-17',
                'cat': cat_objs['corporate'],
                'city': 'Surabaya',
                'address': 'Jl. Basuki Rahmat No. 70, Surabaya',
                'pic': 'Budi Hermawan',
                'phone': '081233441117',
                'rating': 4.5,
                'events': 51,
                'desc': 'Spesialis perencana acara korporat, pameran B2B, seminar berskala nasional, dan product launch di wilayah Jawa Timur.',
                'packages': [
                    {'name': 'Corporate Gathering Organizer', 'price': 18000000, 'pax': 300, 'specs': 'Tim EO 8 personel berseragam\nRegistrasi barcode digital peserta\nManajemen stage, hadiah, dan rundown'},
                    {'name': 'Mega Conference & Expo Organizer', 'price': 60000000, 'pax': 1000, 'specs': 'Manajemen 20 kru multi-divisi\nSistem ticketing & booth tenant management\nLiputan media partner & press conference'}
                ]
            },
            {
                'username': 'bersama_rencana_eo',
                'email': 'kontak@bersamarencana.id',
                'business_name': 'Bersama Rencana EO Semarang',
                'code': 'VND-EO-18',
                'cat': cat_objs['birthday'],
                'city': 'Semarang',
                'address': 'Jl. Erlangga Tengah No. 11, Semarang',
                'pic': 'Bayu Wicaksono',
                'phone': '081233441118',
                'rating': 4.4,
                'events': 32,
                'desc': 'Paket EO ringkas dan fleksibel untuk perayaan ulang tahun, reuni keluarga, gathering komunitas, dan acara kantor skala menengah.',
                'packages': [
                    {'name': 'Paket Pesta Komunitas / Reuni', 'price': 9000000, 'pax': 150, 'specs': 'Tim koordinasi 4 kru on site\nRundown acara & games interaktif\nDokumentasi foto serah terima'},
                    {'name': 'Paket All-In One Family Milestone', 'price': 28000000, 'pax': 300, 'specs': 'Penyusunan konsep tematik dan vendor koordinasi\nTim pelaksana 8 orang\nFree souvenir organizer support'}
                ]
            },
            {
                'username': 'gema_sonic_audio',
                'email': 'booking@gemasonic.com',
                'business_name': 'Gema Sonic Pro Audio',
                'code': 'VND-SND-19',
                'cat': cat_objs['corporate'],
                'city': 'Jakarta',
                'address': 'Jl. Panjang No. 18, Jakarta Barat',
                'pic': 'Teguh Pamungkas',
                'phone': '081233441119',
                'rating': 4.6,
                'events': 47,
                'desc': 'Sound system line-array 5.000 hingga 20.000 watt, moving head beam lighting, dan genset silent untuk acara indoor maupun outdoor.',
                'packages': [
                    {'name': 'Indoor Ballroom Sound 5000 Watt', 'price': 6500000, 'pax': 300, 'specs': 'Sound System 5000 Watt Aktif\n4 Wireless Mic Shure & 1 Digital Mixer\n1 Operator sound bersertifikasi'},
                    {'name': 'Outdoor Stage Sound & Lighting 15000 Watt', 'price': 24000000, 'pax': 800, 'specs': 'Line array sound 15.000 watt\nLighting panggung 16 parLED & 8 moving beam\nGenset silent 60 kVA selama 8 jam'}
                ]
            },
            {
                'username': 'cahaya_panggung_pro',
                'email': 'rental@cahayapanggung.id',
                'business_name': 'Cahaya Panggung Pro Bandung',
                'code': 'VND-SND-20',
                'cat': cat_objs['exhibition'],
                'city': 'Bandung',
                'address': 'Jl. Soekarno Hatta No. 340, Bandung',
                'pic': 'Fajar Nugraha',
                'phone': '081233441120',
                'rating': 4.7,
                'events': 58,
                'desc': 'Tata panggung rigging aluminium kokoh, lighting artistik visual, dan LED Videotron raksasa untuk konser, pameran, dan festival besar.',
                'packages': [
                    {'name': 'Lighting Panggung Artistik & Fog Machine', 'price': 12000000, 'pax': 400, 'specs': '12 Moving beam, 16 parLED, hazzer effect\nRigging gantung lighting aluminium\nLighting designer operator'},
                    {'name': 'Rigging Stage Mega Exhibition & LED Screen', 'price': 40000000, 'pax': 1000, 'specs': 'Panggung 12x8 meter tinggi 1.5 meter\nLED Videotron outdoor P3.9 ukuran 6x4 meter\nSound system festival 20.000 watt'}
                ]
            },
            {
                'username': 'ayu_rias_pengantin',
                'email': 'salon@ayurias.id',
                'business_name': 'Ayu Rias & Busana Pengantin Tradisional',
                'code': 'VND-MUA-21',
                'cat': cat_objs['wedding'],
                'city': 'Yogyakarta',
                'address': 'Jl. Kusumanegara No. 80, Yogyakarta',
                'pic': 'Ibu Ayu Sundari',
                'phone': '081233441121',
                'rating': 4.8,
                'events': 64,
                'desc': 'Spesialis rias pengantin adat Jawa (Paes Ageng, Jogja Putri, Solo Basahan) dan modifikasi modern, termasuk sewa busana adat beludru mewah.',
                'packages': [
                    {'name': 'Rias Akad Nikah & Busana Pengantin', 'price': 5000000, 'pax': 100, 'specs': 'Makeup pengantin wanita & pria\nSewa 1 pasang busana akad nikah\nMelati segar & ronce bunga'},
                    {'name': 'Paket Lengkap Paes Ageng & Resepsi', 'price': 18000000, 'pax': 500, 'specs': 'Paes ageng tradisional khas keraton\n2 Pasang busana pengantin ganti resepsi\nMakeup & busana untuk 2 pasang orang tua & 4 penerima tamu'}
                ]
            },
            {
                'username': 'glow_makeup_studio',
                'email': 'glowmakeup@mua.com',
                'business_name': 'Glow Makeup Studio Jakarta',
                'code': 'VND-MUA-22',
                'cat': cat_objs['birthday'],
                'city': 'Jakarta',
                'address': 'Jl. Gunawarman No. 22, Jakarta Selatan',
                'pic': 'Clara Belinda',
                'phone': '081233441122',
                'rating': 4.5,
                'events': 39,
                'desc': 'Makeup artist berpengalaman untuk pesta sweet seventeen, wisuda, maternity, pre-wedding, dan modern bridal glam look.',
                'packages': [
                    {'name': 'Party & Graduation Glam Look', 'price': 3500000, 'pax': 50, 'specs': 'Makeup tahan lama 12 jam (Airbrush HD)\nHairdo atau hijab styling modern\nFree pemasangan bulu mata artisan'},
                    {'name': 'Pre-Wedding & Engagement Full Look', 'price': 14000000, 'pax': 100, 'specs': 'Makeup lamaran / pre-wed 2 kali ganti look\nStandby touch up di lokasi 6 jam\nMakeup untuk 2 orang keluarga inti'}
                ]
            },
            {
                'username': 'kertas_kata',
                'email': 'halo@kertaskata.com',
                'business_name': 'Kertas & Kata Undangan & Souvenir',
                'code': 'VND-SOU-23',
                'cat': cat_objs['wedding'],
                'city': 'Bandung',
                'address': 'Jl. Trunojoyo No. 17, Bandung',
                'pic': 'Dimas Prasetyo',
                'phone': '081233441123',
                'rating': 4.6,
                'events': 71,
                'desc': 'Undangan pernikahan custom design, website undangan digital interaktif, dan souvenir handmade ramah lingkungan berkualitas tinggi.',
                'packages': [
                    {'name': 'Paket Undangan Digital & 300 Cetak Hardcover', 'price': 4500000, 'pax': 300, 'specs': '300 Pcs undangan hardcover foil emas\nWebsite undangan digital interaktif RSVP\nFree buku tamu custom nama'},
                    {'name': 'Paket Souvenir Eco-Friendly Premium 500 Pcs', 'price': 12000000, 'pax': 500, 'specs': '500 Pcs pouch kanvas kulit sintetis beremboss\nPackaging box eksklusif & kartu ucapan terima kasih\nDesain custom grafir logo inisial'}
                ]
            },
            {
                'username': 'tenda_prima_sejahtera',
                'email': 'sewatenda@primasejahtera.id',
                'business_name': 'Tenda Prima Sejahtera Semarang',
                'code': 'VND-TND-24',
                'cat': cat_objs['exhibition'],
                'city': 'Semarang',
                'address': 'Jl. Majapahit No. 188, Semarang',
                'pic': 'Kusnadi',
                'phone': '081233441124',
                'rating': 4.4,
                'events': 46,
                'desc': 'Sewa tenda roder transparan, tenda dekorasi VIP serut plafon, panggung portable, AC standing, mist fan, dan kursi banquet.',
                'packages': [
                    {'name': 'Paket Tenda Dekorasi VIP 100 m2', 'price': 7500000, 'pax': 200, 'specs': 'Tenda plafon serut warna custom 100 m2\nLampu lampion hias & kain tirai samping\n100 Kursi futura berlapis cover ketat'},
                    {'name': 'Tenda Roder Bening & Full AC Cooling System', 'price': 28000000, 'pax': 600, 'specs': 'Tenda roder transparan 15x20 meter tanpa tiang tengah\n4 Unit AC standing 5 PK & 4 misting fan\nFlooring kayu karpet abu-abu tebal'}
                ]
            }
        ]

        created_vendors = {}
        for item in raw_vendors:
            user = CustomUser.objects.create_user(
                username=item['username'],
                email=item['email'],
                password='pass123',
                role='VENDOR',
                phone_number=item['phone']
            )
            v_profile = VendorProfile.objects.create(
                user=user,
                business_name=item['business_name'],
                anonymized_code=item['code'],
                category=item['cat'],
                city=item['city'],
                address=item['address'],
                pic_name=item['pic'],
                contact_phone=item['phone'],
                contact_email=item['email'],
                rating=item['rating'],
                total_completed_events=item['events'],
                is_vetted=True,
                verification_status='APPROVED',
                description=item['desc']
            )
            for pkg in item['packages']:
                VendorPackage.objects.create(
                    vendor=v_profile,
                    name=pkg['name'],
                    price=pkg['price'],
                    pax_capacity=pkg['pax'],
                    specifications=pkg['specs']
                )
            created_vendors[item['username']] = v_profile

        self.stdout.write(f"  [+] Successfully created {len(created_vendors)} curated vendors with realistic packages!")

        # 6. Scenario 1: Andi Customer (Wedding, Free Planner, Savings Vault)
        plan1 = EventPlan.objects.create(
            customer=cust1,
            title='Pernikahan Andi & Laras',
            event_category=cat_objs['wedding'],
            event_date=datetime.date(2026, 12, 20),
            city='Jakarta',
            estimated_pax=500,
            budget_min=30000000,
            budget_max=80000000,
            selected_services=['venue', 'catering', 'dekorasi', 'foto']
        )
        vault1 = EventSavingsVault.objects.create(
            customer=cust1,
            event_plan=plan1,
            title='Tabungan Pernikahan Impian Andi & Laras',
            target_amount=100000000,
            current_amount=45000000,
            target_date=datetime.date(2026, 12, 1)
        )
        SavingsDeposit.objects.create(vault=vault1, amount=25000000, notes='Setoran Pertama - Tabungan Awal')
        SavingsDeposit.objects.create(vault=vault1, amount=10000000, notes='Setoran Kedua - Bonus Kantor')
        SavingsDeposit.objects.create(vault=vault1, amount=10000000, notes='Setoran Ketiga - Dana Bersama')

        # 7. Scenario 2: Budi Customer (Corporate, Paid Planner UNLOCKED, Confirmed Order)
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
        cat_pkg = created_vendors['cita_rasa_elok'].packages.first()
        BookingOrder.objects.create(
            order_code='ORD-CORP-202611',
            customer=cust2,
            vendor=created_vendors['cita_rasa_elok'],
            package=cat_pkg,
            event_date=datetime.date(2026, 11, 15),
            total_price=cat_pkg.price,
            status='CONFIRMED',
            notes='Menu harap dihindarkan dari olahan kacang untuk 2 tamu VIP.'
        )

        # 8. Scenario 3: Citra Customer (Exhibition, Completed Order with Settled Commission)
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
        photo_pkg = created_vendors['momentum_studio'].packages.first()
        BookingOrder.objects.create(
            order_code='ORD-EXH-SUCCESS',
            customer=cust3,
            vendor=created_vendors['momentum_studio'],
            package=photo_pkg,
            event_date=datetime.date(2026, 8, 25),
            total_price=photo_pkg.price,
            status='COMPLETED',
            commission_status='PAID',
            notes='Dokumentasi dan liputan pameran seni.'
        )

        self.stdout.write(self.style.SUCCESS("[SUCCESS] Vendorama database has been populated with 24 curated vendors!"))
        self.stdout.write("---------------------------------------------------------------")
        self.stdout.write("Credentials:")
        self.stdout.write("  - Admin:    admin / admin123")
        self.stdout.write("  - Customer: andi_customer / pass123")
        self.stdout.write("  - Customer: budi_customer / pass123")
        self.stdout.write("  - Customer: citra_customer / pass123")
        self.stdout.write("  - Vendors:  anargya_estate, rasa_nusantara, kembang_senja, etc. (pass123)")
        self.stdout.write("---------------------------------------------------------------")
