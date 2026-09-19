from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Count, Min, Max
from .models import EventCategory, VendorProfile, VendorPackage, EventPlan, PlannerAccess
from .templatetags.currency_tags import intdot


def home_view(request):
    # 1. Categories with dynamic vendor count & price ranges
    categories = EventCategory.objects.annotate(
        v_count=Count('vendors', distinct=True),
        min_price=Min('vendors__packages__price'),
        max_price=Max('vendors__packages__price')
    ).order_by('-v_count')

    # 2. City Coverage Statistics
    city_list = VendorProfile.objects.values('city').annotate(
        v_count=Count('id')
    ).order_by('-v_count')

    city_details = {
        'Jakarta': {'region': 'Jabodetabek', 'desc': 'Ballroom hotel bintang lima, catering megah, dan wedding organizer berlisensi.'},
        'Bandung': {'region': 'Jawa Barat', 'desc': 'Spesialis wedding outdoor, venue villa sejuk, dan dekorasi rustic botani.'},
        'Surabaya': {'region': 'Jawa Timur', 'desc': 'Convention hall skala besar, catering cita rasa nusantara, dan dokumentasi sinematik.'},
        'Yogyakarta': {'region': 'DIY & Solo', 'desc': 'Resepsi adat keraton, intimate garden party, dan seniman hiburan tradisional-modern.'},
        'Semarang': {'region': 'Jawa Tengah', 'desc': 'Gedung pertemuan strategis, paket pernikahan lengkap, dan corporate gathering.'},
        'Bali': {'region': 'Denpasar & Badung', 'desc': 'Cliffside chapel, sunset beach celebration, dan hospitality luxury kelas dunia.'},
    }

    cities_data = []
    for c in city_list:
        city_name = c['city']
        detail = city_details.get(city_name, {'region': 'Indonesia', 'desc': 'Vendor terkurasi siap melayani kebutuhan acara Anda.'})
        cities_data.append({
            'name': city_name,
            'region': detail['region'],
            'desc': detail['desc'],
            'count': c['v_count'],
        })

    # 3. Overall Package Price Range
    price_aggregate = VendorPackage.objects.aggregate(
        min_p=Min('price'),
        max_p=Max('price')
    )
    min_global_price = price_aggregate['min_p'] or 3500000
    max_global_price = price_aggregate['max_p'] or 120000000

    # 4. Social Proof / Usage Counters
    total_vendors = VendorProfile.objects.count()
    real_unlocked = PlannerAccess.objects.filter(is_unlocked=True).count()
    template_buyers_count = 940 + real_unlocked
    events_planned_count = 1850 + EventPlan.objects.count()

    # 5. Verified Client Reviews
    reviews = [
        {
            'name': 'Andi Pratama & Sarah Meliana',
            'event_type': 'Pernikahan (Wedding) - 600 Pax',
            'city': 'Jakarta & Tangerang',
            'rating': 5,
            'verified': True,
            'avatar_initials': 'AS',
            'color': 'var(--berry)',
            'title': 'Template Excel & Proteksi Escrow Penyelamat Acara Kami!',
            'quote': 'Awalnya pusing mengatur puluhan vendor dan takut ditipu DP. Dengan Vendoraman, semua pembayaran aman dalam 3 milestone escrow. Ditambah lagi, Master Planner Excel-nya menghitung porsi katering dan timeline harian secara otomatis. Kami berhasil hemat Rp 24 juta dari alokasi awal!'
        },
        {
            'name': 'Dian Kusuma, S.Sos',
            'event_type': 'Corporate Gala Dinner - 350 Pax',
            'city': 'Bandung',
            'rating': 5,
            'verified': True,
            'avatar_initials': 'DK',
            'color': 'var(--gold-deep)',
            'title': 'Deck 16:9 Langsung Siap Diajukan ke Direksi',
            'quote': 'Sebagai HR & Event Lead, saya butuh approval cepat dari jajaran direksi. Executive Presentation Deck dari Vendoraman sangat profesional, lengkap dengan pembagian anggaran dan SLA vendor. Tim videotron dan ballroom di Bandung sangat tepat waktu dan memuaskan.'
        },
        {
            'name': 'Bima Satria & Kirana Larasati',
            'event_type': 'Intimate Cliffside Wedding - 150 Pax',
            'city': 'Bali',
            'rating': 5,
            'verified': True,
            'avatar_initials': 'BK',
            'color': 'var(--sage)',
            'title': 'Koordinasi Jarak Jauh Sangat Mudah & Transparan',
            'quote': 'Kami tinggal di Surabaya tapi ingin intimate wedding di Uluwatu, Bali. Fitur WhatsApp unmasked di Paid Planner membuat kami bisa chat langsung dengan PIC resmi vendor, tanpa ada mark-up sepeserpun dari harga asli. Layanan terbaik!'
        },
        {
            'name': 'Clarissa Wijaya & Ibu Linda',
            'event_type': 'Sweet 17th Birthday - 200 Pax',
            'city': 'Surabaya',
            'rating': 5,
            'verified': True,
            'avatar_initials': 'CW',
            'color': 'var(--berry)',
            'title': 'Simulasi Katering & Rundown Sangat Akurat',
            'quote': 'Kalkulator katering di web membagi porsi prasmanan dan stall 60:40 dengan pas, makanan cukup tidak kurang dan tidak mubazir. Checklist 20 logistik di template juga membuat panitia keluarga tenang saat hari H. Recommended banget!'
        },
    ]

    # 6. Frequently Asked Questions (FAQ)
    faqs = [
        {
            'q': 'Apa itu Vendoraman dan apa bedanya dengan direktori vendor biasa?',
            'a': 'Vendoraman bukan sekadar direktori daftar kontak biasa. Kami adalah curated marketplace dengan kurasi mutu ketat, sistem pembayaran bergaransi Milestone Escrow, dan alat perencanaan interaktif (Web Dashboard, Excel otomatis 5-sheet, dan Presentation Deck PDF 16:9). Anda mendapatkan harga murni dari vendor tanpa mark-up sepihak, serta garansi 100% uang kembali jika terjadi wanprestasi.'
        },
        {
            'q': 'Berapa jumlah vendor yang terdaftar dan kategori apa saja yang tersedia?',
            'a': f'Saat ini Vendoraman memiliki {total_vendors}+ vendor terkurasi resmi (Vetted Partners) yang terbagi dalam 6 kategori spesialis: Pernikahan/Wedding (11 vendor), Corporate Gathering & Gala (5 vendor), Ulang Tahun & Perayaan (4 vendor), Pameran/Bazaar/Festival (2 vendor), Seminar & Workshop (1 vendor), dan Intimate Gathering (1 vendor).'
        },
        {
            'q': 'Kota mana saja yang saat ini bisa di-cover oleh Vendoraman?',
            'a': 'Kami melayani 6 wilayah metropolitan utama: Jakarta (Jabodetabek), Bandung, Surabaya, Yogyakarta & Solo, Semarang, dan Bali. Setiap kota didukung oleh vendor lokal berlisensi dan perlindungan dana Escrow 100% aktif.'
        },
        {
            'q': 'Berapa rentang harga paket vendor yang tersedia di platform?',
            'a': f'Harga paket vendor sangat fleksibel mulai dari Rp {intdot(min_global_price)} untuk paket seminar atau intimate event, hingga Rp {intdot(max_global_price)} untuk paket pernikahan akbar dan corporate festival skala ribuan tamu. Seluruh rincian fasilitas dan itemized specifications tertulis transparan.'
        },
        {
            'q': 'Bagaimana sistem Milestone Escrow melindungi dana saya?',
            'a': 'Dana Anda tidak langsung ditransfer ke vendor saat pemesanan. Uang disimpan di rekening penampung resmi Vendoraman dan dicairkan bertahap dalam 3 termin: DP 30% untuk mengunci tanggal, 40% pada H-3 setelah konfirmasi kesiapan barang/jasa, dan 30% pelunasan setelah acara selesai sukses dengan persetujuan Anda.'
        },
        {
            'q': 'Berapa orang yang sudah memakai dan membeli Master Planner Template?',
            'a': f'Lebih dari {intdot(events_planned_count)}+ penyelenggara acara telah menyusun perencanaan di platform kami, dan lebih dari {intdot(template_buyers_count)}+ customer telah membeli serta menggunakan paket Paid Master Planner Template untuk mengelola anggaran acara bernilai miliaran rupiah.'
        },
        {
            'q': 'Apa saja yang didapatkan saat membuka / membeli Paid Planner Template?',
            'a': 'Dengan biaya terjangkau Rp 49.000 (sekali bayar per acara), Anda mendapatkan: (1) Nomor WhatsApp & Email PIC resmi seluruh vendor rekomendasi tanpa sensor, (2) Master Spreadsheet Excel (.xlsx) dengan 5 worksheet berformula otomatis dan simulasi katering, (3) Landscape Presentation Deck (.pdf) 16:9 siap diajukan ke keluarga/direksi, dan (4) Akses penuh web dashboard interaktif.'
        },
        {
            'q': 'Apakah customer dikenakan biaya komisi tambahan atau biaya tersembunyi?',
            'a': 'Sama sekali tidak (0% markup customer). Customer membayar harga asli yang ditetapkan oleh vendor. Vendoraman hanya mengenakan komisi platform 10% langsung dari sisi vendor ketika pesanan berhasil diselesaikan.'
        }
    ]

    context = {
        'categories': categories,
        'cities_data': cities_data,
        'min_global_price': min_global_price,
        'max_global_price': max_global_price,
        'total_vendors': total_vendors,
        'template_buyers_count': template_buyers_count,
        'events_planned_count': events_planned_count,
        'reviews': reviews,
        'faqs': faqs,
        'from_free_template': request.GET.get('ref', '') == 'template-gratis',
    }
    return render(request, 'home.html', context)


def trust_guarantee_view(request):
    return render(request, 'trust_guarantee.html')


def privacy_policy_view(request):
    return render(request, 'legal/privacy.html')


def terms_view(request):
    return render(request, 'legal/terms.html')


def robots_txt_view(request):
    from django.http import HttpResponse
    from django.conf import settings
    site = getattr(settings, 'SITE_URL', '')
    lines = ['User-agent: *', 'Allow: /', f'Sitemap: {site}/sitemap.xml']
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')


def _free_template_settings():
    from .models import FreeTemplateSettings
    return FreeTemplateSettings.get()


FREE_TEMPLATE_SESSION_KEY = 'free_template_unlocked'
FREE_TEMPLATE_EMAIL_KEY = 'free_template_email'


def _send_otp_email(email, code):
    from django.core.mail import send_mail
    from django.conf import settings as dj_settings
    send_mail(
        subject=f'Kode verifikasi Vendoraman: {code}',
        message=(f'Halo,\n\nKode verifikasi e-mail Anda untuk mengunduh Template Gratis Vendoraman adalah:\n\n'
                 f'    {code}\n\nKode berlaku 15 menit. Jangan berikan kode ini ke siapa pun.\n\n'
                 f'Salam,\nTim Vendoraman'),
        from_email=getattr(dj_settings, 'DEFAULT_FROM_EMAIL', 'Vendoraman <noreply@vendoraman.id>'),
        recipient_list=[email],
        fail_silently=False,
    )


def _blank_plan(category=None):
    """Transient (unsaved) plan for template downloads.

    Dummy customer (unsaved) so no personal vault data leaks into the file.
    """
    import datetime
    from django.utils import timezone
    from .models import CustomUser, EventPlan
    ghost = CustomUser(username='template')
    return EventPlan(
        customer=ghost,
        title='Template Kosong — isi sendiri',
        event_category=category,
        event_date=timezone.now().date() + datetime.timedelta(days=90),
        city='Jakarta',
        estimated_pax=100,
        budget_min=10000000,
        budget_max=50000000,
        selected_services=[],
    )


def free_template_view(request):
    """Hidden free-template landing page (NOT in nav/footer/sitemap).

    - Requires login (lead recorded automatically from the account).
    - Download = BLANK template (no vendor data at all).
    - Returns 404 unless enabled in Django Admin.
    """
    from django.http import Http404
    from django.contrib import messages
    from django.contrib.auth.decorators import login_required
    from django.db.models import F
    import datetime
    from .forms import VoucherRedeemForm
    from .models import FreeTemplateLead, Voucher, VoucherRedemption

    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), login_url='login')

    cfg = _free_template_settings()
    if not cfg.is_enabled:
        raise Http404('Halaman tidak tersedia.')

    FreeTemplateLead.objects.get_or_create(
        email=(request.user.email or '').strip().lower() or f'{request.user.username}@local',
        defaults={'phone_number': getattr(request.user, 'phone_number', '')})

    redeem_form = VoucherRedeemForm(initial={'email': request.user.email})
    my_subscription = None
    if request.user.is_authenticated:
        for r in VoucherRedemption.objects.filter(user=request.user).order_by('-expires_at')[:1]:
            my_subscription = r

    if request.method == 'POST':
        redeem_form = VoucherRedeemForm(request.POST)
        if redeem_form.is_valid():
            email = redeem_form.cleaned_data['email'].strip().lower()
            code = redeem_form.cleaned_data['code']
            voucher = Voucher.objects.filter(code__iexact=code).first()
            if voucher is None:
                messages.error(request, 'Kode voucher tidak dikenal. Periksa lagi kode dari Shopee.')
            else:
                ok, reason = voucher.is_valid()
                if not ok:
                    messages.error(request, reason)
                elif VoucherRedemption.objects.filter(
                        voucher=voucher, email=email,
                        expires_at__gte=datetime.date.today()).exists():
                    messages.error(request, 'Kode ini sudah dipakai untuk e-mail tersebut dan masih aktif.')
                else:
                    expires = datetime.date.today() + datetime.timedelta(days=voucher.duration_days)
                    VoucherRedemption.objects.create(
                        voucher=voucher, user=request.user, email=email, expires_at=expires)
                    Voucher.objects.filter(pk=voucher.pk).update(used_count=F('used_count') + 1)
                    user = request.user
                    if user.premium_until is None or user.premium_until < expires:
                        user.premium_until = expires
                        user.save(update_fields=['premium_until'])
                    messages.success(
                        request, f'Voucher {voucher.code} aktif! Langganan premium sampai {expires.strftime("%d %B %Y")}.')
                    return redirect(reverse('free_template') + '#langganan')

    return render(request, 'free_template.html', {
        'original_price': cfg.original_price,
        'redeem_form': redeem_form,
        'lead_email': request.user.email,
        'my_subscription': my_subscription,
    })


def free_template_download_view(request):
    """Blank free template. Login required. No payment, no voucher."""
    from django.http import Http404, FileResponse
    from django.contrib.auth.views import redirect_to_login
    from .services_export import generate_planner_excel
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url='login')
    cfg = _free_template_settings()
    if not cfg.is_enabled:
        raise Http404('Halaman tidak tersedia.')
    data = generate_planner_excel(_blank_plan(), [], {}, vendor_mode='none')
    from django.http import HttpResponse
    resp = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="Vendoraman_Template_Gratis_Kosong.xlsx"'
    return resp


def paid_template_view(request):
    """Paid flow: login → premium (voucher) → pick exactly ONE template category."""
    from django.http import Http404
    from django.contrib import messages
    from django.contrib.auth.views import redirect_to_login
    from .models import EventCategory, PaidTemplateDownload
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url='login')
    if not request.user.is_premium():
        messages.info(request, 'Aktifkan voucher langganan dulu untuk membuka template berbayar.')
        return redirect(reverse('free_template') + '#langganan')

    existing = getattr(request.user, 'paid_template', None)
    if request.method == 'POST':
        if existing is not None:
            messages.warning(request, 'Kamu sudah memilih 1 template. Hubungi admin untuk mengganti pilihan.')
            return redirect('paid_template')
        from django.shortcuts import get_object_or_404
        cat = get_object_or_404(EventCategory, id=request.POST.get('category_id'))
        PaidTemplateDownload.objects.create(user=request.user, event_category=cat)
        messages.success(request, f'Template "{cat.name}" dipilih! Klik unduh di bawah.')
        return redirect('paid_template_download')

    categories = EventCategory.objects.all().order_by('name')
    return render(request, 'paid_template.html', {
        'categories': categories,
        'existing': existing,
    })


def paid_template_download_view(request):
    """Download the ONE chosen paid template: vendor list WITHOUT prices/packages/contacts."""
    from django.http import Http404, HttpResponse
    from django.contrib.auth.views import redirect_to_login
    from .models import VendorProfile
    from .services_export import generate_planner_excel
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url='login')
    if not request.user.is_premium():
        raise Http404('Halaman tidak tersedia.')
    existing = getattr(request.user, 'paid_template', None)
    if existing is None or existing.event_category is None:
        from django.shortcuts import redirect as _redirect
        return _redirect('paid_template')
    cat = existing.event_category
    vendors = list(VendorProfile.objects.filter(
        category=cat, verification_status='APPROVED', is_vetted=True
    ).select_related('category', 'user').prefetch_related('packages'))
    data = generate_planner_excel(_blank_plan(category=cat), vendors, {}, vendor_mode='basic')
    resp = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="Vendoraman_Template_Paid_{cat.slug}.xlsx"'
    return resp
