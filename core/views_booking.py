from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import VendorPackage, EventPlan, BookingOrder


@login_required
def booking_checkout_view(request):
    package_id = request.GET.get('package_id') or request.POST.get('package_id')
    plan_id = request.GET.get('plan_id') or request.POST.get('plan_id')

    package = get_object_or_404(VendorPackage, id=package_id)
    plan = EventPlan.objects.filter(id=plan_id, customer=request.user).first() if plan_id else None

    # Commission Calculation: 10% platform fee from vendor
    total_price = Decimal(str(package.price))
    commission_rate = Decimal('10.00')
    commission_amount = (total_price * commission_rate / Decimal('100')).quantize(Decimal('1'))
    vendor_net_amount = total_price - commission_amount


    # User savings vault if any
    vault = request.user.savings_vaults.first()

    if request.method == 'POST':
        event_date = request.POST.get('event_date')
        if not event_date and plan:
            event_date = plan.event_date

        if not event_date:
            messages.error(request, "Harap cantumkan tanggal pelaksanaan event.")
            return redirect(request.get_full_path())

        order = BookingOrder.objects.create(
            customer=request.user,
            vendor=package.vendor,
            package=package,
            event_date=event_date,
            total_price=total_price,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            vendor_net_amount=vendor_net_amount,
            status='PENDING',
            notes=request.POST.get('notes', '')
        )

        messages.success(
            request,
            f"Permintaan Booking Berhasil Dibuat! Vendor '{package.vendor.business_name}' telah menerima rincian pesanan Anda."
        )
        return redirect('order_detail', order_id=order.id)

    return render(request, 'booking/checkout.html', {
        'package': package,
        'plan': plan,
        'total_price': total_price,
        'commission_rate': commission_rate,
        'commission_amount': commission_amount,
        'vendor_net_amount': vendor_net_amount,
        'vault': vault,
    })


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(BookingOrder, id=order_id)

    is_customer = (request.user == order.customer)
    is_vendor = hasattr(request.user, 'vendor_profile') and (request.user.vendor_profile == order.vendor)
    is_admin = request.user.is_platform_admin()

    if not (is_customer or is_vendor or is_admin):
        messages.error(request, "Anda tidak memiliki akses ke rincian pesanan ini.")
        return redirect('home')

    return render(request, 'booking/order_detail.html', {
        'order': order,
        'is_customer': is_customer,
        'is_vendor': is_vendor,
        'is_admin': is_admin,
    })


@login_required
def update_order_status_view(request, order_id):
    order = get_object_or_404(BookingOrder, id=order_id)
    is_vendor = hasattr(request.user, 'vendor_profile') and (request.user.vendor_profile == order.vendor)
    is_customer = (request.user == order.customer)
    is_admin = request.user.is_platform_admin()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm' and (is_vendor or is_admin):
            order.status = 'CONFIRMED'
            order.save()
            messages.success(request, f"Pesanan {order.order_code} berhasil dikonfirmasi oleh vendor.")
        elif action == 'complete' and (is_vendor or is_customer or is_admin):
            order.status = 'COMPLETED'
            order.commission_status = 'PAID'
            order.vendor.total_completed_events += 1
            order.vendor.save()
            order.save()
            messages.success(request, f"Pesanan {order.order_code} telah diselesaikan! Pendapatan vendor telah dibukukan.")
        elif action == 'cancel' and (is_vendor or is_customer or is_admin):
            order.status = 'CANCELLED'
            order.save()
            messages.warning(request, f"Pesanan {order.order_code} telah dibatalkan.")
        else:
            messages.error(request, "Aksi tidak valid atau Anda tidak memiliki izin.")

    return redirect('order_detail', order_id=order.id)
