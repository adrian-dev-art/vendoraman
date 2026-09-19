from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from .models import VendorProfile, BookingOrder


def is_admin_check(user):
    return user.is_authenticated and user.is_platform_admin()


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
