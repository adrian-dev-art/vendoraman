import io
import datetime
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from .templatetags.currency_tags import intdot


def get_planner_master_data(plan):
    """
    Returns structured data dictionary for web rendering (results.html and deck.html),
    including financial KPIs, interactive catering simulation, multi-tier deadline roadmap,
    and 20-item master equipment checklist.
    """
    import datetime
    today = datetime.date.today()
    days_left = (plan.event_date - today).days if plan.event_date else 0
    pax = plan.estimated_pax or 500
    pagu = float(plan.budget_max or 100000000)

    # Catering default simulator
    phys_inv = round(pax * 0.4)
    dig_inv = round(pax * 0.2)
    tamu_calc = round((phys_inv * 2.0) + (dig_inv * 1.5))
    buffer_pax = round(tamu_calc * 0.10)
    total_porsi = tamu_calc + buffer_pax
    buffet_portions = round(total_porsi * 0.60)
    stall_portions = round(total_porsi * 0.40 * 4)
    buffet_price = 95000
    stall_price = 25000
    subtotal_buffet = buffet_portions * buffet_price
    subtotal_stall = stall_portions * stall_price
    total_food_cost = subtotal_buffet + subtotal_stall
    food_cost_per_pax = round(total_food_cost / total_porsi) if total_porsi else 0

    scenarios = [
        {
            'name': 'Kalau tamu sedikit (80% datang)',
            'pax': round(total_porsi * 0.8),
            'cost': round(total_food_cost * 0.8),
            'badge': 'Hemat 20%',
            'desc': 'Kalau sebagian tamu berhalangan hadir',
        },
        {
            'name': 'Perkiraan normal (100% datang)',
            'pax': total_porsi,
            'cost': total_food_cost,
            'badge': 'Rekomendasi Utama',
            'desc': 'Jumlah aman + 10% cadangan untuk panitia',
        },
        {
            'name': 'Kalau tamu membludak (120% datang)',
            'pax': round(total_porsi * 1.2),
            'cost': round(total_food_cost * 1.2),
            'badge': 'Buffer Ekstra',
            'desc': 'Cadangan kalau yang datang lebih banyak',
        }
    ]

    facilities = [
        {'item': 'Kebutuhan Air Mineral & Minuman', 'qty': round(total_porsi * 1.5), 'unit': 'Gelas / Botol', 'note': 'Rasio konsumsi 1.5 cup minuman per tamu'},
        {'item': 'Kebutuhan Meja Bundar VIP (10 Pax)', 'qty': max(1, round(total_porsi * 0.15 / 10)), 'unit': 'Meja Bundar', 'note': 'Alokasi 15% kursi VIP & keluarga inti'},
        {'item': 'Estimasi Kursi Duduk (Flow 70%)', 'qty': round(total_porsi * 0.70), 'unit': 'Kursi Tamu', 'note': 'Standar flow ballroom standing party'},
        {'item': 'Kapasitas Area Parkir Tamu', 'qty': round(total_porsi * 0.35), 'unit': 'Slot Mobil', 'note': 'Asumsi 1 mobil membawa 2.5–3 orang tamu'},
    ]

    slug = ''
    try:
        if plan.event_category and plan.event_category.slug:
            slug = plan.event_category.slug.lower()
    except Exception:
        slug = ''
    is_wedding = (slug == 'wedding')

    monthly_targets = [
        {'code': 'H-6', 'period': '6 Bulan Sebelum', 'title': 'Penyusunan Anggaran & Eksplorasi Vendor', 'pic': 'Customer & Pasangan', 'status': 'Selesai', 'desc': 'Penyusunan pagu anggaran awal, estimasi jumlah pax, dan eksplorasi kurasi vendor di Vendoraman.'},
        {'code': 'H-5', 'period': '5 Bulan Sebelum', 'title': 'Kunci Venue & Booking Katering via Escrow', 'pic': 'Customer & Vendor Lead', 'status': 'Selesai', 'desc': 'Kunci tanggal venue utama & booking vendor katering dengan pembayaran DP 30% terlindungi escrow.'},
        {'code': 'H-4', 'period': '4 Bulan Sebelum', 'title': 'Booking Dekorasi & Tim Dokumentasi', 'pic': 'Customer & WO', 'status': 'Dalam Proses', 'desc': 'Penentuan tema palet warna pelaminan, backdrop photobooth, dan kontrak tim fotografer/videografer.'},
        {'code': 'H-3', 'period': '3 Bulan Sebelum', 'title': 'Fitting Busana Pengantin & Kurasi Musik', 'pic': 'WO & Penata Busana', 'status': 'Belum Mulai', 'desc': 'Sesi fitting busana pengantin pertama, kurasi playlist musik akustik, dan konfirmasi MC formal.'},
        {'code': 'H-2', 'period': '2 Bulan Sebelum', 'title': 'Cetak Undangan & Rilis Undangan Digital', 'pic': 'Panitia Keluarga & WO', 'status': 'Belum Mulai', 'desc': 'Distribusi e-invitation broadcast, cetak undangan fisik VIP, pesanan souvenir, dan pembentukan panitia.'},
    ]

    weekly_targets = [
        {'code': 'W-4', 'period': 'Minggu Ke-4', 'title': 'Technical Meeting (TM) Seluruh Vendor', 'pic': 'WO & Semua Vendor', 'status': 'Belum Mulai', 'desc': 'TM gabungan di venue bersama katering, dekorasi, audio, lighting untuk finalisasi layout & alur listrik.'},
        {'code': 'W-3', 'period': 'Minggu Ke-3', 'title': 'Distribusi Undangan & Rekapitulasi RSVP', 'pic': 'Customer & Tim Digital', 'status': 'Belum Mulai', 'desc': 'Penyebaran undangan serentak dan tracking konfirmasi kehadiran tamu sebagai dasar porsi katering.'},
        {'code': 'W-2', 'period': 'Minggu Ke-2', 'title': 'Kunci Porsi Katering & Fitting Final', 'pic': 'Vendor Katering & Wardrobe', 'status': 'Belum Mulai', 'desc': 'Kunci jumlah porsi katering bersih (+ buffer 10%), fitting busana final keluarga, dan cek souvenir.'},
        {'code': 'W-1', 'period': 'Minggu Ke-1', 'title': 'Kunci jadwal hari-H & izin gedung Acara', 'pic': 'WO, MC & Keamanan', 'status': 'Belum Mulai', 'desc': 'Finalisasi rundown menit-ke-menit dengan MC & pengisi acara, izin keramaian, dan kantong parkir.'},
    ]

    daily_targets = [
        {'code': 'H-7', 'period': '7 Hari Sebelum', 'title': 'Readiness Check Komprehensif Seluruh Vendor', 'pic': 'Ketua WO & Vendor Leads', 'status': 'Belum Mulai', 'desc': 'Konfirmasi ulang jam loading barang, kedatangan personil, dan contact list PIC lapangan.'},
        {'code': 'H-6', 'period': '6 Hari Sebelum', 'title': 'Pengecekan Fisik Souvenir, Buku Tamu & Angpao', 'pic': 'Panitia Logistik Keluarga', 'status': 'Belum Mulai', 'desc': 'Pengecekan fisik souvenir bersih, amplop tip vendor, pena emas, dan gembok kotak angpao.'},
        {'code': 'H-5', 'period': '5 Hari Sebelum', 'title': 'Konfirmasi Transportasi & Tamu VIP', 'pic': 'Seksi Transportasi', 'status': 'Belum Mulai', 'desc': 'Jadwal penjemputan tamu VIP dari bandara/hotel dan mobil pengantin.'},
        {'code': 'H-4', 'period': '4 Hari Sebelum', 'title': 'Verifikasi Persiapan & Milestone Mid-Term 40%', 'pic': 'Platform Escrow & Customer', 'status': 'Belum Mulai', 'desc': 'Pengecekan bukti foto/video persiapan vendor dan persetujuan pencairan milestone kedua (40%).'},
        {'code': 'H-3', 'period': '3 Hari Sebelum', 'title': 'Finalisasi Urutan Kirab & Meja VIP', 'pic': 'WO & Keluarga', 'status': 'Belum Mulai', 'desc': 'Cetak daftar nama keluarga inti untuk prosesi foto dan penomoran meja VIP khusus.'},
        {'code': 'H-2', 'period': '2 Hari Sebelum', 'title': 'Gladi Resik Venue & Testing Audio Wireless', 'pic': 'MC, WO & Vendor Audio', 'status': 'Belum Mulai', 'desc': 'Gladi kotor di venue, uji sound system panggung, mic wireless, dan tata lampu.'},
        {'code': 'H-1', 'period': '1 Hari Sebelum', 'title': 'Loading Dekorasi, Check-in Kamar & Briefing', 'pic': 'WO & Teknisi Lapangan', 'status': 'Belum Mulai', 'desc': 'Loading in dekorasi pelaminan, check-in kamar keluarga venue, dan briefing malam panitia.'},
    ]

    rundown_items = [
        # Fase 1: Persiapan Subuh & Loading
        {'num': 1, 'phase_code': 'F1', 'phase': 'Persiapan Subuh & Loading', 'time': '04.30 - 05.30', 'duration': '60 Mnt', 'title': 'Loading Vendor Dekorasi, Lighting, Audio & Genset', 'location': 'Ballroom & Foyer Venue', 'pic': 'Tim Loading Vendor & WO Lapangan', 'audio_cue': 'Genset standby 100 kVA, ambient mic test', 'wardrobe': 'Kaos Lapangan & ID Card Panitia', 'status': 'Selesai', 'notes': 'Final inspection panggung, ambience lighting, dan instalasi kabel audio aman tertutup karpet.'},
        {'num': 2, 'phase_code': 'F1', 'phase': 'Persiapan Subuh & Loading', 'time': '05.00 - 07.00', 'duration': '120 Mnt', 'title': 'Sesi Rias Pengantin, Orang Tua & Pagar Ayu', 'location': 'Ruang Rias Pengantin / VIP', 'pic': 'Tim MUA & Asisten Wardrobe', 'audio_cue': 'Playlist santai / instrumental kamar rias', 'wardrobe': 'Kimono Rias -> Busana Akad Resmi', 'status': 'Selesai', 'notes': 'MUA standby mulai jam 05.00. Fotografer standby jam 06.00 untuk sesi candid makeup dan detail busana.'},
        {'num': 3, 'phase_code': 'F1', 'phase': 'Persiapan Subuh & Loading', 'time': '06.30 - 07.15', 'duration': '45 Mnt', 'title': 'Distribusi Sarapan Pagi Keluarga Inti & Panitia', 'location': 'Ruang Makan Transit Venue', 'pic': 'Seksi Konsumsi Keluarga & Katering', 'audio_cue': '-', 'wardrobe': 'Pakaian Transit Keluarga', 'status': 'Selesai', 'notes': '50 Pax Breakfast Box + Kopi & Teh panas siap di ruang transit agar pengantin dan keluarga bertenaga.'},
        {'num': 4, 'phase_code': 'F1', 'phase': 'Persiapan Subuh & Loading', 'time': '07.00 - 07.30', 'duration': '30 Mnt', 'title': 'Briefing Gabungan Panitia, MC & Soundcheck Final', 'location': 'Foyer Area Ballroom', 'pic': 'Ketua WO, MC & Sound Engineer', 'audio_cue': 'Soundcheck Wireless Mic 1-4, test volume 70 dB', 'wardrobe': 'Seragam Panitia & Earpiece HT', 'status': 'Selesai', 'notes': 'Penyamaan frekuensi HT, pembagian hardcopy rundown laminasi, dan sinkronisasi urutan acara dengan MC.'},

        # Fase 2: Penyambutan & Kedatangan Tamu Sakral
        {'num': 5, 'phase_code': 'F2', 'phase': 'Penyambutan & Kedatangan', 'time': '07.30 - 07.45', 'duration': '15 Mnt', 'title': 'Kedatangan Tamu VIP, Keluarga Pria & Barisan Seserahan', 'location': 'Lobby Utama & Drop-off', 'pic': 'Seksi Penerima Tamu & WO', 'audio_cue': 'Alunan Gamelan Lembut / Instrumental Tradisional', 'wardrobe': 'Beskap / Jas Seragam Keluarga Pria', 'status': 'Dalam Proses', 'notes': 'Penyambutan rombongan pengantin pria, pengkondisian barisan seserahan & keluarga pembawa baki.'},
        {'num': 6, 'phase_code': 'F2', 'phase': 'Penyambutan & Kedatangan', 'time': '07.45 - 08.00', 'duration': '15 Mnt', 'title': 'Prosesi Pengalungan Melati & Sambutan Selamat Datang', 'location': 'Pintu Masuk Ruang Akad', 'pic': 'Ibu Pengantin Wanita & MC', 'audio_cue': 'Gendhing / Instrumental Penyambutan Khidmat', 'wardrobe': 'Rangkaian Kalung Bunga Melati Asli', 'status': 'Dalam Proses', 'notes': 'Pengalungan untaian bunga melati oleh Ibu pengantin wanita kepada calon pengantin pria, dilanjutkan penyerahan seserahan simbolis.'},

        # Fase 3: Upacara Sakral Akad Nikah
        {'num': 7, 'phase_code': 'F3', 'phase': 'Upacara Sakral Akad Nikah', 'time': '08.00 - 08.15', 'duration': '15 Mnt', 'title': "Pembukaan Acara, Pembacaan Ayat Suci Al-Qur'an & Saritilawah", 'location': 'Meja Akad Panggung Utama', 'pic': 'MC Protokoler & Qari Profesional', 'audio_cue': 'Mic Qari Reverb Lembut, Suasana Hening Khidmat', 'wardrobe': 'Busana Akad Lengkap (Peci, Sorban)', 'status': 'Belum Mulai', 'notes': 'Tamu hadirin dimohon hening dan khidmat mengikuti pembacaan kalam ilahi pembuka upacara suci.'},
        {'num': 8, 'phase_code': 'F3', 'phase': 'Upacara Sakral Akad Nikah', 'time': '08.15 - 08.45', 'duration': '30 Mnt', 'title': 'Pemeriksaan Berkas KUA, Khutbah Nikah & Prosesi Ijab Qabul', 'location': 'Meja Akad Panggung Utama', 'pic': 'Penghulu KUA, Saksi & Wali Nikah', 'audio_cue': 'Standing Mic Penghulu, Wali & Pengantin Pria', 'wardrobe': 'Busana Akad Resmi + Bunga Melati Dada', 'status': 'Belum Mulai', 'notes': "Momen sakral pengucapan ijab dan qabul di hadapan penghulu dan 2 orang saksi sah, diakhiri ucapan 'Sah' serentak."},
        {'num': 9, 'phase_code': 'F3', 'phase': 'Upacara Sakral Akad Nikah', 'time': '08.45 - 09.05', 'duration': '20 Mnt', 'title': 'Doa Pernikahan, Penyerahan Mahar & Pemasangan Cincin Kawin', 'location': 'Meja Akad Panggung Utama', 'pic': 'Penghulu, WO & Dokumentasi', 'audio_cue': "Backsound Instrumental 'Barakallahu Laka' Lembut", 'wardrobe': 'Box Cincin Emas & Frame Akrilik Mahar', 'status': 'Belum Mulai', 'notes': 'Pengantin wanita dihadirkan berdampingan ke meja akad, penyerahan mahar dan penyematan cincin kawin di jari manis.'},
        {'num': 10, 'phase_code': 'F3', 'phase': 'Upacara Sakral Akad Nikah', 'time': '09.05 - 09.20', 'duration': '15 Mnt', 'title': 'Penandatanganan Buku Nikah & Penyerahan Dokumen KUA', 'location': 'Meja Akad Panggung Utama', 'pic': 'Petugas KUA & Pengantin', 'audio_cue': 'Spotlight Fokus Pengantin & Buku Nikah', 'wardrobe': 'Buku Nikah Asli & Folder Dokumen KUA', 'status': 'Belum Mulai', 'notes': "Sesi tanda tangan resmi buku nikah, pembacaan shighat ta'lik, dan penyerahan buku nikah serta kartu nikah digital."},
        {'num': 11, 'phase_code': 'F3', 'phase': 'Upacara Sakral Akad Nikah', 'time': '09.20 - 09.40', 'duration': '20 Mnt', 'title': 'Prosesi Sungkeman Haru kepada Kedua Pasang Orang Tua', 'location': 'Area Depan Meja Akad / Pelaminan', 'pic': 'MC Sungkeman & WO Lapangan', 'audio_cue': 'Instrumental Piano/Kecapi Haru Mendayu', 'wardrobe': 'Tisu Siap di Tangan WO untuk Orang Tua', 'status': 'Belum Mulai', 'notes': 'Pengantin bersujud memohon doa restu kepada ayah dan ibu. Tim WO standby tisu lembut dan memandu alur dokumentasi.'},

        # Fase 4: Dokumentasi & Transisi Resepsi
        {'num': 12, 'phase_code': 'F4', 'phase': 'Dokumentasi & Transisi', 'time': '09.40 - 10.15', 'duration': '35 Mnt', 'title': 'Sesi Foto Dokumentasi Sakral (Keluarga Inti & Saksi Nikah)', 'location': 'Panggung Pelaminan', 'pic': 'Fotografer Utama & LO Keluarga WO', 'audio_cue': 'Backsound Acoustic Instrument Ramah', 'wardrobe': 'Busana Akad Lengkap', 'status': 'Belum Mulai', 'notes': 'Sesi foto bergantian sesuai checklist: Pengantin + Orang Tua, Pengantin + Mertua, Pengantin + Saudara Kandung & Saksi KUA.'},
        {'num': 13, 'phase_code': 'F4', 'phase': 'Dokumentasi & Transisi', 'time': '10.15 - 10.45', 'duration': '30 Mnt', 'title': 'Retouch Makeup Resepsi & Penggantian Busana Pengantin', 'location': 'Ruang Rias Pengantin', 'pic': 'Tim MUA & Stylist Busana', 'audio_cue': '-', 'wardrobe': 'Gaun Resepsi Mewah / Kebaya Modern Resepsi', 'status': 'Belum Mulai', 'notes': 'Pergantian busana pengantin dan orang tua untuk sesi resepsi akbar. Re-touch riasan wajah dan pasang mahkota/headpiece.'},
        {'num': 14, 'phase_code': 'F4', 'phase': 'Dokumentasi & Transisi', 'time': '10.30 - 10.50', 'duration': '20 Mnt', 'title': 'Final Inspection Katering, Food Testing & Food Warmer Ready', 'location': 'Ballroom & Food Stall Stations', 'pic': 'Captain Katering & Koordinator Lapangan', 'audio_cue': 'Soundcheck Band Resepsi 5 Menit', 'wardrobe': 'Uniform Katering + Sarung Tangan & Masker', 'status': 'Belum Mulai', 'notes': 'Pengecekan api pemanas buffet, kelengkapan sendok piring 1.200 set, stall makanan pembuka dan es punch segar standby.'},

        # Fase 5: Pembukaan Resepsi Akbar & Kirab Pengantin
        {'num': 15, 'phase_code': 'F5', 'phase': 'Pembukaan Resepsi & Kirab', 'time': '10.45 - 11.00', 'duration': '15 Mnt', 'title': 'Registrasi Meja Tamu Dibuka & Foyer Welcome Hospitality', 'location': 'Foyer Depan Ballroom', 'pic': 'Seksi Penerima Tamu, WO & Keamanan', 'audio_cue': 'Ambient Music Welcome, Welcoming Signage', 'wardrobe': 'Seragam Pagar Ayu / Batik Penerima Tamu', 'status': 'Belum Mulai', 'notes': 'Meja registrasi siap dengan tablet e-guestbook, barcode QRIS amplop digital, pembagian souvenir, dan welcome drinks.'},
        {'num': 16, 'phase_code': 'F5', 'phase': 'Pembukaan Resepsi & Kirab', 'time': '11.00 - 11.20', 'duration': '20 Mnt', 'title': 'Opening MC Resepsi & Grand Kirab Pengantin Masuk Ballroom', 'location': 'Red Carpet s/d Pelaminan', 'pic': 'MC Resepsi, Wedding Singer & WO Kirab', 'audio_cue': "Lagu Kirab Pilihan 'Can't Help Falling in Love' / Gendhing", 'wardrobe': 'Busana Resepsi Akbar + Buket Bunga Tangan', 'status': 'Belum Mulai', 'notes': 'Pintu gerbang dibuka, lighting follow-spot menyorot barisan pagar bagus, orang tua, dan mempelai melangkah anggun ke pelaminan.'},
        {'num': 17, 'phase_code': 'F5', 'phase': 'Pembukaan Resepsi & Kirab', 'time': '11.20 - 11.35', 'duration': '15 Mnt', 'title': 'Sambutan Selamat Datang Perwakilan Keluarga & Doa Resepsi', 'location': 'Pelaminan Panggung Utama', 'pic': 'Juru Bicara Keluarga & Tokoh Agama', 'audio_cue': 'Standing Mic Pelaminan, Backsound Lembut', 'wardrobe': 'Pakaian Formal Resepsi', 'status': 'Belum Mulai', 'notes': 'Penyampaian rasa terima kasih atas kehadiran tamu undangan oleh perwakilan keluarga besar kedua mempelai, ditutup doa keberkahan.'},
        {'num': 18, 'phase_code': 'F5', 'phase': 'Pembukaan Resepsi & Kirab', 'time': '11.35 - 11.45', 'duration': '10 Mnt', 'title': 'Wedding Toast / Wedding Cake Cutting Ceremony & Suapan Kasih', 'location': 'Meja Kue Pengantin Samping Pelaminan', 'pic': 'MC Resepsi, WO & Tim Banquet', 'audio_cue': 'Lagu Romantis Pop, Pyrotechnics Cold Spark Machine', 'wardrobe': 'Pisau Kue Pita & Gelas Champagne Kristal', 'status': 'Belum Mulai', 'notes': 'Prosesi pemotongan kue pengantin bertingkat bersama, suapan kue cinta pertama, dan cold fireworks menyala indah tanpa asap.'},

        # Fase 6: Jamuan Prasmanan, Live Music & Sesi Foto
        {'num': 19, 'phase_code': 'F6', 'phase': 'Jamuan Prasmanan & Foto', 'time': '11.45 - 13.15', 'duration': '90 Mnt', 'title': 'Jamuan Prasmanan Dibuka Penuh & Hiburan Live Acoustic Band', 'location': 'Ballroom Buffet & Panggung Musik', 'pic': 'Captain Katering, Home Band & WO', 'audio_cue': 'Live Acoustic Band Playlist Pop Romance 70-75 dB', 'wardrobe': 'All Crew Standby Uniform', 'status': 'Belum Mulai', 'notes': 'Buffet utama dan seluruh stall makanan dibuka serentak. Home band mengiringi dengan alunan lagu romantis elegan.'},
        {'num': 20, 'phase_code': 'F6', 'phase': 'Jamuan Prasmanan & Foto', 'time': '12.00 - 12.45', 'duration': '45 Mnt', 'title': 'Sesi Foto Tamu VIP, Pejabat & Rekan Bisnis Keluarga', 'location': 'Panggung Pelaminan', 'pic': 'LO VIP WO, Fotografer & MC', 'audio_cue': 'Pengaturan Nomor Antrean Foto via MC Santun', 'wardrobe': 'Kamera Utama + Strobo Lighting Pelaminan', 'status': 'Belum Mulai', 'notes': 'Pengaturan antrean foto khusus tamu VVIP dan VIP dipandu LO khusus agar alur panggung tertib dan pengantin tidak kelelahan.'},
        {'num': 21, 'phase_code': 'F6', 'phase': 'Jamuan Prasmanan & Foto', 'time': '12.45 - 13.15', 'duration': '30 Mnt', 'title': 'Sesi Foto Teman Sebaya, Alumni Sekolah & Sahabat Pengantin', 'location': 'Panggung Pelaminan', 'pic': 'Fotografer & WO Panggung', 'audio_cue': 'Lagu Upbeat Ceria & Fun', 'wardrobe': 'Properti Foto Lucu / Aksesoris Photobooth', 'status': 'Belum Mulai', 'notes': 'Sesi foto santai dan interaktif bersama teman alumni kuliah, SMA, sahabat tongkrongan dan komunitas.'},

        # Fase 7: Games Interaktif, Hand Bouquet & Penutupan
        {'num': 22, 'phase_code': 'F7', 'phase': 'Games & Penutupan', 'time': '13.15 - 13.35', 'duration': '20 Mnt', 'title': 'Special Song Pengantin, Lempar Hand Bouquet & Doorprize', 'location': 'Area Tengah Ballroom', 'pic': 'MC, Tim Audio & WO', 'audio_cue': 'Lagu Drum Roll Ketegangan -> Lagu Histeris Gembira', 'wardrobe': 'Hand Bouquet Cadangan Khusus Lempar', 'status': 'Belum Mulai', 'notes': 'Momen seru lempar buket bunga untuk sahabat lajang, pemenang menerima voucher belanja / hadiah emas dari pengantin.'},
        {'num': 23, 'phase_code': 'F7', 'phase': 'Games & Penutupan', 'time': '13.35 - 14.00', 'duration': '25 Mnt', 'title': 'Closing Statement MC & Foto Bersama Seluruh Panitia / Kru WO', 'location': 'Panggung Pelaminan & FOH', 'pic': 'MC, Keluarga & Seluruh Kru WO', 'audio_cue': 'Lagu Victory Celebration Megah', 'wardrobe': 'Seluruh Panitia Berkumpul di Pelaminan', 'status': 'Belum Mulai', 'notes': 'MC mengumumkan acara telah selesai resmi, dilanjutkan foto kenangan keluarga besar bersama seluruh kru wedding organizer.'},

        # Fase 8: Teardown, Serah Terima & Rekonsiliasi Escrow
        {'num': 24, 'phase_code': 'F8', 'phase': 'Teardown & Rekonsiliasi', 'time': '14.00 - 16.30', 'duration': '150 Mnt', 'title': 'Pengamanan Kotak Angpao, Loading Out & Sign-Off Escrow', 'location': 'Ruang VIP & Loading Dock Venue', 'pic': 'Bendahara Keluarga, WO & Seluruh Vendor', 'audio_cue': '-', 'wardrobe': 'Seragam Kerja Loading Out', 'status': 'Belum Mulai', 'notes': 'Kotak angpao diamankan ke safety bag bersegel. Loading out barang vendor, sign-off BAST venue, dan rekomendasi pencairan termin 30% Escrow.'},
    ]

    if not is_wedding:
        # Generic event: no akad/kirab/sungkeman — works for corporate, seminar,
        # birthday, exhibition, intimate gathering.
        cat_label = (plan.event_category.name if plan.event_category else 'Acara')
        monthly_targets = [
            {'code': 'H-6', 'period': '6 Bulan Sebelum', 'title': 'Tentukan budget & lihat vendor', 'pic': 'Kamu & tim', 'status': 'Selesai', 'desc': f'Tentukan budget maksimal, perkiraan tamu, dan lihat vendor untuk {cat_label}.'},
            {'code': 'H-5', 'period': '5 Bulan Sebelum', 'title': 'Kunci gedung & pesan konsumsi', 'pic': 'Kamu & vendor', 'status': 'Selesai', 'desc': 'Kunci tanggal gedung & pesan konsumsi (bayar uang muka 30% yang ditahan aman).'},
            {'code': 'H-4', 'period': '4 Bulan Sebelum', 'title': 'Pesan dekorasi & dokumentasi', 'pic': 'Kamu & EO', 'status': 'Dalam Proses', 'desc': 'Tentukan tema, dekorasi panggung, dan tim foto/video.'},
            {'code': 'H-3', 'period': '3 Bulan Sebelum', 'title': 'Siapkan pengisi acara & MC', 'pic': 'EO & MC', 'status': 'Belum Mulai', 'desc': 'Pilih MC, pengisi acara/hiburan, dan susun daftar tamu.'},
            {'code': 'H-2', 'period': '2 Bulan Sebelum', 'title': 'Sebar undangan & bentuk panitia', 'pic': 'Panitia & EO', 'status': 'Belum Mulai', 'desc': 'Kirim undangan fisik + online, pesan souvenir, bentuk panitia.'},
        ]
        weekly_targets = [
            {'code': 'W-4', 'period': 'Minggu Ke-4', 'title': 'Ketemu semua vendor di gedung', 'pic': 'EO & semua vendor', 'status': 'Belum Mulai', 'desc': 'Samakan layout panggung, listrik, dan alur acara.'},
            {'code': 'W-3', 'period': 'Minggu Ke-3', 'title': 'Sebar undangan & catat yang datang', 'pic': 'Kamu & tim', 'status': 'Belum Mulai', 'desc': 'Hitung tamu yang pasti datang untuk pesan konsumsi.'},
            {'code': 'W-2', 'period': 'Minggu Ke-2', 'title': 'Kunci jumlah konsumsi & cetak materi', 'pic': 'Vendor & EO', 'status': 'Belum Mulai', 'desc': 'Kunci porsi (+ 10% cadangan), cetak backdrop, ID card, souvenir.'},
            {'code': 'W-1', 'period': 'Minggu Ke-1', 'title': 'Kunci jadwal hari-H & izin gedung', 'pic': 'EO, MC & keamanan', 'status': 'Belum Mulai', 'desc': 'Kunci susunan acara bareng MC, urus izin dan parkir.'},
        ]
        daily_targets = [
            {'code': 'H-7', 'period': '7 Hari Sebelum', 'title': 'Cek kesiapan semua vendor', 'pic': 'Ketua EO & vendor', 'status': 'Belum Mulai', 'desc': 'Pastikan jam datang barang dan personil.'},
            {'code': 'H-3', 'period': '3 Hari Sebelum', 'title': 'Cek daftar tamu VIP & tempat duduk', 'pic': 'EO & panitia', 'status': 'Belum Mulai', 'desc': 'Cetak daftar tamu VIP dan denah kursi/meja.'},
            {'code': 'H-2', 'period': '2 Hari Sebelum', 'title': 'Latihan di gedung & tes suara', 'pic': 'MC, EO & audio', 'status': 'Belum Mulai', 'desc': 'Latihan alur acara, tes mic, lampu, dan presentasi.'},
            {'code': 'H-1', 'period': '1 Hari Sebelum', 'title': 'Masukkan dekorasi & briefing', 'pic': 'EO & teknisi', 'status': 'Belum Mulai', 'desc': 'Pasang dekorasi/panggung, briefing panitia malam hari.'},
        ]
        rundown_items = [
            {'num': 1, 'phase_code': 'F1', 'phase': 'Siap-siap & pasang alat', 'time': '07.00 - 08.00', 'duration': '60 Mnt', 'title': 'Vendor masuk, pasang panggung, suara & lampu', 'location': 'Gedung acara', 'pic': 'Tim EO & vendor', 'audio_cue': 'Tes mic & musik latar', 'wardrobe': 'Kaos panitia & ID card', 'status': 'Belum Mulai', 'notes': 'Pastikan kabel aman, panggung dan backdrop berdiri kokoh.'},
            {'num': 2, 'phase_code': 'F1', 'phase': 'Siap-siap & pasang alat', 'time': '08.00 - 08.30', 'duration': '30 Mnt', 'title': 'Briefing panitia & tes akhir', 'location': 'Depan panggung', 'pic': 'Ketua EO & MC', 'audio_cue': 'Tes mic MC 1-2', 'wardrobe': 'Seragam panitia', 'status': 'Belum Mulai', 'notes': 'Bagi tugas, samakan frekuensi HT, bagi jadwal cetak.'},
            {'num': 3, 'phase_code': 'F2', 'phase': 'Tamu datang', 'time': '08.30 - 09.00', 'duration': '30 Mnt', 'title': 'Pintu dibuka, tamu registrasi & sambutan', 'location': 'Pintu masuk & meja tamu', 'pic': 'Panitia tamu', 'audio_cue': 'Musik sambutan', 'wardrobe': 'Batik panitia', 'status': 'Belum Mulai', 'notes': 'Siapkan buku tamu/tablet, souvenir, dan minuman selamat datang.'},
            {'num': 4, 'phase_code': 'F3', 'phase': 'Acara dibuka', 'time': '09.00 - 09.15', 'duration': '15 Mnt', 'title': 'MC buka acara & sambutan tuan rumah', 'location': 'Panggung utama', 'pic': 'MC & tuan rumah', 'audio_cue': 'Musik pembuka', 'wardrobe': 'Pakaian formal', 'status': 'Belum Mulai', 'notes': 'Sapa tamu, jelaskan susunan acara hari ini.'},
            {'num': 5, 'phase_code': 'F4', 'phase': 'Acara inti', 'time': '09.15 - 11.00', 'duration': '105 Mnt', 'title': 'Sesi utama (materi / sambutan / potong kue / games)', 'location': 'Panggung utama', 'pic': 'MC & pengisi acara', 'audio_cue': 'Slide + mic pembicara', 'wardrobe': '-', 'status': 'Belum Mulai', 'notes': 'Sesuaikan dengan jenismu: seminar, ultah, gathering, atau pameran.'},
            {'num': 6, 'phase_code': 'F5', 'phase': 'Istirahat & makan', 'time': '11.00 - 12.00', 'duration': '60 Mnt', 'title': 'Ishoma / makan bersama & hiburan', 'location': 'Area konsumsi & panggung', 'pic': 'Katering & MC', 'audio_cue': 'Musik santai / akustik', 'wardrobe': '-', 'status': 'Belum Mulai', 'notes': 'Buka prasmanan/stall, cek pemanas makanan dan antrean.'},
            {'num': 7, 'phase_code': 'F6', 'phase': 'Acara lanjut', 'time': '12.00 - 13.00', 'duration': '60 Mnt', 'title': 'Sesi kedua + foto bersama & doorprize', 'location': 'Panggung utama', 'pic': 'MC & fotografer', 'audio_cue': 'Musik seru', 'wardrobe': '-', 'status': 'Belum Mulai', 'notes': 'Bagi doorprize, foto per kelompok biar tertib.'},
            {'num': 8, 'phase_code': 'F7', 'phase': 'Penutupan & beres-beres', 'time': '13.00 - 14.00', 'duration': '60 Mnt', 'title': 'MC tutup acara, tamu pulang, bongkar alat', 'location': 'Gedung & parkir', 'pic': 'EO & semua vendor', 'audio_cue': '-', 'wardrobe': 'Kaos bongkar', 'status': 'Belum Mulai', 'notes': 'Amankan kotak amal/doorprize sisa, bongkar alat, serah terima gedung.'},
        ]
        logistics = [
            {'cat': 'Dokumen & Uang', 'name': 'Izin gedung & surat-surat acara', 'pic': 'Ketua panitia & EO', 'qty': '1 Set', 'status': 'Siap', 'loc': 'Tas dokumen', 'note': 'Wajib dibawa'},
            {'cat': 'Dokumen & Uang', 'name': 'Amplop honor vendor hari-H', 'pic': 'Bendahara', 'qty': '5 Amplop', 'status': 'Belum Siap', 'loc': 'Tas bendahara', 'note': 'Diberikan setelah beres'},
            {'cat': 'Tamu', 'name': 'Buku tamu / tablet registrasi', 'pic': 'Panitia tamu', 'qty': '2 Buku / 1 Tablet', 'status': 'Siap', 'loc': 'Meja tamu', 'note': 'Cek charger'},
            {'cat': 'Tamu', 'name': f'Souvenir & paperbag ({round(pax * 0.85)} pcs)', 'pic': 'Tim souvenir', 'qty': f'{round(pax * 0.85)} Pcs', 'status': 'Dalam Proses', 'loc': 'Gudang gedung', 'note': 'Pisahkan untuk VIP'},
            {'cat': 'Teknis', 'name': 'Materi presentasi & video di flashdisk', 'pic': 'Operator', 'qty': '2 Flashdisk', 'status': 'Siap', 'loc': 'Meja operator', 'note': 'Format MP4/PPT, sudah dites'},
            {'cat': 'Teknis', 'name': 'Jadwal acara cetak (10 rangkap)', 'pic': 'EO lapangan', 'qty': '10 Rangkap', 'status': 'Siap', 'loc': 'Ruang panitia', 'note': 'Dibagikan saat briefing'},
            {'cat': 'Teknis', 'name': 'Mic cadangan + baterai baru', 'pic': 'Teknisi suara', 'qty': '4 Baterai', 'status': 'Siap', 'loc': 'Meja suara', 'note': 'Baterai baru segel'},
            {'cat': 'Teknis', 'name': 'HT panitia & P3K', 'pic': 'Keamanan & medis', 'qty': '4 HT + 1 P3K', 'status': 'Siap', 'loc': 'Pos panitia', 'note': 'Frekuensi disamakan'},
        ]

    if is_wedding:
        logistics = [
        {'cat': 'Dokumen & Finansial', 'name': 'Buku Nikah / Akta Resmi & Surat Izin Keramaian', 'pic': 'Keluarga Inti & WO', 'qty': '1 Set Lengkap', 'status': 'Siap', 'loc': 'Tas Khusus Dokumen', 'note': 'Wajib dibawa saat prosesi'},
        {'cat': 'Dokumen & Finansial', 'name': 'Cincin Kawin & Box Mahar / Seserahan', 'pic': 'Pendamping Pengantin', 'qty': '1 Box Mahar', 'status': 'Siap', 'loc': 'Safety Box Hotel', 'note': 'Kunci dipegang pendamping'},
        {'cat': 'Dokumen & Finansial', 'name': 'Amplop Honor / Tip Vendor Hari-H', 'pic': 'Bendahara Keluarga', 'qty': '5 Amplop Tunai', 'status': 'Belum Siap', 'loc': 'Tas Bendahara', 'note': 'Pemberian pasca loading out'},
        {'cat': 'Dokumen & Finansial', 'name': 'Kotak Angpao & Gembok Pengaman Cadangan', 'pic': 'Seksi Logistik', 'qty': '2 Kotak + 4 Kunci', 'status': 'Siap', 'loc': 'Meja Penerima Tamu', 'note': 'Kunci diserahkan ke keluarga'},

        {'cat': 'Busana & Rias', 'name': 'Baju Pengantin Utama (Akad/Resepsi)', 'pic': 'Pengantin & MUA', 'qty': '2 Pasang Busana', 'status': 'Siap', 'loc': 'Kamar Pengantin', 'note': 'Sudah final fitting'},
        {'cat': 'Busana & Rias', 'name': 'Sepatu Pengantin & Sandal Cadangan Nyaman', 'pic': 'Pengantin', 'qty': '2 Pasang', 'status': 'Siap', 'loc': 'Kamar Ganti Venue', 'note': 'Pastikan sol sepatu anti slip'},
        {'cat': 'Busana & Rias', 'name': 'Aksesoris Busana, Dasi, Manset & Kaos Kaki', 'pic': 'Asisten Wardrobe', 'qty': '1 Set Komplit', 'status': 'Siap', 'loc': 'Koper Wardrobe', 'note': 'Cek kancing cadangan'},
        {'cat': 'Busana & Rias', 'name': 'P3K Darurat, Obat Pribadi, Plester & Parasetamol', 'pic': 'Tim Medis Keluarga', 'qty': '1 Pouch Lengkap', 'status': 'Siap', 'loc': 'Foyer Ruang Rias', 'note': 'Siapkan minyak kayu putih'},
        {'cat': 'Busana & Rias', 'name': 'Touch-up Makeup Kit & Hair Spray Cadangan', 'pic': 'Tim MUA', 'qty': '1 Pouch Rias', 'status': 'Siap', 'loc': 'Backstage', 'note': 'Standby selama sesi kirab'},

        {'cat': 'Resepsi & Tamu', 'name': 'Buku Tamu / E-Guestbook Tablet Scanner', 'pic': 'Seksi Penerima Tamu', 'qty': '4 Buku / 2 Tablet', 'status': 'Siap', 'loc': 'Foyer Ballroom', 'note': 'Uji koneksi charger tablet'},
        {'cat': 'Resepsi & Tamu', 'name': 'Pulpen Emas & Spidol Tanda Tangan', 'pic': 'Seksi Penerima Tamu', 'qty': '10 Buah', 'status': 'Siap', 'loc': 'Meja Registrasi', 'note': 'Cek tinta tidak macet'},
        {'cat': 'Resepsi & Tamu', 'name': 'Souvenir Tamu & Paperbag Cadangan', 'pic': 'Tim Souvenir WO', 'qty': f'{round(pax * 0.85)} Pcs', 'status': 'Dalam Proses', 'loc': 'Gudang Transit Venue', 'note': 'Sortir sesuai kategori VIP'},
        {'cat': 'Resepsi & Tamu', 'name': 'Nomor Meja VIP & Signage Meja Keluarga', 'pic': 'Tim Dekorasi', 'qty': '15 Akrilik Meja', 'status': 'Siap', 'loc': 'Meja Bundar VIP', 'note': 'Pasang nama keluarga'},
        {'cat': 'Resepsi & Tamu', 'name': 'Stand Barcode QRIS / Rekening Amplop Digital', 'pic': 'Panitia Finansial', 'qty': '2 Akrilik Stand', 'status': 'Siap', 'loc': 'Meja Buku Tamu', 'note': 'Uji scan barcode aktif'},

        {'cat': 'Teknis & Multimedia', 'name': 'Flashdisk Master Video Slideshow & Foto Prewedding', 'pic': 'Operator Multimedia', 'qty': '2 Flashdisk (Backup)', 'status': 'Siap', 'loc': 'Meja FOH Audio Video', 'note': 'Format MP4 1080p tested'},
        {'cat': 'Teknis & Multimedia', 'name': 'Flashdisk Lagu Kirab & Backsound Playlist', 'pic': 'Operator Musik & Band', 'qty': '2 Flashdisk USB', 'status': 'Siap', 'loc': 'Sound Console', 'note': 'Urutan lagu kirab teruji'},
        {'cat': 'Teknis & Multimedia', 'name': 'Hardcopy Master Rundown Acara Lengkap', 'pic': 'Koordinator Lapangan WO', 'qty': '10 Rangkap Laminasi', 'status': 'Siap', 'loc': 'Ruang Briefing Panitia', 'note': 'Dibagikan saat briefing pagi'},
        {'cat': 'Teknis & Multimedia', 'name': 'Baterai Cadangan Wireless Mic (AA/9V)', 'pic': 'Teknisi Sound System', 'qty': '8 Pasang Baterai Baru', 'status': 'Siap', 'loc': 'FOH Sound Engineer', 'note': 'Baterai baru segel'},
        {'cat': 'Teknis & Multimedia', 'name': 'Lakban Hitam, Gunting, Cutter & Kabel Rol', 'pic': 'Seksi Perlengkapan', 'qty': '1 Toolkit Lengkap', 'status': 'Siap', 'loc': 'Gudang Logistik WO', 'note': 'Peralatan serba guna'},
        {'cat': 'Teknis & Multimedia', 'name': 'Handy Talky (HT) & Earpiece Panitia', 'pic': 'Seksi Keamanan & WO', 'qty': '8 Unit Terisi Penuh', 'status': 'Dalam Proses', 'loc': 'Sekretariat Panitia', 'note': 'Frekuensi disamakan'},
    ]

    realisasi_total = round(pagu * 0.93)
    variance = round(pagu - realisasi_total)
    serapan_pct = round((realisasi_total / pagu) * 100, 1) if pagu else 0
    dana_terbayar = round(realisasi_total * 0.30)
    sisa_kewajiban = realisasi_total - dana_terbayar

    financial_breakdown = [
        {'name': 'Catering & Jamuan Tamu', 'pct': 40, 'plan': round(pagu * 0.40), 'actual': total_food_cost, 'vendor': 'Nusantara Royal Catering', 'status': 'DP 30% Terbayar', 'dp': round(total_food_cost*0.3), 'mid': round(total_food_cost*0.4), 'fin': round(total_food_cost*0.3), 'paid': round(total_food_cost*0.3), 'debt': round(total_food_cost*0.7)},
        {'name': 'Dekorasi, Pelaminan & Venue', 'pct': 30, 'plan': round(pagu * 0.30), 'actual': round(pagu * 0.30), 'vendor': 'Kencana Art Decoration', 'status': 'Menunggu Konfirmasi', 'dp': round(pagu*0.30*0.3), 'mid': round(pagu*0.30*0.4), 'fin': round(pagu*0.30*0.3), 'paid': 0, 'debt': round(pagu*0.30)},
        {'name': 'Dokumentasi (Foto & Video)', 'pct': 12, 'plan': round(pagu * 0.12), 'actual': round(pagu * 0.12), 'vendor': 'Lumina Visuals Studio', 'status': 'Quotation Diterima', 'dp': round(pagu*0.12*0.3), 'mid': round(pagu*0.12*0.4), 'fin': round(pagu*0.12*0.3), 'paid': 0, 'debt': round(pagu*0.12)},
        {'name': 'Sound System, Lighting & MC', 'pct': 13, 'plan': round(pagu * 0.13), 'actual': round(pagu * 0.13), 'vendor': 'SoundVibe Pro Audio', 'status': 'Rekomendasi', 'dp': round(pagu*0.13*0.3), 'mid': round(pagu*0.13*0.4), 'fin': round(pagu*0.13*0.3), 'paid': 0, 'debt': round(pagu*0.13)},
        {'name': 'Dana Cadangan Tak Terduga (5%)', 'pct': 5, 'plan': round(pagu * 0.05), 'actual': 0, 'vendor': 'Alokasi Cadangan Mandiri', 'status': 'Belum Bayar', 'dp': 0, 'mid': 0, 'fin': 0, 'paid': 0, 'debt': 0},
    ]

    return {
        'days_left': max(days_left, 0),
        'pax': pax,
        'pagu_max': pagu,
        'realisasi_total': realisasi_total,
        'variance': variance,
        'serapan_pct': serapan_pct,
        'cost_per_pax': round(realisasi_total / total_porsi) if total_porsi else 0,
        'dana_terbayar': dana_terbayar,
        'sisa_kewajiban': sisa_kewajiban,
        'financial_breakdown': financial_breakdown,
        'catering': {
            'phys_inv': phys_inv,
            'dig_inv': dig_inv,
            'tamu_calc': tamu_calc,
            'buffer_pax': buffer_pax,
            'total_porsi': total_porsi,
            'buffet_portions': buffet_portions,
            'stall_portions': stall_portions,
            'buffet_price': buffet_price,
            'stall_price': stall_price,
            'subtotal_buffet': subtotal_buffet,
            'subtotal_stall': subtotal_stall,
            'total_food_cost': total_food_cost,
            'food_cost_per_pax': food_cost_per_pax,
            'facilities': facilities,
            'scenarios': scenarios,
        },
        'timeline': {
            'monthly': monthly_targets,
            'weekly': weekly_targets,
            'daily': daily_targets,
            'rundown': rundown_items,
        },
        'logistics': logistics,
    }


def generate_planner_excel(plan, vendors, budget_allocations, vendor_mode='full'):
    """vendor_mode:
    - 'full': lengkap (nama vendor, harga, kontak PIC) — ekspor personal dari sistem.
    - 'basic': template berbayar — list vendor (nama, kategori, kota, rating)
      TANPA harga/paket/kontak. Detail, spek & pencocokan budget hanya di aplikasi.
    - 'none': template gratis kosongan — tanpa data vendor sama sekali.
    """
    """
    Generates a world-class, fully formula-driven master event workbook with 5 distinct tabs:
    1. Budget & Bayar (Executive KPI cards, live formulas, automated variance, escrow cashflow & debt tracking)
    2. Direktori Vendor & PIC (Unmasked contacts, WhatsApp links, cost-per-pax formulas & status dropdowns)
    3. Jadwal & Rundown (Live TODAY() countdown, readiness counters, Bulanan, Mingguan, Harian & Hari-H Rundown)
    4. Hitung Katering (Interactive guest attendance simulator, buffet vs stall ratios, logistics & sensitivity analysis)
    5. Daftar Barang (Master equipment checklist, readiness KPI counter & storage/PIC tracking)
    """
    wb = openpyxl.Workbook()

    # Brand Colors
    navy_fill = PatternFill(start_color="1B1F3B", end_color="1B1F3B", fill_type="solid")
    gold_fill = PatternFill(start_color="D9A441", end_color="D9A441", fill_type="solid")
    berry_fill = PatternFill(start_color="B23A5D", end_color="B23A5D", fill_type="solid")
    soft_gray = PatternFill(start_color="F8FAF6", end_color="F8FAF6", fill_type="solid")
    kpi_card_fill = PatternFill(start_color="F5EFE0", end_color="F5EFE0", fill_type="solid")
    input_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    accent_green = PatternFill(start_color="D1E7DD", end_color="D1E7DD", fill_type="solid")
    accent_red = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
    accent_yellow = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")

    font_white_title = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    font_white_bold = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_kpi_label = Font(name="Calibri", size=9, bold=True, color="4B4F72")
    font_kpi_val = Font(name="Calibri", size=15, bold=True, color="1B1F3B")
    font_bold = Font(name="Calibri", size=10, bold=True, color="1B1F3B")
    font_regular = Font(name="Calibri", size=10, color="1B1F3B")
    font_sub = Font(name="Calibri", size=9, italic=True, color="4B4F72")

    cf_green_font = Font(color="0F5132", bold=True)
    cf_red_font = Font(color="842029", bold=True)
    cf_yellow_font = Font(color="664D03", bold=True)

    thin_border = Border(
        left=Side(style='thin', color='D0D5DD'),
        right=Side(style='thin', color='D0D5DD'),
        top=Side(style='thin', color='D0D5DD'),
        bottom=Side(style='thin', color='D0D5DD')
    )

    # -------------------------------------------------------------
    # TAB 1: Budget & Bayar (Master Financial Control)
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Budget & Bayar"
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner
    ws1.merge_cells("A1:N1")
    ws1["A1"] = f"VENDORAMAN - MASTER FINANCIAL & BUDGET PLANNER: {plan.title.upper()}"
    ws1["A1"].font = font_white_title
    ws1["A1"].fill = navy_fill
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    # User Guide / Color Legend
    ws1.cell(row=2, column=1, value="LEGENDA:").font = font_bold
    ws1.merge_cells("B2:D2")
    ws1["B2"] = "KOLOM KUNING = INPUT EDITABLE (Bisa Diubah)"
    ws1["B2"].font = Font(name="Calibri", size=9, bold=True, color="856404")
    ws1["B2"].fill = input_fill
    ws1["B2"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("E2:G2")
    ws1["E2"] = "KOLOM HIJAU/PUTIH = FORMULA OTOMATIS"
    ws1["E2"].font = Font(name="Calibri", size=9, bold=True, color="0F5132")
    ws1["E2"].fill = accent_green
    ws1["E2"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("H2:K2")
    ws1["H2"] = "STATUS PEMBAYARAN = KLIK DROPDOWN UNTUK MENGUBAH"
    ws1["H2"].font = Font(name="Calibri", size=9, bold=True, color="1B1F3B")
    ws1["H2"].fill = kpi_card_fill
    ws1["H2"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20

    # 7 Executive KPI Cards (Row 4-6)
    # Card 1: Pagu Anggaran
    ws1.merge_cells("A4:B4")
    ws1["A4"] = "BATAS BUDGET MAKSIMAL"
    ws1["A4"].font = font_kpi_label
    ws1["A4"].fill = kpi_card_fill
    ws1["A4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("A5:B6")
    ws1["A5"] = float(plan.budget_max)
    ws1["A5"].number_format = '"Rp " #,##0'
    ws1["A5"].font = font_kpi_val
    ws1["A5"].fill = kpi_card_fill
    ws1["A5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 2: Total Realisasi
    ws1.merge_cells("C4:D4")
    ws1["C4"] = "PERKIRAAN TOTAL BELANJA"
    ws1["C4"].font = font_kpi_label
    ws1["C4"].fill = soft_gray
    ws1["C4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("C5:D6")
    ws1["C5"] = "=SUM(F15:F19)"
    ws1["C5"].number_format = '"Rp " #,##0'
    ws1["C5"].font = font_kpi_val
    ws1["C5"].fill = soft_gray
    ws1["C5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 3: Sisa Saldo (Variance)
    ws1.merge_cells("E4:F4")
    ws1["E4"] = "SISA UANG KAMU"
    ws1["E4"].font = font_kpi_label
    ws1["E4"].fill = accent_green
    ws1["E4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("E5:F6")
    ws1["E5"] = "=A5-C5"
    ws1["E5"].number_format = '"Rp " #,##0'
    ws1["E5"].font = font_kpi_val
    ws1["E5"].fill = accent_green
    ws1["E5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 4: Serapan Anggaran (%)
    ws1.merge_cells("G4:H4")
    ws1["G4"] = "BUDGET TERPAKAI (%)"
    ws1["G4"].font = font_kpi_label
    ws1["G4"].fill = soft_gray
    ws1["G4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("G5:H6")
    ws1["G5"] = "=C5/A5"
    ws1["G5"].number_format = '0.0%'
    ws1["G5"].font = font_kpi_val
    ws1["G5"].fill = soft_gray
    ws1["G5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 5: Biaya per Tamu (Cost/Pax)
    ws1.merge_cells("I4:J4")
    ws1["I4"] = "BIAYA PER TAMU"
    ws1["I4"].font = font_kpi_label
    ws1["I4"].fill = kpi_card_fill
    ws1["I4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("I5:J6")
    ws1["I5"] = "=ROUND(C5/'Hitung Katering'!$B$12, 0)"
    ws1["I5"].number_format = '"Rp " #,##0'
    ws1["I5"].font = font_kpi_val
    ws1["I5"].fill = kpi_card_fill
    ws1["I5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 6: Total Dana Terbayar Escrow
    ws1.merge_cells("K4:L4")
    ws1["K4"] = "SUDAH DIBAYAR"
    ws1["K4"].font = font_kpi_label
    ws1["K4"].fill = accent_green
    ws1["K4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("K5:L6")
    ws1["K5"] = "=SUM(M15:M19)"
    ws1["K5"].number_format = '"Rp " #,##0'
    ws1["K5"].font = font_kpi_val
    ws1["K5"].fill = accent_green
    ws1["K5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 7: Sisa Kewajiban Hutang
    ws1.merge_cells("M4:N4")
    ws1["M4"] = "SISA YANG BELUM DIBAYAR"
    ws1["M4"].font = font_kpi_label
    ws1["M4"].fill = soft_gray
    ws1["M4"].alignment = Alignment(horizontal="center", vertical="center")

    ws1.merge_cells("M5:N6")
    ws1["M5"] = "=C5-K5"
    ws1["M5"].number_format = '"Rp " #,##0'
    ws1["M5"].font = font_kpi_val
    ws1["M5"].fill = soft_gray
    ws1["M5"].alignment = Alignment(horizontal="center", vertical="center")

    for r in range(4, 7):
        for c in range(1, 15):
            ws1.cell(row=r, column=c).border = thin_border

    # Event Metadata (Rows 8-10). B9 is a real date value (Dashboard + countdown use it),
    # and Anggaran Max mirrors the KPI card (=A5) so edits flow everywhere.
    meta_info = [
        ("Kategori Acara", plan.event_category.name if plan.event_category else "Event", "Kota / Lokasi", plan.city, "Status Kurasi", "Vetted Partners Only", "Proteksi", "Garansi Finansial 100%"),
        ("Tanggal Acara", plan.event_date, "Estimasi Tamu", f"{plan.estimated_pax} Pax", "Skema Pembayaran", "Platform Escrow Bertahap", "Metode", "Virtual Account & QRIS"),
        ("Anggaran Min", f"Rp {intdot(plan.budget_min)}", "Anggaran Max", "=A5", "Sistem Escrow", "Tiga Tahap (30-40-30)", "Layanan", "Dedicated Event Planner"),
    ]
    for r_idx, row_data in enumerate(meta_info, start=8):
        for c_pair in range(4):
            lbl = row_data[c_pair*2]
            val = row_data[c_pair*2 + 1]
            col_lbl = c_pair*3 + 1
            col_val = col_lbl + 1
            ws1.cell(row=r_idx, column=col_lbl, value=lbl).font = font_bold
            c_val = ws1.cell(row=r_idx, column=col_val, value=val)
            c_val.font = font_regular
            if r_idx == 9 and c_pair == 0 and hasattr(val, 'strftime'):
                c_val.number_format = 'DD MMMM YYYY'
            if r_idx == 10 and c_pair == 1:
                c_val.number_format = '"Rp " #,##0'

    # Master Table Header (Row 14)
    headers1 = [
        "No.", "Kategori Pengeluaran", "Alokasi Target (%)", "Target Anggaran (Rp)",
        "Vendor Rekomendasi / Terpilih", "Realisasi Kontrak (Rp)", "Selisih / Variance (Rp)",
        "Status Efisiensi", "DP 30% (Rp)", "Mid-Term 40% (Rp)", "Pelunasan 30% (Rp)", "Status Pembayaran",
        "Dana Terbayar (Rp)", "Sisa Kewajiban (Rp)"
    ]
    header_row1 = 14
    for col_idx, h_text in enumerate(headers1, start=1):
        cell = ws1.cell(row=header_row1, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws1.row_dimensions[header_row1].height = 28

    total_max = float(plan.budget_max)
    _vlabel = "—" if vendor_mode in ('basic', 'none') else None
    rows_data1 = [
        (1, "Catering & Jamuan Tamu", 0.40, "='Hitung Katering'!B34", _vlabel or "Nusantara Royal Catering", "DP 30% Terbayar"),
        (2, "Dekorasi, Pelaminan & Venue", 0.30, total_max * 0.30, _vlabel or "Kencana Art Decoration", "Menunggu Konfirmasi"),
        (3, "Dokumentasi (Foto & Cinematic Video)", 0.12, total_max * 0.12, _vlabel or "Lumina Visuals Studio", "Quotation Diterima"),
        (4, "Sound System, Lighting, MC & Hiburan", 0.13, total_max * 0.13, _vlabel or "SoundVibe Pro Audio", "Rekomendasi"),
        (5, "Dana Cadangan Tak Terduga (Contingency)", 0.05, 0, "Alokasi Cadangan Mandiri", "Belum Bayar"),
    ]

    curr_row = 15
    for item in rows_data1:
        ws1.cell(row=curr_row, column=1, value=item[0]).alignment = Alignment(horizontal="center")
        ws1.cell(row=curr_row, column=2, value=item[1]).font = font_bold if item[0] == 5 else font_regular
        
        # Col 3: Target %
        c_pct = ws1.cell(row=curr_row, column=3, value=item[2])
        c_pct.number_format = '0.0%'
        c_pct.alignment = Alignment(horizontal="center")
        
        # Col 4: Target Anggaran = $A$5 * C{row}
        c_plan = ws1.cell(row=curr_row, column=4, value=f"=$A$5*C{curr_row}")
        c_plan.number_format = '#,##0'
        
        # Col 5: Vendor Terpilih
        ws1.cell(row=curr_row, column=5, value=item[4]).font = font_regular
        
        # Col 6: Realisasi Kontrak (Rp) -> user editable, highlighted
        c_act = ws1.cell(row=curr_row, column=6, value=item[3])
        c_act.number_format = '#,##0'
        c_act.fill = input_fill
        c_act.font = font_bold
        
        # Col 7: Selisih / Variance formula: Target - Realisasi (Positive = Surplus, Negative = Defisit)
        c_var = ws1.cell(row=curr_row, column=7, value=f"=D{curr_row}-F{curr_row}")
        c_var.number_format = '#,##0'
        c_var.font = font_bold
        
        # Col 8: Status Efisiensi formula
        c_stat = ws1.cell(row=curr_row, column=8, value=f'=IF(F{curr_row}=0,"Belum Realisasi",IF(G{curr_row}>0,"HEMAT " & TEXT(G{curr_row},"#,##0"),IF(G{curr_row}<0,"DEFISIT " & TEXT(ABS(G{curr_row}),"#,##0"),"SESUAI")))')
        c_stat.alignment = Alignment(horizontal="center")
        c_stat.font = font_bold
        
        # Col 9: DP 30% formula
        c_dp = ws1.cell(row=curr_row, column=9, value=f"=ROUND(F{curr_row}*0.3, 0)")
        c_dp.number_format = '#,##0'
        
        # Col 10: Mid-Term 40% formula
        c_mid = ws1.cell(row=curr_row, column=10, value=f"=ROUND(F{curr_row}*0.4, 0)")
        c_mid.number_format = '#,##0'
        
        # Col 11: Pelunasan 30% formula
        c_fin = ws1.cell(row=curr_row, column=11, value=f"=ROUND(F{curr_row}*0.3, 0)")
        c_fin.number_format = '#,##0'
        
        # Col 12: Status Pembayaran (Dropdown)
        c_pay = ws1.cell(row=curr_row, column=12, value=item[5])
        c_pay.alignment = Alignment(horizontal="center")
        
        # Col 13: Dana Terbayar Otomatis (Live Escrow Outflow formula)
        c_paid = ws1.cell(row=curr_row, column=13, value=f'=IF(L{curr_row}="Lunas",F{curr_row},IF(L{curr_row}="Mid-Term 40% Terbayar",I{curr_row}+J{curr_row},IF(L{curr_row}="DP 30% Terbayar",I{curr_row},0)))')
        c_paid.number_format = '#,##0'
        c_paid.font = font_bold
        
        # Col 14: Sisa Kewajiban Hutang = Realisasi - Dana Terbayar
        c_debt = ws1.cell(row=curr_row, column=14, value=f"=F{curr_row}-M{curr_row}")
        c_debt.number_format = '#,##0'
        c_debt.font = font_bold
        
        for c in range(1, 15):
            ws1.cell(row=curr_row, column=c).border = thin_border
        curr_row += 1

    # Total Summary Row (Row 20)
    ws1.cell(row=curr_row, column=1, value="").alignment = Alignment(horizontal="center")
    ws1.cell(row=curr_row, column=2, value="TOTAL KESELURUHAN").font = font_bold
    ws1.cell(row=curr_row, column=3, value="=SUM(C15:C19)").number_format = '0.0%'
    ws1.cell(row=curr_row, column=4, value="=SUM(D15:D19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=5, value="5 Divisi Master")
    ws1.cell(row=curr_row, column=6, value="=SUM(F15:F19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=7, value="=SUM(G15:G19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=8, value='=IF(G20>0,"TOTAL SURPLUS",IF(G20<0,"TOTAL DEFISIT","SEIMBANG"))').alignment = Alignment(horizontal="center")
    ws1.cell(row=curr_row, column=9, value="=SUM(I15:I19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=10, value="=SUM(J15:J19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=11, value="=SUM(K15:K19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=12, value="Rekap Escrow").alignment = Alignment(horizontal="center")
    ws1.cell(row=curr_row, column=13, value="=SUM(M15:M19)").number_format = '#,##0'
    ws1.cell(row=curr_row, column=14, value="=SUM(N15:N19)").number_format = '#,##0'

    for c in range(1, 15):
        cell = ws1.cell(row=curr_row, column=c)
        cell.font = font_bold
        cell.fill = soft_gray
        cell.border = thin_border

    # Data Validation Dropdown for Status Pembayaran
    dv_pay = DataValidation(type="list", formula1='"Belum Bayar,DP 30% Terbayar,Mid-Term 40% Terbayar,Lunas"', allow_blank=True)
    ws1.add_data_validation(dv_pay)
    dv_pay.add("L15:L19")

    # Conditional formatting for Selisih (Col G) & Status Pembayaran (Col L)
    ws1.conditional_formatting.add("G15:G20", CellIsRule(operator="greaterThan", formula=["0"], fill=accent_green, font=cf_green_font))
    ws1.conditional_formatting.add("G15:G20", CellIsRule(operator="lessThan", formula=["0"], fill=accent_red, font=cf_red_font))
    ws1.conditional_formatting.add("L15:L19", CellIsRule(operator="equal", formula=['"Lunas"'], fill=accent_green, font=cf_green_font))
    ws1.conditional_formatting.add("L15:L19", CellIsRule(operator="equal", formula=['"DP 30% Terbayar"'], fill=accent_yellow, font=cf_yellow_font))
    ws1.conditional_formatting.add("L15:L19", CellIsRule(operator="equal", formula=['"Mid-Term 40% Terbayar"'], fill=accent_yellow, font=cf_yellow_font))

    # Notes & Guidance below
    note_row = curr_row + 2
    ws1.cell(row=note_row, column=2, value="* Panduan Finansial: Kolom berlatar kuning (Realisasi Kontrak) dapat Anda sesuaikan. Biaya katering terhubung otomatis ke Tab 'Hitung Katering'. Selisih, status efisiensi, dan dana terbayar escrow terupdate otomatis.").font = font_sub
    ws1.freeze_panes = 'A15'

    # -------------------------------------------------------------
    # TAB 2: Direktori Vendor & PIC (Procurement Matrix)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Direktori Vendor & PIC")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:N1")
    ws2["A1"] = "DIREKTORI RESMI VENDOR TERKURASI & KONTAK PIC (PAID PLANNER UNLOCKED)"
    ws2["A1"].font = font_white_title
    ws2["A1"].fill = navy_fill
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 36

    v_count = len(vendors) if vendors else 4
    v_end_row = max(6 + v_count, 7)

    # Summary KPI Cards at Top of Tab 2 (Rows 3-4)
    ws2.merge_cells("A3:C3")
    ws2["A3"] = "TOTAL VENDOR TERKURASI"
    ws2["A3"].font = font_kpi_label
    ws2["A3"].fill = kpi_card_fill
    ws2["A3"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("A4:C4")
    ws2["A4"] = f"=COUNTA(C7:C{v_end_row})"
    ws2["A4"].font = font_kpi_val
    ws2["A4"].fill = kpi_card_fill
    ws2["A4"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("D3:F3")
    ws2["D3"] = "VENDOR SUDAH BOOKING"
    ws2["D3"].font = font_kpi_label
    ws2["D3"].fill = accent_green
    ws2["D3"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("D4:F4")
    ws2["D4"] = f'=COUNTIF(L7:L{v_end_row}, "Sudah Booking")'
    ws2["D4"].font = font_kpi_val
    ws2["D4"].fill = accent_green
    ws2["D4"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("G3:I3")
    ws2["G3"] = "VENDOR DALAM DISKUSI"
    ws2["G3"].font = font_kpi_label
    ws2["G3"].fill = accent_yellow
    ws2["G3"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("G4:I4")
    ws2["G4"] = f'=COUNTIF(L7:L{v_end_row}, "Dalam Diskusi")'
    ws2["G4"].font = font_kpi_val
    ws2["G4"].fill = accent_yellow
    ws2["G4"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("J3:N3")
    ws2["J3"] = "TOTAL NILAI KONTRAK VENDOR TERPILIH"
    ws2["J3"].font = font_kpi_label
    ws2["J3"].fill = soft_gray
    ws2["J3"].alignment = Alignment(horizontal="center")

    ws2.merge_cells("J4:N4")
    ws2["J4"] = f'=SUMIF(L7:L{v_end_row}, "Sudah Booking", K7:K{v_end_row})'
    ws2["J4"].number_format = '"Rp " #,##0'
    ws2["J4"].font = font_kpi_val
    ws2["J4"].fill = soft_gray
    ws2["J4"].alignment = Alignment(horizontal="center")

    for r in range(3, 5):
        for c in range(1, 15):
            ws2.cell(row=r, column=c).border = thin_border

    headers2 = [
        "No.", "Kategori", "Nama Vendor Resmi", "Kota", "Rating", "Event Selesai",
        "Nama PIC", "Kontak WhatsApp PIC", "Paket Utama", "Kapasitas Pax", "Harga Paket (Rp)", "Status Tindak Lanjut",
        "Estimasi Biaya/Pax", "Catatan Negosiasi & Termin"
    ]
    for col_idx, h_text in enumerate(headers2, start=1):
        cell = ws2.cell(row=6, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws2.row_dimensions[6].height = 26

    v_row = 7
    for idx, vendor in enumerate(vendors, start=1):
        ws2.cell(row=v_row, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws2.cell(row=v_row, column=2, value=vendor.category.name if vendor.category else "Umum").font = font_regular
        ws2.cell(row=v_row, column=3, value=vendor.business_name).font = font_bold
        ws2.cell(row=v_row, column=4, value=vendor.city).font = font_regular

        c_rating = ws2.cell(row=v_row, column=5, value=float(vendor.rating))
        c_rating.alignment = Alignment(horizontal="center")
        c_rating.number_format = '0.0 "★"'

        c_events = ws2.cell(row=v_row, column=6, value=vendor.total_completed_events)
        c_events.alignment = Alignment(horizontal="center")
        c_events.number_format = '#,##0'

        if vendor_mode == 'basic':
            # Template berbayar: list vendor saja — TANPA harga/paket/kontak.
            # Detail, spek & pencocokan budget hanya ada di aplikasi.
            _note = "Lihat di aplikasi"
            ws2.cell(row=v_row, column=7, value=_note).font = font_sub
            ws2.cell(row=v_row, column=8, value=_note).font = font_sub
            ws2.cell(row=v_row, column=9, value=_note).font = font_sub
            c_pax = ws2.cell(row=v_row, column=10, value=_note)
            c_pax.alignment = Alignment(horizontal="center")
            c_price = ws2.cell(row=v_row, column=11, value=_note)
            c_price.font = font_bold
            c_price.alignment = Alignment(horizontal="center")
            c_followup = ws2.cell(row=v_row, column=12, value="Belum Dihubungi")
            c_followup.alignment = Alignment(horizontal="center")
            c_per_pax = ws2.cell(row=v_row, column=13, value=_note)
            c_per_pax.alignment = Alignment(horizontal="center")
            ws2.cell(row=v_row, column=14, value="Pilih sendiri & hubungi vendor langsung").font = font_regular
            for c in range(1, 15):
                ws2.cell(row=v_row, column=c).border = thin_border
            v_row += 1
            continue

        pkg = vendor.packages.first()
        ws2.cell(row=v_row, column=7, value=vendor.pic_name).font = font_regular
        
        clean_phone = "".join(filter(str.isdigit, vendor.contact_phone))
        if clean_phone.startswith("0"):
            clean_phone = "62" + clean_phone[1:]
        c_phone = ws2.cell(row=v_row, column=8, value=vendor.contact_phone)
        c_phone.hyperlink = f"https://wa.me/{clean_phone}"
        c_phone.font = Font(name="Calibri", size=10, color="0000EE", underline="single")
        c_phone.alignment = Alignment(horizontal="center")
        
        ws2.cell(row=v_row, column=9, value=pkg.name if pkg else "Custom Package").font = font_regular
        
        c_pax = ws2.cell(row=v_row, column=10, value=pkg.pax_capacity if pkg else plan.estimated_pax)
        c_pax.alignment = Alignment(horizontal="center")
        c_pax.number_format = '#,##0'

        c_price = ws2.cell(row=v_row, column=11, value=float(pkg.price) if pkg else 0)
        c_price.number_format = '"Rp " #,##0'
        c_price.font = font_bold

        c_followup = ws2.cell(row=v_row, column=12, value="Sudah Booking" if idx == 1 else "Dalam Diskusi" if idx == 2 else "Belum Dihubungi")
        c_followup.alignment = Alignment(horizontal="center")

        c_per_pax = ws2.cell(row=v_row, column=13, value=f"=IF(J{v_row}>0, ROUND(K{v_row}/J{v_row}, 0), 0)")
        c_per_pax.number_format = '"Rp " #,##0'
        c_per_pax.alignment = Alignment(horizontal="right")

        ws2.cell(row=v_row, column=14, value="Negosiasi paket bonus & jadwal loading").font = font_regular

        for c in range(1, 15):
            ws2.cell(row=v_row, column=c).border = thin_border
        v_row += 1

    dv_vendor = DataValidation(type="list", formula1='"Belum Dihubungi,Dalam Diskusi,Sudah Booking,Ditolak"', allow_blank=True)
    ws2.add_data_validation(dv_vendor)
    if v_row > 7:
        dv_vendor.add(f"L7:L{v_row-1}")

        ws2.conditional_formatting.add(f"L7:L{v_row-1}", CellIsRule(operator="equal", formula=['"Sudah Booking"'], fill=accent_green, font=cf_green_font))
        ws2.conditional_formatting.add(f"L7:L{v_row-1}", CellIsRule(operator="equal", formula=['"Dalam Diskusi"'], fill=accent_yellow, font=cf_yellow_font))
        ws2.conditional_formatting.add(f"L7:L{v_row-1}", CellIsRule(operator="equal", formula=['"Ditolak"'], fill=accent_red, font=cf_red_font))

    ws2.freeze_panes = 'A7'

    # -------------------------------------------------------------
    # TAB 3: Jadwal & Rundown (Mission Control & Countdown)
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="Jadwal & Rundown")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:J1")
    ws3["A1"] = "JADWAL PERSIAPAN & ACARA HARI-H"
    ws3["A1"].font = font_white_title
    ws3["A1"].fill = navy_fill
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 36

    planner_master = get_planner_master_data(plan)
    _md = planner_master['timeline']['monthly']
    _wd = planner_master['timeline']['weekly']
    _dd = planner_master['timeline']['daily']
    _n_m, _n_w, _n_d = len(_md), len(_wd), len(_dd)
    # Layout: section title row, header row, then data rows; one blank row between sections.
    _m_start, _m_end = 10, 10 + _n_m - 1
    _w_head = _m_end + 4
    _w_start, _w_end = _w_head + 2, _w_head + 2 + _n_w - 1
    _d_head = _w_end + 4
    _d_start, _d_end = _d_head + 2, _d_head + 2 + _n_d - 1

    # Top Readiness & Countdown Dashboard (Rows 3-5)
    # Card 1: Live Countdown Hari
    ws3.merge_cells("A3:B4")
    ws3["A3"] = "HITUNG MUNDUR (HARI LAGI)"
    ws3["A3"].font = font_kpi_label
    ws3["A3"].fill = kpi_card_fill
    ws3["A3"].alignment = Alignment(horizontal="center", vertical="center")

    ws3.merge_cells("A5:B5")
    ws3["A5"] = "='Budget & Bayar'!B9-TODAY()"
    ws3["A5"].font = font_kpi_val
    ws3["A5"].number_format = '#,##0" HARI LAGI"'
    ws3["A5"].fill = kpi_card_fill
    ws3["A5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 2: Total Target Operasional
    ws3.merge_cells("C3:D4")
    ws3["C3"] = "TOTAL YANG HARUS DIKERJAKAN"
    ws3["C3"].font = font_kpi_label
    ws3["C3"].fill = soft_gray
    ws3["C3"].alignment = Alignment(horizontal="center", vertical="center")

    ws3.merge_cells("C5:D5")
    ws3["C5"] = f"=COUNTA(C{_m_start}:C{_m_end})+COUNTA(C{_w_start}:C{_w_end})+COUNTA(C{_d_start}:C{_d_end})"
    ws3["C5"].font = font_kpi_val
    ws3["C5"].fill = soft_gray
    ws3["C5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 3: Target Selesai
    ws3.merge_cells("E3:F4")
    ws3["E3"] = "SUDAH SELESAI"
    ws3["E3"].font = font_kpi_label
    ws3["E3"].fill = accent_green
    ws3["E3"].alignment = Alignment(horizontal="center", vertical="center")

    ws3.merge_cells("E5:F5")
    ws3["E5"] = f'=COUNTIF(E{_m_start}:E{_m_end},"Selesai")+COUNTIF(E{_w_start}:E{_w_end},"Selesai")+COUNTIF(E{_d_start}:E{_d_end},"Selesai")'
    ws3["E5"].font = font_kpi_val
    ws3["E5"].fill = accent_green
    ws3["E5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 4: Target Dalam Proses
    ws3.merge_cells("G3:H4")
    ws3["G3"] = "SEDANG DIKERJAKAN"
    ws3["G3"].font = font_kpi_label
    ws3["G3"].fill = accent_yellow
    ws3["G3"].alignment = Alignment(horizontal="center", vertical="center")

    ws3.merge_cells("G5:H5")
    ws3["G5"] = f'=COUNTIF(E{_m_start}:E{_m_end},"Dalam Proses")+COUNTIF(E{_w_start}:E{_w_end},"Dalam Proses")+COUNTIF(E{_d_start}:E{_d_end},"Dalam Proses")'
    ws3["G5"].font = font_kpi_val
    ws3["G5"].fill = accent_yellow
    ws3["G5"].alignment = Alignment(horizontal="center", vertical="center")

    # Card 5: Persentase Kesiapan
    ws3.merge_cells("I3:J4")
    ws3["I3"] = "PERSEN SIAP (%)"
    ws3["I3"].font = font_kpi_label
    ws3["I3"].fill = kpi_card_fill
    ws3["I3"].alignment = Alignment(horizontal="center", vertical="center")

    ws3.merge_cells("I5:J5")
    ws3["I5"] = "=E5/C5"
    ws3["I5"].font = font_kpi_val
    ws3["I5"].number_format = '0.0%'
    ws3["I5"].fill = kpi_card_fill
    ws3["I5"].alignment = Alignment(horizontal="center", vertical="center")

    for r in range(3, 6):
        for c in range(1, 11):
            ws3.cell(row=r, column=c).border = thin_border

    monthly_data = [
        (f"Bulan: {m['code']}", m['period'], f"{m['title']} — {m['desc']}", m['pic'], m['status'], m['title'])
        for m in _md
    ]
    weekly_data = [
        (f"Minggu: {w['code']}", w['title'], f"{w['desc']}", w['pic'], w['status'], w['title'])
        for w in _wd
    ]
    daily_data = [
        (f"Hari: {d['code']}", d['period'], f"{d['title']} — {d['desc']}", d['pic'], d['status'], d['title'])
        for d in _dd
    ]

    # 1. TARGET BULANAN
    t_row = 8
    ws3.cell(row=t_row, column=1, value="1. YANG HARUS SELESAI TIAP BULAN (6-2 BULAN SEBELUM ACARA)").font = font_bold
    t_row += 1
    monthly_headers = ["Periode Target", "Batas Waktu", "Sasaran Utama & Deliverables", "Penanggung Jawab", "Status Target", "Catatan Verifikasi"]
    for col_idx, h_text in enumerate(monthly_headers, start=1):
        cell = ws3.cell(row=t_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws3.row_dimensions[t_row].height = 24
    t_row += 1

    for item in monthly_data:
        ws3.cell(row=t_row, column=1, value=item[0]).font = font_bold
        ws3.cell(row=t_row, column=2, value=item[1]).alignment = Alignment(horizontal="center")
        ws3.cell(row=t_row, column=3, value=item[2]).font = font_regular
        ws3.cell(row=t_row, column=4, value=item[3]).font = font_regular
        ws3.cell(row=t_row, column=5, value=item[4]).alignment = Alignment(horizontal="center")
        ws3.cell(row=t_row, column=6, value=item[5]).font = font_sub
        for c in range(1, 7):
            ws3.cell(row=t_row, column=c).border = thin_border
        t_row += 1
    t_row += 1

    # 2. TARGET MINGGUAN
    t_row += 2
    ws3.cell(row=t_row, column=1, value="2. YANG HARUS SELESAI TIAP MINGGU (4 MINGGU TERAKHIR)").font = font_bold
    t_row += 1
    weekly_headers = ["Minggu Ke-", "Fokus Koordinasi", "Sasaran Utama & Deliverables", "PIC Vendor / Panitia", "Status Target", "Catatan Verifikasi"]
    for col_idx, h_text in enumerate(weekly_headers, start=1):
        cell = ws3.cell(row=t_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws3.row_dimensions[t_row].height = 24
    t_row += 1

    for item in weekly_data:
        ws3.cell(row=t_row, column=1, value=item[0]).font = font_bold
        ws3.cell(row=t_row, column=2, value=item[1]).font = font_bold
        ws3.cell(row=t_row, column=3, value=item[2]).font = font_regular
        ws3.cell(row=t_row, column=4, value=item[3]).font = font_regular
        ws3.cell(row=t_row, column=5, value=item[4]).alignment = Alignment(horizontal="center")
        ws3.cell(row=t_row, column=6, value=item[5]).font = font_sub
        for c in range(1, 7):
            ws3.cell(row=t_row, column=c).border = thin_border
        t_row += 1
    t_row += 1

    # 3. TARGET HARIAN
    t_row += 2
    ws3.cell(row=t_row, column=1, value="3. YANG HARUS SELESAI TIAP HARI (7-1 HARI SEBELUM ACARA)").font = font_bold
    t_row += 1
    daily_headers = ["Hari Countdown", "Waktu Pelaksanaan", "Aksi Operasional & Pengecekan", "Penanggung Jawab", "Status Target", "Catatan Verifikasi"]
    for col_idx, h_text in enumerate(daily_headers, start=1):
        cell = ws3.cell(row=t_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = berry_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws3.row_dimensions[t_row].height = 24
    t_row += 1

    for item in daily_data:
        ws3.cell(row=t_row, column=1, value=item[0]).font = font_bold
        ws3.cell(row=t_row, column=2, value=item[1]).alignment = Alignment(horizontal="center")
        ws3.cell(row=t_row, column=3, value=item[2]).font = font_regular
        ws3.cell(row=t_row, column=4, value=item[3]).font = font_regular
        ws3.cell(row=t_row, column=5, value=item[4]).alignment = Alignment(horizontal="center")
        ws3.cell(row=t_row, column=6, value=item[5]).font = font_sub
        for c in range(1, 7):
            ws3.cell(row=t_row, column=c).border = thin_border
        t_row += 1
    t_row += 1

    dv_status = DataValidation(type="list", formula1='"Selesai,Dalam Proses,Belum Mulai"', allow_blank=True)
    ws3.add_data_validation(dv_status)
    dv_status.add(f"E{_m_start}:E{_m_end}")
    dv_status.add(f"E{_w_start}:E{_w_end}")
    dv_status.add(f"E{_d_start}:E{_d_end}")

    ws3.conditional_formatting.add(f"E{_m_start}:E{_d_end}", CellIsRule(operator="equal", formula=['"Selesai"'], fill=accent_green, font=cf_green_font))
    ws3.conditional_formatting.add(f"E{_m_start}:E{_d_end}", CellIsRule(operator="equal", formula=['"Dalam Proses"'], fill=accent_yellow, font=cf_yellow_font))
    ws3.conditional_formatting.add(f"E{_m_start}:E{_d_end}", CellIsRule(operator="equal", formula=['"Belum Mulai"'], fill=accent_red, font=cf_red_font))

    # 4. RUNDOWN HARI H
    t_row += 2
    _n_r = len(planner_master['timeline']['rundown'])
    ws3.cell(row=t_row, column=1, value=f"4. JADWAL LENGKAP HARI-H ({_n_r} ACARA DARI PAGI SAMPAI SORE)").font = font_bold
    t_row += 1
    rundown_headers = ["No", "Waktu (WIB)", "Durasi", "Fase Acara", "Agenda / Sesi Acara Detail", "Lokasi", "PIC Utama", "Cue Audio & Wardrobe", "Catatan Teknis & SOP Lapangan", "Status Sesi"]
    for col_idx, h_text in enumerate(rundown_headers, start=1):
        cell = ws3.cell(row=t_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws3.row_dimensions[t_row].height = 24
    t_row += 1

    full_rundown = planner_master['timeline']['rundown']
    start_rundown_row = t_row

    for item in full_rundown:
        c_no = ws3.cell(row=t_row, column=1, value=item['num'])
        c_no.alignment = Alignment(horizontal="center")
        c_no.font = font_bold

        c_time = ws3.cell(row=t_row, column=2, value=item['time'])
        c_time.alignment = Alignment(horizontal="center")
        c_time.font = font_bold

        c_dur = ws3.cell(row=t_row, column=3, value=item['duration'])
        c_dur.alignment = Alignment(horizontal="center")

        c_phase = ws3.cell(row=t_row, column=4, value=item['phase'])
        c_phase.font = font_bold

        c_title = ws3.cell(row=t_row, column=5, value=item['title'])
        c_title.font = font_bold

        ws3.cell(row=t_row, column=6, value=item['location']).font = font_regular
        ws3.cell(row=t_row, column=7, value=item['pic']).font = font_regular
        ws3.cell(row=t_row, column=8, value=f"{item['audio_cue']} | {item['wardrobe']}").font = font_sub
        ws3.cell(row=t_row, column=9, value=item['notes']).font = font_regular

        c_status = ws3.cell(row=t_row, column=10, value=item['status'])
        c_status.alignment = Alignment(horizontal="center")
        c_status.font = font_bold

        for c in range(1, 11):
            ws3.cell(row=t_row, column=c).border = thin_border
        t_row += 1

    end_rundown_row = t_row - 1
    dv_rundown = DataValidation(type="list", formula1='"Selesai,Dalam Proses,Belum Mulai"', allow_blank=True)
    ws3.add_data_validation(dv_rundown)
    dv_rundown.add(f"J{start_rundown_row}:J{end_rundown_row}")
    ws3.conditional_formatting.add(f"J{start_rundown_row}:J{end_rundown_row}", CellIsRule(operator="equal", formula=['"Selesai"'], fill=accent_green, font=cf_green_font))
    ws3.conditional_formatting.add(f"J{start_rundown_row}:J{end_rundown_row}", CellIsRule(operator="equal", formula=['"Dalam Proses"'], fill=accent_yellow, font=cf_yellow_font))
    ws3.conditional_formatting.add(f"J{start_rundown_row}:J{end_rundown_row}", CellIsRule(operator="equal", formula=['"Belum Mulai"'], fill=accent_red, font=cf_red_font))

    ws3.freeze_panes = 'A9'

    # -------------------------------------------------------------
    # TAB 4: Hitung Katering (Interactive Simulator & Estimator)
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="Hitung Katering")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:E1")
    ws4["A1"] = "HITUNG KEBUTUHAN MAKAN & BIAYA KATERING"
    ws4["A1"].font = font_white_title
    ws4["A1"].fill = navy_fill
    ws4["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 36

    ws4.cell(row=2, column=1, value="LEGENDA:").font = font_bold
    ws4.merge_cells("B2:C2")
    ws4["B2"] = "KOLOM KUNING = INPUT EDITABLE"
    ws4["B2"].font = Font(name="Calibri", size=9, bold=True, color="856404")
    ws4["B2"].fill = input_fill
    ws4["B2"].alignment = Alignment(horizontal="center")

    ws4.merge_cells("D2:E2")
    ws4["D2"] = "KOLOM HIJAU = HASIL KALKULASI OTOMATIS"
    ws4["D2"].font = Font(name="Calibri", size=9, bold=True, color="0F5132")
    ws4["D2"].fill = accent_green
    ws4["D2"].alignment = Alignment(horizontal="center")

    ws4.cell(row=4, column=1, value="1. PARAMETER PERHITUNGAN TAMU (SIMULATOR KEHADIRAN):").font = font_bold

    calc_inputs = [
        ("Jumlah Undangan Fisik (Lembar)", round(plan.estimated_pax * 0.4), "Ubah sesuai jumlah cetak fisik"),
        ("Estimasi Tamu per Undangan Fisik", 2.0, "Standar rata-rata kehadiran: 2 orang per undangan"),
        ("Jumlah Undangan Digital / Broadcast", round(plan.estimated_pax * 0.2), "Ubah sesuai daftar broadcast digital"),
        ("Estimasi Kehadiran per Undangan Digital", 1.5, "Standar rata-rata kehadiran e-invitation: 1.5 orang"),
        ("Subtotal Estimasi Tamu Undangan (Pax)", "=(B5*B6)+(B7*B8)", "Kalkulasi otomatis proyeksi tamu hadir"),
        ("Buffer Panitia, Kru Vendor & Keluarga (%)", 0.10, "Standar aman WO: 10% dari tamu hadir"),
        ("Porsi Tambahan Cadangan & Panitia (Pax)", "=ROUND(B9*B10, 0)", "Kalkulasi otomatis porsi buffer cadangan"),
        ("TOTAL ESTIMASI KEBUTUHAN PORSI BERSIH (PAX)", "=B9+B11", "Basis utama pemesanan paket katering ke vendor"),
    ]

    for idx, (label, val, note) in enumerate(calc_inputs, start=5):
        ws4.cell(row=idx, column=1, value=label).font = font_bold if idx in [9, 12] else font_regular
        c_val = ws4.cell(row=idx, column=2, value=val)
        c_val.font = font_bold
        if idx == 10:
            c_val.number_format = '0%'
        elif idx in [6, 8]:
            c_val.number_format = '0.0'
        else:
            c_val.number_format = '#,##0'
        
        if idx in [5, 6, 7, 8, 10]:
            c_val.fill = input_fill
        elif idx == 12:
            c_val.fill = accent_green

        ws4.cell(row=idx, column=3, value=note).font = font_sub
        for c in range(1, 4):
            ws4.cell(row=idx, column=c).border = thin_border

    # Section 2: Distribusi Alokasi Porsi Menu
    ws4.cell(row=14, column=1, value="2. DISTRIBUSI ALOKASI PORSI MENU MAKANAN (STANDAR INDUSTRI WEDDING):").font = font_bold
    headers4 = ["Komponen Jamuan", "Rasio Formula Standar", "Jumlah Porsi Dianjurkan", "Satuan", "Keterangan Distribusi"]
    for col_idx, h_text in enumerate(headers4, start=1):
        cell = ws4.cell(row=15, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws4.row_dimensions[15].height = 24

    catering_calc = [
        ("Menu Buffet Utama (Prasmanan)", 0.60, "=ROUND($B$12*B16, 0)", "Porsi", "6 menu utama lauk pauk, nasi, sup & dessert"),
        ("Food Stalls / Gubukan (Variasi Menu)", 0.40, "=ROUND($B$12*B17*4, 0)", "Porsi Stall", "Rekomendasi 4 porsi gubukan per tamu (Sate, Zuppa, Siomay, Es Krim)"),
        ("Porsi Meja Khusus VIP & Keluarga Inti", 0.10, "=ROUND($B$12*B18, 0)", "Porsi VIP", "Disajikan khusus di ruang transit keluarga & meja tamu VIP"),
        ("Konsumsi Box Kru & Vendor Standby", 0.05, "=ROUND($B$12*B19, 0)", "Box Konsumsi", "Disiapkan box makanan praktis sebelum acara dimulai"),
    ]

    c_row = 16
    for item in catering_calc:
        ws4.cell(row=c_row, column=1, value=item[0]).font = font_bold
        c_pct = ws4.cell(row=c_row, column=2, value=item[1])
        c_pct.number_format = '0%'
        c_pct.alignment = Alignment(horizontal="center")

        c_calc = ws4.cell(row=c_row, column=3, value=item[2])
        c_calc.number_format = '#,##0'
        c_calc.font = font_bold
        c_calc.alignment = Alignment(horizontal="right")

        ws4.cell(row=c_row, column=4, value=item[3]).alignment = Alignment(horizontal="center")
        ws4.cell(row=c_row, column=5, value=item[4]).font = font_regular

        for c in range(1, 6):
            ws4.cell(row=c_row, column=c).border = thin_border
        c_row += 1

    # Section 3: Fasilitas & Logistik Tamu
    c_row += 1
    ws4.cell(row=c_row, column=1, value="3. ESTIMASI FASILITAS & LOGISTIK TAMU (FORMULA WO):").font = font_bold
    c_row += 1
    log_headers = ["Item Fasilitas Tamu", "Formula Kebutuhan", "Satuan", "Keterangan Logistik"]
    for col_idx, h_text in enumerate(log_headers, start=1):
        cell = ws4.cell(row=c_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws4.row_dimensions[c_row].height = 24
    c_row += 1

    log_data = [
        ("Kebutuhan Air Mineral & Minuman Tamu", "=ROUND($B$12*1.5, 0)", "Gelas / Botol", "Rata-rata konsumsi minuman 1.5 cup per orang"),
        ("Kebutuhan Meja Bundar VIP (10 Pax)", "=ROUNDUP($B$12*0.15/10, 0)", "Unit Meja", "Untuk alokasi 15% tamu duduk di meja VIP"),
        ("Estimasi Kursi Duduk (Standing Party 70%)", "=ROUNDUP($B$12*0.70, 0)", "Unit Kursi", "Kebutuhan kursi ballroom dengan rasio flow 70%"),
        ("Estimasi Kapasitas Parkir Kendaraan Tamu", "=ROUNDUP($B$12*0.35, 0)", "Slot Mobil", "Asumsi 1 mobil berisi 2.5 - 3 orang tamu"),
    ]
    for item in log_data:
        ws4.cell(row=c_row, column=1, value=item[0]).font = font_bold
        c_val = ws4.cell(row=c_row, column=2, value=item[1])
        c_val.font = font_bold
        c_val.number_format = '#,##0'
        ws4.cell(row=c_row, column=3, value=item[2]).alignment = Alignment(horizontal="center")
        ws4.cell(row=c_row, column=4, value=item[3]).font = font_sub
        for c in range(1, 5):
            ws4.cell(row=c_row, column=c).border = thin_border
        c_row += 1

    # Section 4: Simulasi Biaya Katering Otomatis
    c_row += 1
    ws4.cell(row=c_row, column=1, value="4. SIMULASI ANGGARAN KATERING OTOMATIS:").font = font_bold
    c_row += 1
    sim_headers = ["Item Simulasi", "Nilai / Formula", "Satuan", "Keterangan"]
    for col_idx, h_text in enumerate(sim_headers, start=1):
        cell = ws4.cell(row=c_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = berry_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws4.row_dimensions[c_row].height = 24
    c_row += 1

    sim_data = [
        ("Estimasi Harga Paket Prasmanan per Pax", 95000, "Rp / Pax", "Ubah sesuai penawaran vendor katering"),
        ("Estimasi Harga Rata-rata Stall per Porsi", 25000, "Rp / Porsi", "Ubah sesuai variasi gubukan"),
        ("Subtotal Biaya Prasmanan (Buffet)", "=C16*B30", "Rp", "Porsi Buffet x Harga per Pax"),
        ("Subtotal Biaya Food Stalls (Gubukan)", "=C17*B31", "Rp", "Porsi Stall x Harga per Porsi"),
        ("TOTAL BIAYA MAKAN", "=SUM(B32:B33)", "Rp", "Total proyeksi belanja katering"),
        ("BIAYA MAKAN PER TAMU", "=ROUND(B34/$B$12, 0)", "Rp / Tamu", "Rasio biaya makanan per orang"),
    ]

    for item in sim_data:
        ws4.cell(row=c_row, column=1, value=item[0]).font = font_bold if "TOTAL" in item[0] or "BIAYA" in item[0] else font_regular
        c_v = ws4.cell(row=c_row, column=2, value=item[1])
        c_v.font = font_bold
        c_v.number_format = '"Rp " #,##0'
        if c_row in [30, 31]:
            c_v.fill = input_fill
        elif c_row == 34:
            c_v.fill = accent_green

        ws4.cell(row=c_row, column=3, value=item[2]).alignment = Alignment(horizontal="center")
        ws4.cell(row=c_row, column=4, value=item[3]).font = font_sub

        for c in range(1, 5):
            ws4.cell(row=c_row, column=c).border = thin_border
        c_row += 1

    # Section 5: Analisis Sensitivitas Kehadiran Tamu (3 Skenario)
    c_row += 1
    ws4.cell(row=c_row, column=1, value="5. KALAU TAMU LEBIH SEDIKIT / LEBIH BANYAK (3 CONTOH):").font = font_bold
    c_row += 1
    sens_headers = ["Skenario Kehadiran", "Faktor Multiplier", "Proyeksi Tamu (Pax)", "Estimasi Total Biaya Katering (Rp)", "Dampak Anggaran"]
    for col_idx, h_text in enumerate(sens_headers, start=1):
        cell = ws4.cell(row=c_row, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws4.row_dimensions[c_row].height = 24
    c_row += 1

    sens_data = [
        ("Kalau tamu sedikit (80% datang)", 0.80, "=ROUND($B$12*B39, 0)", "=ROUND(B34*B39, 0)", "Hemat 20% biaya katering"),
        ("Perkiraan normal (100% datang)", 1.00, "=$B$12", "=B34", "Sesuai kalkulasi awal"),
        ("Kalau tamu membludak (120% datang)", 1.20, "=ROUND($B$12*B41, 0)", "=ROUND(B34*B41, 0)", "Perlu alokasi buffer dana darurat +20%"),
    ]
    for item in sens_data:
        ws4.cell(row=c_row, column=1, value=item[0]).font = font_bold
        c_f = ws4.cell(row=c_row, column=2, value=item[1])
        c_f.number_format = '0%'
        c_f.alignment = Alignment(horizontal="center")

        c_p = ws4.cell(row=c_row, column=3, value=item[2])
        c_p.number_format = '#,##0'
        c_p.alignment = Alignment(horizontal="center")

        c_c = ws4.cell(row=c_row, column=4, value=item[3])
        c_c.number_format = '"Rp " #,##0'
        c_c.font = font_bold

        ws4.cell(row=c_row, column=5, value=item[4]).font = font_sub
        for c in range(1, 6):
            ws4.cell(row=c_row, column=c).border = thin_border
        c_row += 1

    ws4.freeze_panes = 'A16'

    # -------------------------------------------------------------
    # TAB 5: Master Daftar Barang (Operational Asset Matrix)
    # -------------------------------------------------------------
    ws5 = wb.create_sheet(title="Daftar Barang")
    ws5.views.sheetView[0].showGridLines = True

    ws5.merge_cells("A1:H1")
    ws5["A1"] = "DAFTAR BARANG YANG HARUS DISIAPKAN UNTUK HARI-H"
    ws5["A1"].font = font_white_title
    ws5["A1"].fill = navy_fill
    ws5["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[1].height = 36

    # Top Summary KPI Cards (Rows 3-4)
    ws5.merge_cells("A3:B3")
    ws5["A3"] = "TOTAL BARANG"
    ws5["A3"].font = font_kpi_label
    ws5["A3"].fill = kpi_card_fill
    ws5["A3"].alignment = Alignment(horizontal="center")

    _log = planner_master['logistics']
    _n_log = len(_log)
    _log_end = 7 + _n_log - 1
    ws5.merge_cells("A4:B4")
    ws5["A4"] = f"=COUNTA(C7:C{_log_end})"
    ws5["A4"].font = font_kpi_val
    ws5["A4"].fill = kpi_card_fill
    ws5["A4"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("C3:D3")
    ws5["C3"] = "BARANG SUDAH SIAP"
    ws5["C3"].font = font_kpi_label
    ws5["C3"].fill = accent_green
    ws5["C3"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("C4:D4")
    ws5["C4"] = f'=COUNTIF(F7:F{_log_end}, "Siap")'
    ws5["C4"].font = font_kpi_val
    ws5["C4"].fill = accent_green
    ws5["C4"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("E3:F3")
    ws5["E3"] = "BARANG BELUM SIAP"
    ws5["E3"].font = font_kpi_label
    ws5["E3"].fill = accent_red
    ws5["E3"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("E4:F4")
    ws5["E4"] = f'=COUNTIF(F7:F{_log_end}, "Belum Siap")'
    ws5["E4"].font = font_kpi_val
    ws5["E4"].fill = accent_red
    ws5["E4"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("G3:H3")
    ws5["G3"] = "PERSEN BARANG SIAP (%)"
    ws5["G3"].font = font_kpi_label
    ws5["G3"].fill = soft_gray
    ws5["G3"].alignment = Alignment(horizontal="center")

    ws5.merge_cells("G4:H4")
    ws5["G4"] = "=C4/A4"
    ws5["G4"].font = font_kpi_val
    ws5["G4"].number_format = '0.0%'
    ws5["G4"].fill = soft_gray
    ws5["G4"].alignment = Alignment(horizontal="center")

    for r in range(3, 5):
        for c in range(1, 9):
            ws5.cell(row=r, column=c).border = thin_border

    headers5 = ["No.", "Kategori Logistik", "Nama Item Perlengkapan", "Penanggung Jawab (PIC)", "Kuantitas / Jumlah", "Status Kesiapan", "Lokasi Penyimpanan", "Catatan Khusus"]
    for col_idx, h_text in enumerate(headers5, start=1):
        cell = ws5.cell(row=6, column=col_idx, value=h_text)
        cell.font = font_white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws5.row_dimensions[6].height = 26

    checklist_items = [
        (i + 1, it['cat'], it['name'], it['pic'], it['qty'], it['status'], it['loc'], it['note'])
        for i, it in enumerate(_log)
    ]

    l_row = 7
    for item in checklist_items:
        ws5.cell(row=l_row, column=1, value=item[0]).alignment = Alignment(horizontal="center")
        ws5.cell(row=l_row, column=2, value=item[1]).font = font_bold
        ws5.cell(row=l_row, column=3, value=item[2]).font = font_regular
        ws5.cell(row=l_row, column=4, value=item[3]).font = font_regular
        ws5.cell(row=l_row, column=5, value=item[4]).alignment = Alignment(horizontal="center")
        
        c_st = ws5.cell(row=l_row, column=6, value=item[5])
        c_st.alignment = Alignment(horizontal="center")
        
        ws5.cell(row=l_row, column=7, value=item[6]).font = font_regular
        ws5.cell(row=l_row, column=8, value=item[7]).font = font_sub
        
        for c in range(1, 9):
            ws5.cell(row=l_row, column=c).border = thin_border
        l_row += 1

    dv_check = DataValidation(type="list", formula1='"Siap,Belum Siap,Dalam Proses,Tidak Perlu"', allow_blank=True)
    ws5.add_data_validation(dv_check)
    dv_check.add(f"F7:F{l_row-1}")

    ws5.conditional_formatting.add(f"F7:F{l_row-1}", CellIsRule(operator="equal", formula=['"Siap"'], fill=accent_green, font=cf_green_font))
    ws5.conditional_formatting.add(f"F7:F{l_row-1}", CellIsRule(operator="equal", formula=['"Belum Siap"'], fill=accent_red, font=cf_red_font))
    ws5.conditional_formatting.add(f"F7:F{l_row-1}", CellIsRule(operator="equal", formula=['"Dalam Proses"'], fill=accent_yellow, font=cf_yellow_font))

    ws5.freeze_panes = 'A7'

    # -------------------------------------------------------------
    # TAB 6: Tabungan (Savings Vault progress & deposit history)
    # -------------------------------------------------------------
    ws6 = wb.create_sheet(title="Tabungan")
    ws6.views.sheetView[0].showGridLines = True

    ws6.merge_cells("A1:E1")
    ws6["A1"] = "TABUNGAN ACARA — TARGET, TERKUMPUL & RIWAYAT SETORAN"
    ws6["A1"].font = font_white_title
    ws6["A1"].fill = navy_fill
    ws6["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws6.row_dimensions[1].height = 36

    # Legend: yellow = ketik sendiri, green = otomatis (mirrors other sheets).
    ws6.cell(row=2, column=1, value="KUNING = ketik sendiri").font = Font(name="Calibri", size=9, bold=True, color="856404")
    ws6.cell(row=2, column=1).fill = input_fill
    ws6.cell(row=2, column=1).alignment = Alignment(horizontal="center")
    ws6.merge_cells("B2:C2")
    ws6["B2"] = "Ketik target & setoran di kolom kuning"
    ws6["B2"].font = font_sub
    ws6["B2"].alignment = Alignment(horizontal="center")
    ws6.merge_cells("D2:E2")
    ws6["D2"] = "Kolom hijau = total otomatis, jangan diubah"
    ws6["D2"].font = Font(name="Calibri", size=9, bold=True, color="0F5132")
    ws6["D2"].fill = accent_green
    ws6["D2"].alignment = Alignment(horizontal="center")

    # Resolve vault: prefer vault linked to this plan, else customer's latest vault.
    vault = None
    try:
        vault = getattr(plan, 'savings_vault', None)
        if vault is None:
            vault = plan.customer.savings_vaults.order_by('-created_at').first()
    except Exception:
        vault = None

    if vault is not None:
        # KPI cards (values are live formulas wired to the table below)
        ws6.merge_cells("A3:B3")
        ws6["A3"] = "TARGET TABUNGAN"
        ws6["A3"].font = font_kpi_label
        ws6["A3"].fill = kpi_card_fill
        ws6["A3"].alignment = Alignment(horizontal="center")
        ws6.merge_cells("A4:B4")
        ws6["A4"] = float(vault.target_amount or 0)
        ws6["A4"].number_format = '"Rp " #,##0'
        ws6["A4"].font = font_kpi_val
        ws6["A4"].fill = input_fill  # editable: user raises/lowers target here
        ws6["A4"].alignment = Alignment(horizontal="center")

        ws6.merge_cells("C3:D3")
        ws6["C3"] = "SUDAH TERKUMPUL"
        ws6["C3"].font = font_kpi_label
        ws6["C3"].fill = accent_green
        ws6["C3"].alignment = Alignment(horizontal="center")
        ws6.merge_cells("C4:D4")
        # Filled with formula after the table is built (points at TOTAL OTOMATIS row).
        ws6["C4"] = 0
        ws6["C4"].number_format = '"Rp " #,##0'
        ws6["C4"].font = font_kpi_val
        ws6["C4"].fill = accent_green
        ws6["C4"].alignment = Alignment(horizontal="center")

        ws6["E3"] = "TERKUMPUL (%)"
        ws6["E3"].font = font_kpi_label
        ws6["E3"].fill = soft_gray
        ws6["E3"].alignment = Alignment(horizontal="center")
        ws6["E4"] = 0  # replaced with =IF(A4=0,0,C4/A4) after table build
        ws6["E4"].number_format = '0.0%'
        ws6["E4"].font = font_kpi_val
        ws6["E4"].fill = soft_gray
        ws6["E4"].alignment = Alignment(horizontal="center")

        for r in range(3, 5):
            for c in range(1, 6):
                ws6.cell(row=r, column=c).border = thin_border

        ws6.cell(row=6, column=1, value="Nama tabungan").font = font_bold
        ws6.cell(row=6, column=2, value=vault.title).font = font_regular
        ws6.cell(row=7, column=1, value="Target tanggal").font = font_bold
        ws6.cell(row=7, column=2, value=str(vault.target_date)).font = font_regular
        ws6.cell(row=8, column=1, value="Sisa yang belum terkumpul").font = font_bold
        c_rem = ws6.cell(row=8, column=2, value=f"=A4-C4")
        c_rem.number_format = '"Rp " #,##0'
        c_rem.font = font_bold

        # Deposit history — every amount cell is yellow (ketik sendiri).
        # 5 blank entry rows are pre-added so users just type; TOTAL covers them.
        ws6.cell(row=10, column=1, value="RIWAYAT SETORAN — ketik setoran baru di baris kuning kosong").font = font_bold
        dep_headers = ["No.", "Tanggal", "Jumlah (Rp)", "Catatan", "Cara Bayar"]
        for col_idx, h_text in enumerate(dep_headers, start=1):
            cell = ws6.cell(row=11, column=col_idx, value=h_text)
            cell.font = font_white_bold
            cell.fill = navy_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        ws6.row_dimensions[11].height = 24

        deposits = list(vault.deposits.all().order_by('created_at'))
        d_row = 12
        for i, dep in enumerate(deposits, start=1):
            ws6.cell(row=d_row, column=1, value=i).alignment = Alignment(horizontal="center")
            ws6.cell(row=d_row, column=2, value=dep.created_at.strftime("%d %b %Y") if dep.created_at else "").alignment = Alignment(horizontal="center")
            c_amt = ws6.cell(row=d_row, column=3, value=float(dep.amount or 0))
            c_amt.number_format = '"Rp " #,##0'
            c_amt.font = font_bold
            c_amt.fill = input_fill  # editable: fix a typo by typing over it
            c_amt.alignment = Alignment(horizontal="right")
            ws6.cell(row=d_row, column=4, value=dep.notes or "").font = font_regular
            ws6.cell(row=d_row, column=4).fill = input_fill
            ws6.cell(row=d_row, column=5, value=dep.payment_method or "").font = font_regular
            for c in range(1, 6):
                ws6.cell(row=d_row, column=c).border = thin_border
            d_row += 1
        # Blank entry rows: just type date + amount + note, totals update by themselves.
        BLANK_ROWS = 5
        first_entry = 12
        for j in range(BLANK_ROWS):
            n = len(deposits) + j + 1
            ws6.cell(row=d_row, column=1, value=n).alignment = Alignment(horizontal="center")
            ws6.cell(row=d_row, column=1).fill = input_fill
            ws6.cell(row=d_row, column=2, value="").alignment = Alignment(horizontal="center")
            ws6.cell(row=d_row, column=2).fill = input_fill
            c_new = ws6.cell(row=d_row, column=3, value="")
            c_new.number_format = '"Rp " #,##0'
            c_new.font = font_bold
            c_new.fill = input_fill
            c_new.alignment = Alignment(horizontal="right")
            ws6.cell(row=d_row, column=4, value="").font = font_regular
            ws6.cell(row=d_row, column=4).fill = input_fill
            ws6.cell(row=d_row, column=5, value="").font = font_regular
            ws6.cell(row=d_row, column=5).fill = input_fill
            for c in range(1, 6):
                ws6.cell(row=d_row, column=c).border = thin_border
            d_row += 1
        last_entry = d_row - 1
        # Total row (live formula over ALL entry rows incl. blanks)
        ws6.cell(row=d_row, column=1, value="").alignment = Alignment(horizontal="center")
        ws6.cell(row=d_row, column=2, value="TOTAL OTOMATIS").font = font_bold
        c_tot = ws6.cell(row=d_row, column=3, value=f"=SUM(C{first_entry}:C{last_entry})")
        c_tot.number_format = '"Rp " #,##0'
        c_tot.font = font_bold
        c_tot.fill = accent_green
        for c in range(1, 6):
            cell = ws6.cell(row=d_row, column=c)
            if c != 3:
                cell.fill = soft_gray
            cell.border = thin_border
        # Wire KPI cards to the live total: everything up top follows the table.
        ws6["C4"] = f"=C{d_row}"
        ws6["E4"] = "=IF(A4=0,0,C4/A4)"
        ws6.cell(row=8, column=2, value="=A4-C4")  # sisa (already formula, reaffirmed)
        ws6.freeze_panes = 'A12'
    else:
        ws6.merge_cells("A3:E3")
        ws6["A3"] = "Belum ada tabungan untuk rencana ini"
        ws6["A3"].font = font_bold
        ws6["A3"].alignment = Alignment(horizontal="center")
        ws6.merge_cells("A4:E6")
        ws6["A4"] = (
            "Cara pakai: buka halaman Tabungan di aplikasi, buat tabungan baru "
            "(misal: Tabungan Pernikahan), lalu setor sedikit demi sedikit. "
            "Setelah ada tabungan, unduh ulang Excel ini dan riwayat setoran akan muncul otomatis di sini."
        )
        ws6["A4"].font = font_regular
        ws6["A4"].alignment = Alignment(wrap_text=True, vertical="top")

    # Auto-adjust column widths across all worksheets
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # -------------------------------------------------------------
    # TAB 0: Dashboard (cover summary + live charts, first sheet)
    # Built LAST so its hand-tuned column widths survive auto-adjust.
    # Every number here is a formula pointing at the other sheets,
    # so the charts refresh themselves when the user edits yellow cells.
    # -------------------------------------------------------------
    dash = wb.create_sheet(title="Dashboard", index=0)
    wb.active = 0
    dash.views.sheetView[0].showGridLines = False
    dash.sheet_properties.tabColor = "D9A441"
    dash.freeze_panes = 'A4'

    dash.merge_cells("A1:N1")
    _slug = ''
    try:
        if plan.event_category and plan.event_category.slug:
            _slug = plan.event_category.slug.lower()
    except Exception:
        _slug = ''
    _emoji = {'wedding': '\U0001F492', 'corporate': '\U0001F3E2', 'seminar': '\U0001F393',
              'birthday': '\U0001F382', 'exhibition': '\U0001F3AA', 'intimate': '\U0001F33F'}.get(_slug, '\U0001F4CB')
    dash["A1"] = f"{_emoji} VENDORAMAN \u2014 DASHBOARD RINGKASAN ACARA"
    dash["A1"].font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    dash["A1"].fill = navy_fill
    dash["A1"].alignment = Alignment(horizontal="center", vertical="center")
    dash.row_dimensions[1].height = 33.75

    dash.merge_cells("A2:N2")
    dash["A2"] = ("='Budget & Bayar'!B8&\" \u2022 \"&'Budget & Bayar'!E8&\" \u2022 \""
                   "&TEXT('Budget & Bayar'!B9,\"DD MMMM YYYY\")&\" \u2022 \""
                   "&'Budget & Bayar'!E9&\" tamu\"")
    dash["A2"].font = Font(name="Calibri", size=10, color="4B4F72")
    dash["A2"].fill = soft_gray
    dash["A2"].alignment = Alignment(horizontal="center", vertical="center")
    dash.row_dimensions[2].height = 18

    def _dash_kpi(label_range, label, value_range, formula, num_fmt, sub_range=None, sub=""):
        dash.merge_cells(label_range)
        dash[label_range.split(":")[0]] = label
        c = dash[label_range.split(":")[0]]
        c.font = font_kpi_label
        c.fill = kpi_card_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        dash.merge_cells(value_range)
        top = value_range.split(":")[0]
        dash[top] = formula
        v = dash[top]
        v.number_format = num_fmt
        v.font = font_kpi_val
        v.fill = soft_gray
        v.alignment = Alignment(horizontal="center", vertical="center")
        if sub_range:
            dash.merge_cells(sub_range)
            s = dash[sub_range.split(":")[0]]
            s.value = sub
            s.font = Font(name="Calibri", size=8, color="4B4F72")
            s.fill = soft_gray
            s.alignment = Alignment(horizontal="center", vertical="center")

    dash.merge_cells("A4:N4")
    dash["A4"] = "RINGKASAN KUNCI (KPI)"
    dash["A4"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    dash["A4"].fill = berry_fill
    dash["A4"].alignment = Alignment(horizontal="center", vertical="center")
    dash.row_dimensions[4].height = 19.5

    _dash_kpi("A5:D5", "HARI MENUJU ACARA", "A6:D6", "='Jadwal & Rundown'!A5", '0" hari"',
              "A7:D7", "HITUNG MUNDUR OTOMATIS")
    _dash_kpi("F5:I5", "BUDGET TERPAKAI", "F6:I6", "='Budget & Bayar'!G5", '0.0%',
              "F7:I7", "Dari batas budget maksimal")
    _dash_kpi("K5:N5", "SISA UANG KAMU", "K6:N6", "='Budget & Bayar'!E5", '"Rp " #,##0',
              "K7:N7", "Batas budget dikurangi realisasi")
    dash.row_dimensions[5].height = 15.75
    dash.row_dimensions[6].height = 30
    dash.row_dimensions[7].height = 15.75

    _dash_kpi("A9:D9", "PERSEN SIAP PERSIAPAN", "A10:D10", "='Jadwal & Rundown'!I5", '0.0%',
              "A11:D11", "Checklist + rundown Hari-H")
    _dash_kpi("F9:I9", "BARANG SUDAH SIAP", "F10:I10", "='Daftar Barang'!G4", '0.0%',
              "F11:I11", "Dari total barang perlengkapan")
    _dash_kpi("K9:N9", "TABUNGAN TERKUMPUL", "K10:N10", "=Tabungan!E4", '0.0%',
              "K11:N11", "Dari target tabungan acara")
    dash.row_dimensions[9].height = 15.75
    dash.row_dimensions[10].height = 30
    dash.row_dimensions[11].height = 15.75

    for _r in list(range(5, 8)) + list(range(9, 12)):
        for _c in range(1, 15):
            dash.cell(row=_r, column=_c).border = thin_border
    # Sisa uang hijau kalau plus, merah kalau minus; serapan merah kalau >100%.
    dash.conditional_formatting.add("K6:N6", CellIsRule(operator="greaterThan", formula=["0"], fill=accent_green, font=cf_green_font))
    dash.conditional_formatting.add("K6:N6", CellIsRule(operator="lessThan", formula=["0"], fill=accent_red, font=cf_red_font))
    dash.conditional_formatting.add("F6:I6", CellIsRule(operator="greaterThan", formula=["1"], fill=accent_red, font=cf_red_font))

    dash.merge_cells("A13:N13")
    dash["A13"] = "VISUALISASI & GRAFIK"
    dash["A13"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    dash["A13"].fill = berry_fill
    dash["A13"].alignment = Alignment(horizontal="center", vertical="center")
    dash.row_dimensions[13].height = 19.5

    # Chart helper (hidden-ish, far right): counts for the status bar chart.
    dash.merge_cells("Q14:R14")
    dash["Q14"] = "STATUS PERSIAPAN (BANTUAN GRAFIK)"
    dash["Q14"].font = Font(name="Calibri", size=8, bold=True, color="4B4F72")
    dash["Q14"].fill = kpi_card_fill
    dash["Q14"].alignment = Alignment(horizontal="left", vertical="center")
    for _r, _lbl, _f in ((15, "Selesai", "='Jadwal & Rundown'!E5"),
                         (16, "Dalam Proses", "='Jadwal & Rundown'!G5"),
                         (17, "Belum Mulai", "='Jadwal & Rundown'!C5-'Jadwal & Rundown'!E5-'Jadwal & Rundown'!G5")):
        dash.cell(row=_r, column=17, value=_lbl).font = Font(name="Calibri", size=9)
        dash.cell(row=_r, column=17).fill = soft_gray
        dash.cell(row=_r, column=17).alignment = Alignment(horizontal="left", vertical="center")
        c = dash.cell(row=_r, column=18, value=_f)
        c.number_format = '0'
        c.font = Font(name="Calibri", size=11)
        c.alignment = Alignment(horizontal="center", vertical="center")
    for _r in (14, 15, 16, 17):
        dash.row_dimensions[_r].height = 15

    from openpyxl.chart import BarChart, DoughnutChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.marker import DataPoint
    from openpyxl.drawing.fill import PatternFillProperties, ColorChoice

    _navy = "1B1F3B"
    _gold = "D9A441"
    _berry = "B23A5D"
    _sage = "5C7A5E"
    _slate = "64748B"

    # Chart 1: Target vs Realisasi per kategori (clustered column, category colors).
    _bar_colors = {
        'wedding': ("1B1F3B", "D9A441"),
        'corporate': ("3FA7D6", "1868B7"),
        'seminar': ("E1AD01", "0F8B8D"),
        'birthday': ("F2B705", "E63979"),
        'exhibition': ("0B7285", "E8590C"),
        'intimate': ("8A9A5B", "B8877A"),
    }.get(_slug, ("1B1F3B", "D9A441"))
    ch1 = BarChart()
    ch1.type = "col"
    ch1.style = 10
    ch1.title = "Target vs Realisasi per Kategori"
    ch1.y_axis.title = "Rupiah"
    ch1.y_axis.numFmt = '"Rp "#,##0'
    ch1.height = 7.5
    ch1.width = 15
    ch1.gapWidth = 150
    ch1.legend.position = "r"
    cats = Reference(ws1, min_col=2, min_row=15, max_row=19)
    for _col, _fill in ((4, _bar_colors[0]), (6, _bar_colors[1])):
        vals = Reference(ws1, min_col=_col, min_row=14, max_row=19)
        ch1.add_data(vals, titles_from_data=True)
        ch1.series[-1].graphicalProperties.solidFill = _fill
        ch1.series[-1].graphicalProperties.line.noFill = True
    ch1.set_categories(cats)
    dash.add_chart(ch1, "A15")

    # Chart 2: Alokasi budget share (doughnut with % labels).
    ch2 = DoughnutChart()
    ch2.title = "Alokasi Anggaran (%)"
    ch2.height = 7.5
    ch2.width = 15
    ch2.legend.position = "r"
    _vals = Reference(ws1, min_col=3, min_row=14, max_row=19)
    ch2.add_data(_vals, titles_from_data=True)
    ch2.set_categories(Reference(ws1, min_col=2, min_row=15, max_row=19))
    ch2.series[0].graphicalProperties.solidFill = "4F81BD"
    ch2.series[0].graphicalProperties.line.noFill = True
    for _i, _fill in enumerate([_navy, _gold, _berry, _sage, _slate]):
        pt = DataPoint(idx=_i)
        pt.graphicalProperties.solidFill = _fill
        pt.graphicalProperties.line.noFill = True
        ch2.series[0].data_points.append(pt)
    ch2.series[0].dLbls = DataLabelList()
    ch2.series[0].dLbls.showPercent = True
    ch2.series[0].dLbls.showCatName = True
    ch2.series[0].dLbls.showLeaderLines = True
    dash.add_chart(ch2, "H15")

    # Chart 3: Status persiapan (horizontal bar from the Q:R helper).
    ch3 = BarChart()
    ch3.type = "bar"
    ch3.style = 10
    ch3.title = "Status Persiapan Acara"
    ch3.height = 7.5
    ch3.width = 15
    ch3.gapWidth = 150
    ch3.legend = None
    ch3.add_data(Reference(dash, min_col=18, min_row=14, max_row=17), titles_from_data=True)
    ch3.set_categories(Reference(dash, min_col=17, min_row=15, max_row=17))
    ch3.series[0].tx = SeriesLabel(v="Jumlah")
    ch3.series[0].graphicalProperties.solidFill = _berry
    ch3.series[0].graphicalProperties.line.noFill = True
    dash.add_chart(ch3, "A32")

    # Chart 4: Doughnut tambahan — beda tiap kategori (progress tabungan /
    # status pembayaran vendor / kesiapan logistik).
    if _slug in ('corporate', 'seminar'):
        _ch4_title = ('DISTRIBUSI STATUS PEMBAYARAN PESERTA/VENDOR' if _slug == 'seminar'
                       else 'DISTRIBUSI STATUS PEMBAYARAN VENDOR')
        _ch4_rows = [('Belum Bayar', '=COUNTIF(\'Budget & Bayar\'!$L$15:$L$19,"Belum Bayar")'),
                     ('DP 30% Terbayar', '=COUNTIF(\'Budget & Bayar\'!$L$15:$L$19,"DP 30% Terbayar")'),
                     ('Mid-Term 40%', '=COUNTIF(\'Budget & Bayar\'!$L$15:$L$19,"Mid-Term 40% Terbayar")'),
                     ('Lunas', '=COUNTIF(\'Budget & Bayar\'!$L$15:$L$19,"Lunas")')]
    elif _slug == 'exhibition':
        _ch4_title = 'KESIAPAN LOGISTIK & PERLENGKAPAN'
        _n_log = len(planner_master['logistics'])
        _lend = 6 + _n_log
        _ch4_rows = [('Siap', f'=COUNTIF(\'Daftar Barang\'!$F$7:$F${_lend},"Siap")'),
                     ('Dalam Proses', f'=COUNTIF(\'Daftar Barang\'!$F$7:$F${_lend},"Dalam Proses")'),
                     ('Belum Siap', f'=COUNTIF(\'Daftar Barang\'!$F$7:$F${_lend},"Belum Siap")')]
    else:
        _ch4_title = ('PROGRESS TABUNGAN ULANG TAHUN' if _slug == 'birthday'
                       else 'PROGRESS TABUNGAN ACARA')
        _ch4_rows = [('Terkumpul', '=Tabungan!C4'),
                     ('Sisa Kurang', '=Tabungan!B8')]
    dash.merge_cells("Q19:R19")
    dash["Q19"] = f"{_ch4_title} (BANTUAN GRAFIK)"
    dash["Q19"].font = Font(name="Calibri", size=8, bold=True, color="4B4F72")
    dash["Q19"].fill = kpi_card_fill
    dash["Q19"].alignment = Alignment(horizontal="left", vertical="center")
    dash.row_dimensions[19].height = 15
    _ch4_start = 20
    for _k, (_lbl, _f) in enumerate(_ch4_rows):
        _r = _ch4_start + _k
        dash.cell(row=_r, column=17, value=_lbl).font = Font(name="Calibri", size=9)
        dash.cell(row=_r, column=17).fill = soft_gray
        dash.cell(row=_r, column=17).alignment = Alignment(horizontal="left", vertical="center")
        c = dash.cell(row=_r, column=18, value=_f)
        c.number_format = '0'
        c.font = Font(name="Calibri", size=11)
        c.alignment = Alignment(horizontal="center", vertical="center")
        dash.row_dimensions[_r].height = 15
    _ch4_end = _ch4_start + len(_ch4_rows) - 1
    ch4 = DoughnutChart()
    ch4.title = _ch4_title
    ch4.height = 7.5
    ch4.width = 15
    ch4.legend.position = "r"
    ch4.add_data(Reference(dash, min_col=18, min_row=19, max_row=_ch4_end), titles_from_data=True)
    ch4.set_categories(Reference(dash, min_col=17, min_row=_ch4_start, max_row=_ch4_end))
    ch4.series[0].tx = SeriesLabel(v="Jumlah")
    ch4.series[0].graphicalProperties.solidFill = "4F81BD"
    ch4.series[0].graphicalProperties.line.noFill = True
    ch4.series[0].dLbls = DataLabelList()
    ch4.series[0].dLbls.showPercent = True
    ch4.series[0].dLbls.showCatName = True
    ch4.series[0].dLbls.showLeaderLines = True
    dash.add_chart(ch4, "H32")

    # Mirror table: per-category status pulled live from Budget & Bayar.
    dash.merge_cells("A50:N50")
    dash["A50"] = "STATUS PER KATEGORI ANGGARAN"
    dash["A50"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    dash["A50"].fill = berry_fill
    dash["A50"].alignment = Alignment(horizontal="center", vertical="center")
    dash.row_dimensions[50].height = 19.5
    _dheads = [("A51", "No.", 1, 1), ("B51:E51", "Kategori Pengeluaran", 2, 5),
               ("F51:G51", "Target Anggaran (Rp)", 6, 7), ("H51:I51", "Realisasi Kontrak (Rp)", 8, 9),
               ("J51:K51", "Status Efisiensi", 10, 11), ("L51:N51", "Status Pembayaran", 12, 14)]
    for _rng, _txt, _c0, _c1 in _dheads:
        dash.merge_cells(_rng)
        h = dash[_rng.split(":")[0]]
        h.value = _txt
        h.font = font_white_bold
        h.fill = navy_fill
        h.alignment = Alignment(horizontal="center", vertical="center")
        for _c in range(_c0, _c1 + 1):
            dash.cell(row=51, column=_c).border = thin_border
    dash.row_dimensions[51].height = 15
    for _i in range(5):
        _r = 52 + _i
        _src = 15 + _i
        dash.cell(row=_r, column=1, value=f"='Budget & Bayar'!A{_src}").alignment = Alignment(horizontal="center", vertical="center")
        dash.cell(row=_r, column=1).number_format = '0'
        dash.merge_cells(f"B{_r}:E{_r}")
        dash.cell(row=_r, column=2, value=f"='Budget & Bayar'!B{_src}").alignment = Alignment(horizontal="left", vertical="center")
        dash.merge_cells(f"F{_r}:G{_r}")
        c = dash.cell(row=_r, column=6, value=f"='Budget & Bayar'!D{_src}")
        c.number_format = '"Rp " #,##0'
        c.alignment = Alignment(horizontal="center", vertical="center")
        dash.merge_cells(f"H{_r}:I{_r}")
        c = dash.cell(row=_r, column=8, value=f"='Budget & Bayar'!F{_src}")
        c.number_format = '"Rp " #,##0'
        c.alignment = Alignment(horizontal="center", vertical="center")
        dash.merge_cells(f"J{_r}:K{_r}")
        dash.cell(row=_r, column=10, value=f"='Budget & Bayar'!H{_src}").alignment = Alignment(horizontal="left", vertical="center")
        dash.merge_cells(f"L{_r}:N{_r}")
        dash.cell(row=_r, column=12, value=f"='Budget & Bayar'!L{_src}").alignment = Alignment(horizontal="left", vertical="center")
        for _c in range(1, 15):
            cell = dash.cell(row=_r, column=_c)
            cell.font = Font(name="Calibri", size=11)
            cell.fill = soft_gray
            cell.border = thin_border
        dash.row_dimensions[_r].height = 15
    dash.conditional_formatting.add("J52:K56", CellIsRule(operator="equal", formula=['"Lunas"'], fill=accent_green, font=cf_green_font))
    dash.conditional_formatting.add("L52:N56", CellIsRule(operator="equal", formula=['"Lunas"'], fill=accent_green, font=cf_green_font))

    dash.column_dimensions["A"].width = 14
    dash.column_dimensions["E"].width = 4
    dash.column_dimensions["F"].width = 14
    dash.column_dimensions["J"].width = 4
    dash.column_dimensions["K"].width = 14
    dash.column_dimensions["P"].width = 2
    dash.column_dimensions["Q"].width = 20
    dash.column_dimensions["R"].width = 12

    # Metadata kepemilikan: tercatat di properti file (File > Info) atas nama pembuat.
    import datetime as _dt
    wb.properties.creator = "Adrian Muhamad Ghofur"
    wb.properties.lastModifiedBy = "Adrian Muhamad Ghofur"
    wb.properties.title = f"Vendoraman Master Planner - {plan.title}"
    wb.properties.subject = f"Template perencana acara ({plan.event_category.name if plan.event_category else 'Event'})"
    wb.properties.description = ("Dibuat dan dimiliki oleh Adrian Muhamad Ghofur. "
                                 "Dilarang menggandakan atau menjual ulang tanpa izin tertulis.")
    wb.properties.keywords = "Vendoraman, event planner, Adrian Muhamad Ghofur"
    wb.properties.category = "Event Planner Template"
    wb.properties.company = "Vendoraman"
    wb.properties.created = _dt.datetime.now()

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and footers with slide numbers to ReportLab landscape pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress on cover slide
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4B4F72"))
        # Top banner line
        self.setStrokeColor(colors.HexColor("#E4DDD0"))
        self.setLineWidth(0.5)
        self.line(40, 555, 802, 555)
        self.drawString(40, 562, "VENDORAMAN — EXECUTIVE EVENT PROPOSAL & PLANNER DECK")
        
        # Bottom footer
        self.line(40, 45, 802, 45)
        self.drawString(40, 32, "Protected by Vendoraman Escrow & Financial Guarantee")
        self.drawRightString(802, 32, f"Slide {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_planner_pdf_deck(plan, vendors, budget_allocations):
    """
    Generates a 16:9 Landscape Executive Presentation Deck (PDF)
    Using ReportLab, designed for presentation to stakeholders, clients, or family elders.
    """
    buffer = io.BytesIO()
    
    # Standard A4 Landscape: 842 x 595 points
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50,
        author="Adrian Muhamad Ghofur",
        title=f"Vendoraman Master Plan - {plan.title}",
        subject="Template perencana acara Vendoraman (dibuat dan dimiliki oleh Adrian Muhamad Ghofur)",
        keywords="Vendoraman, event planner, Adrian Muhamad Ghofur",
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Typography
    title_style = ParagraphStyle(
        'CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor('#1B1F3B'),
        alignment=1, # Center
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#4B4F72'),
        alignment=1,
        spaceAfter=20
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1B1F3B'),
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'BodyDark',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1B1F3B')
    )
    body_bold = ParagraphStyle(
        'BodyDarkBold',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1B1F3B')
    )
    badge_style = ParagraphStyle(
        'BadgeGold',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#B9852B'),
        alignment=1
    )

    story = []

    # -------------------------------------------------------------
    # SLIDE 1: COVER SLIDE
    # -------------------------------------------------------------
    story.append(Spacer(1, 60))
    story.append(Paragraph("V E N D O R A M A", ParagraphStyle('SubBrand', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#D9A441'), alignment=1, spaceAfter=8)))
    story.append(Paragraph(f"Executive Event Proposal & Master Plan<br/><b>{plan.title}</b>", title_style))
    story.append(Paragraph(f"Disusun secara komprehensif untuk {plan.customer.get_full_name() or plan.customer.username} &bull; {plan.city}", subtitle_style))
    story.append(Spacer(1, 20))

    # Event Specs Box on Cover
    cover_data = [
        [
            Paragraph(f"<b>Kategori Acara</b><br/>{plan.event_category.name if plan.event_category else 'Event'}", body_style),
            Paragraph(f"<b>Tanggal Acara</b><br/>{plan.event_date.strftime('%d %B %Y')}", body_style),
            Paragraph(f"<b>Jumlah Tamu</b><br/>{plan.estimated_pax} Tamu (Pax)", body_style),
            Paragraph(f"<b>Pagu Anggaran</b><br/>Rp {intdot(plan.budget_min)} – {intdot(plan.budget_max)}", body_style)
        ]
    ]
    t_cover = Table(cover_data, colWidths=[185, 185, 185, 185])
    t_cover.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAF6')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4DDD0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4DDD0')),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(t_cover)
    story.append(Spacer(1, 40))
    story.append(Paragraph("TERVERIFIKASI PLATFORM &bull; GARANSI KEUANGAN ESCROW &bull; DILINDUNGI PENUH", ParagraphStyle('CoverBadge', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#5C7A5E'), alignment=1)))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 2: STRATEGIC BUDGET BREAKDOWN
    # -------------------------------------------------------------
    story.append(Paragraph("Alokasi Strategis Anggaran Acara", section_heading))
    story.append(Paragraph(f"Distribusi pembiayaan berbasis standar industri untuk memastikan efisiensi optimal pada plafon pagu anggaran <b>Rp {intdot(plan.budget_max)}</b>.", body_style))
    story.append(Spacer(1, 16))

    budget_table_data = [
        [
            Paragraph("<b>Komponen Pengeluaran</b>", body_bold),
            Paragraph("<b>Alokasi</b>", body_bold),
            Paragraph("<b>Rekomendasi Biaya (Rp)</b>", body_bold),
            Paragraph("<b>Panduan Manajemen Biaya</b>", body_bold)
        ]
    ]

    total_budget = float(plan.budget_max)
    budget_specs = [
        ("Catering & Jamuan Makanan", "40%", round(total_budget * 0.40), "Fokus pada porsi buffet aman + stall favorit tamu"),
        ("Dekorasi, Pelaminan & Ambience", "30%", round(total_budget * 0.30), "Titik fokus panggung, pelaminan, photobooth & lighting"),
        ("Dokumentasi (Foto & Video Cinematic)", "15%", round(total_budget * 0.15), "Dokumentasi momen penting, teaser 1 menit & all unedited files"),
        ("Sound System, Akustik Band & MC", "15%", round(total_budget * 0.15), "Pengisi suasana ramah tamah, pemandu acara & kejelasan audio")
    ]

    for item in budget_specs:
        budget_table_data.append([
            Paragraph(item[0], body_style),
            Paragraph(item[1], body_bold),
            Paragraph(f"Rp {intdot(item[2])}", body_bold),
            Paragraph(item[3], body_style),
        ])

    budget_table_data.append([
        Paragraph("<b>TOTAL PAGU ANGGARAN</b>", body_bold),
        Paragraph("<b>100%</b>", body_bold),
        Paragraph(f"<b>Rp {intdot(total_budget)}</b>", body_bold),
        Paragraph("<b>100% Dana Diamankan dengan Skema Escrow</b>", ParagraphStyle('Gre', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#059669'))),
    ])

    t_budget = Table(budget_table_data, colWidths=[220, 80, 160, 280])
    t_budget.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B1F3B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4DDD0')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F8FAF6')),
    ]))
    story.append(t_budget)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Keamanan Transaksi:</b> Dana Anda tidak ditransfer langsung ke vendor, melainkan disimpan dalam platform escrow dan dicairkan bertahap (DP 30%, Mid-Term 40%, Pelunasan 30% H+1 selesai acara).", ParagraphStyle('FootNote', fontName='Helvetica-Oblique', fontSize=9, textColor=colors.HexColor('#4B4F72'))))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 3+: VENDOR SHOWCASE CARDS (Grouped 2 per slide)
    # -------------------------------------------------------------
    vendor_chunk_size = 2
    for chunk_idx in range(0, len(vendors), vendor_chunk_size):
        chunk = vendors[chunk_idx:chunk_idx + vendor_chunk_size]
        story.append(Paragraph(f"Rekomendasi Vendor Terkurasi & Kontak PIC (Bagian {chunk_idx // vendor_chunk_size + 1})", section_heading))
        story.append(Paragraph("Seluruh identitas resmi, nomor WhatsApp PIC, dan paket penawaran telah dibuka penuh untuk pemegang Paid Planner.", body_style))
        story.append(Spacer(1, 14))

        for vendor in chunk:
            pkg = vendor.packages.first()
            specs_text = "<br/>".join([f"&bull; {s}" for s in (pkg.get_spec_list()[:3] if pkg else ["Penawaran paket fleksibel"])])
            
            starting_price = float(pkg.price) if pkg else 0
            card_data = [
                [
                    Paragraph(f"<b>{vendor.business_name}</b><br/><font color='#4B4F72'>{vendor.category.name if vendor.category else 'Vendor'} &bull; {vendor.city}</font>", ParagraphStyle('VTitle', fontName='Helvetica-Bold', fontSize=13, leading=16)),
                    Paragraph(f"<b>Rating: {vendor.rating} / 5.0</b><br/><font color='#5C7A5E'>{vendor.total_completed_events} Event Selesai &bull; Vetted Partner</font>", ParagraphStyle('VRate', fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=2))
                ],
                [
                    Paragraph(f"<b>Profil:</b> {vendor.description[:180]}...", body_style),
                    Paragraph(f"<b>Paket Terpilih:</b> {pkg.name if pkg else 'Custom'}<br/><b>Mulai:</b> Rp {intdot(starting_price)}<br/>{specs_text}", body_style)
                ],
                [
                    Paragraph(f"<b>Kontak PIC:</b> {vendor.pic_name} &nbsp;|&nbsp; <b>WhatsApp / Telp:</b> <font color='#B23A5D'><b>{vendor.contact_phone}</b></font>", body_bold),
                    Paragraph(f"<b>Alamat:</b> {vendor.address or vendor.city}", body_style)
                ]
            ]
            t_card = Table(card_data, colWidths=[460, 280])
            t_card.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D0D5DD')),
                ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#E4DDD0')),
                ('LINEBELOW', (0,1), (-1,1), 0.5, colors.HexColor('#E4DDD0')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(t_card)
            story.append(Spacer(1, 14))

        story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE: TARGET DEADLINE (BULANAN, MINGGUAN & HARIAN)
    # -------------------------------------------------------------
    story.append(Paragraph("Target Deadline Persiapan: Bulanan, Mingguan & Harian", section_heading))
    story.append(Paragraph("Dekomposisi tahapan operasional untuk memastikan nol risiko kelalaian dan koordinasi vendor presisi:", body_style))
    story.append(Spacer(1, 14))

    deadline_grid = [
        [
            Paragraph("<b>TARGET BULANAN (STRATEGIS)</b><br/><font color='#D9A441'><b>H-6 s/d H-2 Menuju Hari-H</b></font>", ParagraphStyle('HCol1', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1B1F3B'))),
            Paragraph("<b>TARGET MINGGUAN (SPRINT)</b><br/><font color='#D9A441'><b>W-4 s/d W-1 Menuju Hari-H</b></font>", ParagraphStyle('HCol2', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1B1F3B'))),
            Paragraph("<b>TARGET HARIAN (OPERASIONAL)</b><br/><font color='#B23A5D'><b>H-7 s/d H-1 & Hari-H</b></font>", ParagraphStyle('HCol3', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1B1F3B'))),
        ],
        [
            Paragraph(
                "&bull; <b>H-6:</b> Anggaran & target pax fix<br/>"
                "&bull; <b>H-5:</b> Kunci venue & katering (DP 30%)<br/>"
                "&bull; <b>H-4:</b> Booking dekorasi & foto/video<br/>"
                "&bull; <b>H-3:</b> Fitting busana 1 & booking MC<br/>"
                "&bull; <b>H-2:</b> Cetak undangan & pesan souvenir",
                body_style
            ),
            Paragraph(
                "&bull; <b>W-4:</b> Technical Meeting (TM) seluruh vendor<br/>"
                "&bull; <b>W-3:</b> Sebar undangan & rekap RSVP tamu<br/>"
                "&bull; <b>W-2:</b> Kunci jumlah porsi katering (+10%)<br/>"
                "&bull; <b>W-1:</b> Master rundown fix & izin keamanan",
                body_style
            ),
            Paragraph(
                "&bull; <b>H-7:</b> Readiness check seluruh vendor<br/>"
                "&bull; <b>H-4:</b> Pengecekan bukti siap vendor<br/>"
                "&bull; <b>H-3:</b> Pencairan Mid-Term Escrow 40%<br/>"
                "&bull; <b>H-2:</b> Gladi resik & test sound system<br/>"
                "&bull; <b>H-1:</b> Loading dekorasi & briefing malam<br/>"
                "&bull; <b>Hari-H:</b> Eksekusi rundown per jam",
                body_style
            ),
        ]
    ]
    t_deadlines = Table(deadline_grid, colWidths=[246, 246, 248])
    t_deadlines.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAF6')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#D0D5DD')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4DDD0')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_deadlines)
    story.append(Spacer(1, 14))
    story.append(Paragraph("<b>Fitur Excel Master:</b> Lembar kerja 'Jadwal & Rundown' di file Excel menyertakan tabel checklist interaktif lengkap dengan kolom PIC, nomor WhatsApp, status verifikasi, dan audio cue.", ParagraphStyle('NoteD', fontName='Helvetica-Oblique', fontSize=9, textColor=colors.HexColor('#4B4F72'))))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE: TABUNGAN ACARA (Savings Vault progress)
    # -------------------------------------------------------------
    story.append(Paragraph("Tabungan Acara: Target & Sudah Terkumpul", section_heading))
    _vault = None
    try:
        _vault = getattr(plan, 'savings_vault', None)
        if _vault is None:
            _vault = plan.customer.savings_vaults.order_by('-created_at').first()
    except Exception:
        _vault = None
    if _vault is not None:
        _target = float(_vault.target_amount or 0)
        _current = float(_vault.current_amount or 0)
        _pct = round((_current / _target * 100), 1) if _target else 0
        _remain = max(_target - _current, 0)
        story.append(Paragraph(
            f"<b>{_vault.title}</b> &bull; Target tanggal {_vault.target_date} &bull; "
            f"Target <b>Rp {intdot(_target)}</b> &bull; Sudah terkumpul <b>Rp {intdot(_current)}</b> "
            f"({_pct}%) &bull; Sisa <b>Rp {intdot(_remain)}</b>.",
            body_style,
        ))
        story.append(Spacer(1, 14))
        _dep_data = [
            [
                Paragraph("<b>No.</b>", body_bold),
                Paragraph("<b>Tanggal</b>", body_bold),
                Paragraph("<b>Jumlah (Rp)</b>", body_bold),
                Paragraph("<b>Catatan</b>", body_bold),
            ]
        ]
        for i, dep in enumerate(_vault.deposits.all().order_by('created_at')[:12], start=1):
            _dep_data.append([
                Paragraph(str(i), body_style),
                Paragraph(dep.created_at.strftime("%d %b %Y") if dep.created_at else "-", body_style),
                Paragraph(f"Rp {intdot(float(dep.amount or 0))}", body_bold),
                Paragraph(dep.notes or "-", body_style),
            ])
        if len(_dep_data) == 1:
            _dep_data.append([
                Paragraph("-", body_style),
                Paragraph("-", body_style),
                Paragraph("-", body_style),
                Paragraph("Belum ada setoran. Tambah dari halaman Tabungan di aplikasi.", body_style),
            ])
        t_dep = Table(_dep_data, colWidths=[50, 130, 170, 390])
        t_dep.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B1F3B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4DDD0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(t_dep)
        story.append(Spacer(1, 12))
        story.append(Paragraph("Rincian lengkap + rumus otomatis ada di sheet 'Tabungan' file Excel.", ParagraphStyle('NoteS', fontName='Helvetica-Oblique', fontSize=9, textColor=colors.HexColor('#4B4F72'))))
    else:
        story.append(Paragraph("Belum ada tabungan untuk rencana ini. Buka halaman Tabungan di aplikasi, buat tabungan baru, lalu setor sedikit demi sedikit. Unduh ulang file ini setelah ada setoran dan riwayatnya akan muncul otomatis di sini dan di sheet 'Tabungan' Excel.", body_style))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE FINAL: TIMELINE ROADMAP & NEXT STEPS
    # -------------------------------------------------------------
    story.append(Paragraph("Roadmap Eksekusi & Langkah Selanjutnya", section_heading))
    story.append(Paragraph("Panduan tahapan koordinasi terstruktur dari penguncian vendor hingga hari pelaksanaan acara:", body_style))
    story.append(Spacer(1, 14))

    roadmap_data = [
        [
            Paragraph("<b>Tahap 1: Booking & DP Escrow</b>", body_bold),
            Paragraph("Pilih paket vendor resmi, transfer DP 30% ke Platform Escrow Vendoraman. Tanggal acara Anda terkunci resmi.", body_style)
        ],
        [
            Paragraph("<b>Tahap 2: Technical Meeting</b>", body_bold),
            Paragraph("Lakukan koordinasi langsung dengan PIC vendor via WhatsApp/tatap muka. Sesuaikan detail rundown dan spesifikasi.", body_style)
        ],
        [
            Paragraph("<b>Tahap 3: H-3 Readiness Check & Mid-Term</b>", body_bold),
            Paragraph("Vendor mengonfirmasi kesiapan deliverables. Platform mencairkan milestone ke-2 (40%) untuk persiapan akhir.", body_style)
        ],
        [
            Paragraph("<b>Tahap 4: Hari-H & Konfirmasi Selesai</b>", body_bold),
            Paragraph("Acara berjalan lancar sesuai rundown. Setelah Anda puas dan konfirmasi di platform, dana sisa 30% dicairkan ke vendor.", body_style)
        ]
    ]
    t_road = Table(roadmap_data, colWidths=[220, 520])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAF6')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4DDD0')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(t_road)
    story.append(Spacer(1, 24))

    closing_box = [
        [
            Paragraph("<b>Butuh Bantuan Konsultasi Khusus?</b> Hubungi Concierge Planner Vendoraman di <font color='#B23A5D'>support@vendoraman.id</font> atau langsung hubungi PIC vendor pada direktori di atas.", body_style)
        ]
    ]
    t_close = Table(closing_box, colWidths=[740])
    t_close.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E1E9DE')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#5C7A5E')),
        ('PADDING', (0,0), (-1,-1), 14),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_close)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
