import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import F

from .models import EventCategory, VendorProfile, CustomUser, EventPlan, TemplateDownloadCode, TemplateDownloadLog
from .services_export import generate_planner_excel


CATEGORY_DESCRIPTIONS = {
    'wedding': {
        'headline': 'Template Excel Wedding Planner & Resepsi Lengkap',
        'subheadline': 'Panduan perencanaan pernikahan terstruktur dari lamaran, akad, hingga resepsi. Rumus otomatis anti-boncos dan kalkulator porsi katering.',
        'target_audience': 'Calon Pengantin, Keluarga Besar & Wedding Organizer (WO)',
        'estimated_savings': 'Hemat s/d Rp 15 - 30 Juta dari alokasi budget presisi',
        'key_perks': [
            'Kalkulator Porsi Katering Cerdas (Buffet 60% vs Stall 40% + 10% buffer)',
            'Checklist Berjangka H-90, H-60, H-30, H-7 hingga Hari-H',
            'Rundown Menit-demi-Menit Akad & Resepsi dengan PIC Terperinci',
            'Matriks Perbandingan Vendor Venue, Dekor, Foto & MUA',
            'Formula Kontrol Arus Kas DP, Pelunasan & Rekonsiliasi Realisasi'
        ]
    },
    'corporate': {
        'headline': 'Template Excel Corporate Gathering & Annual Meeting',
        'subheadline': 'Standar manajemen event profesional untuk HR, Event Committee kantor, dan Corporate Event Organizer. Dilengkapi perhitungan Cost Per Pax.',
        'target_audience': 'Panitia Kantor, Divisi HR / GA & Corporate EO',
        'estimated_savings': 'Kontrol deviasi anggaran kantor di bawah toleransi 5%',
        'key_perks': [
            'Simulasi Cost per Employee / Pax dengan batas pagu anggaran',
            'Timeline Koordinasi Vendor Stage, Rigging, LED Videotron & Audio',
            'Rundown Acara Formal & Hiburan Karyawan per sesi menit',
            'Logistik Souvenir, Transportasi Bus, Rooming List & Doorprize',
            'Dashboard Rekapitulasi Realisasi untuk Laporan Pertanggungjawaban (LPJ)'
        ]
    },
    'birthday': {
        'headline': 'Template Excel Birthday Party & Sweet 17 Celebration',
        'subheadline': 'Manajemen pesta ulang tahun meriah tanpa drama overbudget. Dari pemilihan venue cafe/ballroom, kue, photobooth, hingga susunan games.',
        'target_audience': 'Penyelenggara Pesta, Orang Tua, Sweet 17 Organizer',
        'estimated_savings': 'Mencegah pemborosan pernak-pernik dan katering berlebih',
        'key_perks': [
            'Checklist Pemesanan Kue Ulang Tahun, Dessert Table & Backdrop Balon',
            'Kalkulator Pax Makanan Utama & Kids/Youth Snack Corner',
            'Rundown Candle Lighting, Special Performance & Pembagian Goodie Bag',
            'Daftar Tamu VIP, Teman Sekolah/Kampus & Konfirmasi RSVP',
            'Pencatatan Anggaran Dekorasi Tematik & MC/DJ'
        ]
    },
    'exhibition': {
        'headline': 'Template Excel Exhibition, Bazaar & Festival Planner',
        'subheadline': 'Sistem kendali terpadu untuk bazar multi-tenant, festival musik/kuliner, dan pameran dagang. Manajemen booth, layout, dan perizinan.',
        'target_audience': 'Panitia Festival, EO Bazar, Pengelola Mall/Venue',
        'estimated_savings': 'Maksimalkan occupancy rate booth dan arus kas fee tenant',
        'key_perks': [
            'Daftar Plotting Booth, Ukuran Kavling & Status Pembayaran Tenant',
            'Tracking Perizinan Keramaian, Damkar, Keamanan & Satpol PP',
            'Jadwal Loading In & Loading Out Tenant per blok waktu',
            'Anggaran Kebersihan, Keamanan, Genset & Sound System',
            'Rekapitulasi Tiket Masuk & Estimasi Traffic Pengunjung'
        ]
    },
    'seminar': {
        'headline': 'Template Excel Seminar, Workshop & Conference Planner',
        'subheadline': 'Perencanaan konferensi edukatif dan workshop teknis. Kelola registrasi peserta, seminar kit, akomodasi pembicara, dan sertifikat.',
        'target_audience': 'Lembaga Pelatihan, Kampus, Komunitas & Event Organizer',
        'estimated_savings': 'Presisi alokasi seminar kit dan konsumsi per sesi',
        'key_perks': [
            'Rundown Keynote Speaker, Breakout Session & Tanya Jawab Interaktif',
            'Tracking Honorarium, Transport & Hospitality Pembicara/Instruktur',
            'Kalkulator Coffee Break (Pagi/Sore) & Makan Siang Peserta',
            'Checklist Pengadaan Sertifikat, Modul Cetak & Merchandise',
            'Evaluasi Feedback Peserta & Rekap Kehadiran'
        ]
    },
    'intimate': {
        'headline': 'Template Excel Intimate Gathering & Lamaran Planner',
        'subheadline': 'Solusi praktis acara hangat berkesan untuk lamaran keluarga, private dinner, aqiqah, dan syukuran intim di rumah atau restoran.',
        'target_audience': 'Keluarga, Pasangan Lamaran, Host Acara Personal',
        'estimated_savings': 'Efisiensi paket set-menu dan dekorasi minimalis elegan',
        'key_perks': [
            'Rundown Prosesi Seserahan & Perkenalan Dua Keluarga',
            'Hitung Porsi Menu Family-Style / Set Menu Restoran',
            'Checklist Daftar Hantaran, Kotak Cincin & Busana Keluarga',
            'Budgeting Fotografer Dokumentasi & Sound System Ringkas',
            'Daftar Konfirmasi Kehadiran Tamu Inti'
        ]
    }
}


def _get_category_info(category):
    slug = category.slug.lower()
    return CATEGORY_DESCRIPTIONS.get(slug, {
        'headline': f'Template Excel Perencanaan {category.name}',
        'subheadline': f'Sistem template Excel berformula cerdas dan terstruktur untuk event {category.name}.',
        'target_audience': 'Penyelenggara Acara & Tim Panitia',
        'estimated_savings': 'Efisiensi alokasi pos anggaran',
        'key_perks': [
            'Formula Otomatis Perhitungan Budget & Varians',
            'Direktori Vendor Terkurasi Kategori',
            'Timeline & Rundown Hari-H Lengkap',
            'Simulasi Kebutuhan Katering & Logistik',
            'Master Checklist Perlengkapan Acara'
        ]
    })


def excel_templates_catalog_view(request):
    """Katalog publik seluruh koleksi template Excel event Vendoraman."""
    categories = EventCategory.objects.all().order_by('name')
    categories_data = []
    for cat in categories:
        info = _get_category_info(cat)
        categories_data.append({
            'category': cat,
            'info': info,
        })

    return render(request, 'excel/catalog.html', {
        'categories_data': categories_data,
    })


def excel_template_category_view(request, category_slug):
    """Halaman landing page detail per kategori Excel dengan form unduh kode unik."""
    category = get_object_or_404(EventCategory, slug=category_slug)
    info = _get_category_info(category)
    other_categories = EventCategory.objects.exclude(id=category.id).order_by('name')

    return render(request, 'excel/category_detail.html', {
        'category': category,
        'info': info,
        'other_categories': other_categories,
    })


@require_POST
def excel_template_download_action(request, category_slug):
    """Validasi kode unik dan eksekusi pengunduhan file Excel tanpa login."""
    category = get_object_or_404(EventCategory, slug=category_slug)
    code_raw = request.POST.get('code', '').strip()
    email_raw = request.POST.get('email', '').strip().lower()

    if not code_raw:
        messages.error(request, 'Silakan masukkan kode unik yang Anda terima dari Shopee.')
        return redirect('excel_template_category', category_slug=category.slug)

    code_obj = TemplateDownloadCode.objects.filter(code__iexact=code_raw).first()
    if not code_obj:
        messages.error(
            request,
            f'Kode unik "{code_raw}" tidak ditemukan. Pastikan Anda menyalin kode dengan benar sesuai chat/catatan pesanan Shopee.'
        )
        return redirect('excel_template_category', category_slug=category.slug)

    # Validasi kesesuaian kategori, kuota pemakaian, dan status aktif
    is_valid, error_msg = code_obj.is_valid_for(category)
    if not is_valid:
        messages.error(request, error_msg)
        return redirect('excel_template_category', category_slug=category.slug)

    # 1. Update quota pemakaian secara atomik
    TemplateDownloadCode.objects.filter(pk=code_obj.pk).update(used_count=F('used_count') + 1)

    # 2. Catat audit trail pengunduhan
    ip_header = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = ip_header.split(',')[0].strip() if ip_header else request.META.get('REMOTE_ADDR')
    ua = request.META.get('HTTP_USER_AGENT', '')
    TemplateDownloadLog.objects.create(
        download_code=code_obj,
        event_category=category,
        email=email_raw,
        ip_address=ip if ip else None,
        user_agent=ua[:500] if ua else ''
    )

    # 3. Generate file Excel OpenXML (.xlsx) dengan mode vendor basic
    dummy_user = CustomUser(username='shopee_guest')
    dummy_plan = EventPlan(
        customer=dummy_user,
        title=f'Master Planner {category.name}',
        event_category=category,
        event_date=datetime.date.today() + datetime.timedelta(days=90),
        city='Jakarta',
        estimated_pax=150,
        budget_min=25000000,
        budget_max=100000000,
        selected_services=[],
    )

    vendors = list(VendorProfile.objects.filter(
        category=category,
        verification_status='APPROVED',
        is_vetted=True
    ).select_related('category', 'user').prefetch_related('packages'))

    excel_bytes = generate_planner_excel(dummy_plan, vendors, {}, vendor_mode='basic')

    response = HttpResponse(
        excel_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Vendoraman_Template_{category.slug}.xlsx"'
    return response
