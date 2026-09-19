from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import EventPlan, BookingOrder, EventSavingsVault, VendorProfile, VendorPackage, EventCategory


@login_required
def customer_dashboard_view(request):
    if not request.user.is_customer() and not request.user.is_platform_admin():
        if request.user.is_vendor_user():
            return redirect('vendor_dashboard')

    plans = EventPlan.objects.filter(customer=request.user).order_by('-created_at')
    orders = BookingOrder.objects.filter(customer=request.user).select_related('vendor', 'package').order_by('-created_at')
    vaults = EventSavingsVault.objects.filter(customer=request.user).order_by('-created_at')

    return render(request, 'customer/dashboard.html', {
        'plans': plans,
        'orders': orders,
        'vaults': vaults,
    })


@login_required
def vendor_dashboard_view(request):
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, "Akun Anda bukan akun vendor yang terdaftar.")
        return redirect('home')

    vendor = request.user.vendor_profile
    orders = BookingOrder.objects.filter(vendor=vendor).select_related('customer', 'package').order_by('-created_at')
    packages = vendor.packages.all().order_by('-created_at')

    # Commission Financial Metrics
    active_or_completed = orders.exclude(status='CANCELLED')
    gross_revenue = active_or_completed.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_commission_paid = active_or_completed.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0
    net_earnings = active_or_completed.aggregate(Sum('vendor_net_amount'))['vendor_net_amount__sum'] or 0

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        pax_capacity = request.POST.get('pax_capacity', 100)
        specifications = request.POST.get('specifications', '')

        if name and price:
            VendorPackage.objects.create(
                vendor=vendor,
                name=name,
                price=price,
                pax_capacity=pax_capacity,
                specifications=specifications
            )
            messages.success(request, f"Paket layanan '{name}' berhasil ditambahkan ke katalog!")
            return redirect('vendor_dashboard')

    return render(request, 'vendor/dashboard.html', {
        'vendor': vendor,
        'orders': orders,
        'packages': packages,
        'gross_revenue': gross_revenue,
        'total_commission_paid': total_commission_paid,
        'net_earnings': net_earnings,
    })
