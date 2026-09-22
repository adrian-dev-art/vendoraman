from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from .models import VendorProfile, BookingOrder


def is_admin_check(user):
    return user.is_authenticated and user.is_platform_admin()


def is_operator_or_admin_check(user):
    return user.is_authenticated and user.can_manage_shopee_and_templates()


@login_required
@user_passes_test(is_admin_check)
def admin_dashboard_view(request):
    pending_vendors = VendorProfile.objects.filter(verification_status='PENDING').order_by('-created_at')
    active_orders = BookingOrder.objects.exclude(status='CANCELLED').order_by('-created_at')
    recent_completed_orders = BookingOrder.objects.filter(status='COMPLETED').order_by('-created_at')[:5]

    # Metrics
    total_gmv = BookingOrder.objects.exclude(status='CANCELLED').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_commission_revenue = BookingOrder.objects.exclude(status='CANCELLED').aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0
    total_vetted_vendors = VendorProfile.objects.filter(is_vetted=True).count()

    return render(request, 'admin/dashboard.html', {
        'pending_vendors': pending_vendors,
        'active_orders': active_orders,
        'recent_completed_orders': recent_completed_orders,
        'total_gmv': total_gmv,
        'total_commission_revenue': total_commission_revenue,
        'total_vetted_vendors': total_vetted_vendors,
    })


@login_required
@user_passes_test(is_admin_check)
def admin_verify_vendor_view(request, vendor_id, action):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    if action == 'approve':
        vendor.verification_status = 'APPROVED'
        vendor.is_vetted = True
        vendor.save()
        messages.success(request, f"Vendor '{vendor.business_name}' berhasil diverifikasi dan mendapatkan lencana Vetted Trust Badge.")
    elif action == 'reject':
        vendor.verification_status = 'REJECTED'
        vendor.is_vetted = False
        vendor.save()
        messages.warning(request, f"Pendaftaran vendor '{vendor.business_name}' telah ditolak.")
    elif action == 'suspend':
        vendor.verification_status = 'SUSPENDED'
        vendor.is_vetted = False
        vendor.save()
        messages.error(request, f"Vendor '{vendor.business_name}' telah disuspensi dari platform.")

    return redirect('admin_dashboard')


import secrets
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from .models import TemplateDownloadCode, TemplateDownloadLog


@login_required
@user_passes_test(is_operator_or_admin_check)
def admin_download_codes_view(request):
    """Halaman tabel manajemen kode unduh Shopee dengan pelacakan aktivitas."""
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')

    codes_qs = TemplateDownloadCode.objects.select_related('category', 'downloaded_category').all()

    if search_query:
        codes_qs = codes_qs.filter(
            Q(code__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(last_page_viewed__icontains=search_query)
        )

    if status_filter == 'unused':
        codes_qs = codes_qs.filter(used_count=0, is_active=True)
    elif status_filter == 'used':
        codes_qs = codes_qs.filter(used_count__gte=1)
    elif status_filter == 'visited':
        codes_qs = codes_qs.filter(first_visited_at__isnull=False)
    elif status_filter == 'unvisited':
        codes_qs = codes_qs.filter(first_visited_at__isnull=True, used_count=0)
    elif status_filter == 'inactive':
        codes_qs = codes_qs.filter(is_active=False)

    # Statistics
    total_codes = TemplateDownloadCode.objects.count()
    unused_codes = TemplateDownloadCode.objects.filter(used_count=0, is_active=True).count()
    used_codes = TemplateDownloadCode.objects.filter(used_count__gte=1).count()
    visited_codes = TemplateDownloadCode.objects.filter(first_visited_at__isnull=False).count()
    avg_seconds = TemplateDownloadCode.objects.filter(time_spent_seconds__gt=0).aggregate(Avg('time_spent_seconds'))['time_spent_seconds__avg'] or 0
    avg_time_display = f"{int(avg_seconds // 60)}m {int(avg_seconds % 60)}s" if avg_seconds >= 60 else f"{int(avg_seconds)} dtk"

    paginator = Paginator(codes_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/download_codes.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_codes': total_codes,
        'unused_codes': unused_codes,
        'used_codes': used_codes,
        'visited_codes': visited_codes,
        'avg_time_display': avg_time_display,
    })


@login_required
@user_passes_test(is_operator_or_admin_check)
@require_POST
def admin_generate_code_api(request):
    """API untuk membuat kode download baru (universal 1x pakai) dan pesan chat Shopee."""
    notes = request.POST.get('notes', 'Shopee Customer').strip()
    prefix = "VND-MSTR"

    # Generate unique code
    while True:
        token = secrets.token_hex(3).upper()
        code_str = f"{prefix}-{token}"
        if not TemplateDownloadCode.objects.filter(code=code_str).exists():
            break

    code_obj = TemplateDownloadCode.objects.create(
        code=code_str,
        category=None,  # None = Universal (Bebas untuk template mana pun)
        max_uses=1,     # Hanya 1 kali unduh
        is_active=True,
        notes=notes or "Shopee Customer"
    )

    base_url = request.build_absolute_uri('/')
    chat_message = code_obj.generate_chat_message(base_url=base_url)
    direct_link = f"{base_url.rstrip('/')}/templates/?code={code_obj.code}"

    return JsonResponse({
        'status': 'success',
        'id': code_obj.id,
        'code': code_obj.code,
        'message': chat_message,
        'direct_link': direct_link,
        'created_at': code_obj.created_at.strftime('%d %b %Y, %H:%M'),
        'max_uses': code_obj.max_uses,
        'used_count': code_obj.used_count,
        'notes': code_obj.notes,
    })


@login_required
@user_passes_test(is_operator_or_admin_check)
@require_POST
def admin_toggle_code_api(request, code_id):
    """API untuk mengaktifkan / menonaktifkan kode."""
    code_obj = get_object_or_404(TemplateDownloadCode, id=code_id)
    code_obj.is_active = not code_obj.is_active
    code_obj.save(update_fields=['is_active'])
    return JsonResponse({
        'status': 'success',
        'is_active': code_obj.is_active,
        'code': code_obj.code
    })
