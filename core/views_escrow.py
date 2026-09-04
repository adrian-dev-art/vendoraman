from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import VendorPackage, EventPlan, BookingOrder, EscrowMilestone


@login_required
def escrow_checkout_view(request):
    package_id = request.GET.get('package_id') or request.POST.get('package_id')
    plan_id = request.GET.get('plan_id') or request.POST.get('plan_id')

    package = get_object_or_404(VendorPackage, id=package_id)
    plan = EventPlan.objects.filter(id=plan_id, customer=request.user).first() if plan_id else None

    # Calculate 3-tier milestones
    total_price = package.price
    dp_amount = round(total_price * 30 / 100)
    mid_amount = round(total_price * 40 / 100)
    final_amount = total_price - dp_amount - mid_amount

    # Check user savings vault if any
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
            escrow_status='HELD',
            notes=request.POST.get('notes', '')
        )
        order.create_default_milestones()

        messages.success(
            request,
            f"Pembayaran Escrow Berhasil! Dana Rp {total_price:,.0f} telah diamankan di Rekening Bersama Vendorama. Vendor telah menerima notifikasi persiapan."
        )
        return redirect('order_detail', order_id=order.id)

    return render(request, 'escrow/checkout.html', {
        'package': package,
        'plan': plan,
        'total_price': total_price,
        'dp_amount': dp_amount,
        'mid_amount': mid_amount,
        'final_amount': final_amount,
        'vault': vault,
    })


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(BookingOrder, id=order_id)

    # Permission check: customer, vendor user, or admin
    is_customer = (request.user == order.customer)
    is_vendor = hasattr(request.user, 'vendor_profile') and (request.user.vendor_profile == order.vendor)
    is_admin = request.user.is_platform_admin()

    if not (is_customer or is_vendor or is_admin):
        messages.error(request, "Anda tidak memiliki akses ke rincian pesanan ini.")
        return redirect('home')

    milestones = order.milestones.all().order_by('milestone_index')
    dispute = getattr(order, 'dispute', None)

    return render(request, 'escrow/order_detail.html', {
        'order': order,
        'milestones': milestones,
        'dispute': dispute,
        'is_customer': is_customer,
        'is_vendor': is_vendor,
        'is_admin': is_admin,
    })


@login_required
def request_milestone_payout_view(request, order_id, milestone_id):
    order = get_object_or_404(BookingOrder, id=order_id)
    milestone = get_object_or_404(EscrowMilestone, id=milestone_id, order=order)

    # Only the vendor or admin can request payout
    is_vendor = hasattr(request.user, 'vendor_profile') and (request.user.vendor_profile == order.vendor)
    if not (is_vendor or request.user.is_platform_admin()):
        messages.error(request, "Hanya vendor yang dapat mengajukan pencairan termin.")
        return redirect('order_detail', order_id=order.id)

    if order.escrow_status == 'FROZEN':
        messages.error(request, "Pencairan tidak dapat diajukan karena pesanan sedang dalam proses sengketa (Dispute).")
        return redirect('order_detail', order_id=order.id)

    if milestone.status == 'HELD':
        milestone.status = 'REQUESTED'
        milestone.save()
        messages.success(request, f"Permintaan pencairan untuk '{milestone.title}' berhasil dikirim ke platform dan customer.")

    return redirect('order_detail', order_id=order.id)


@login_required
def approve_milestone_payout_view(request, order_id, milestone_id):
    order = get_object_or_404(BookingOrder, id=order_id)
    milestone = get_object_or_404(EscrowMilestone, id=milestone_id, order=order)

    # Customer or Admin can release funds
    is_customer = (request.user == order.customer)
    is_admin = request.user.is_platform_admin()

    if not (is_customer or is_admin):
        messages.error(request, "Hanya customer pemesan atau tim admin yang dapat menyetujui pencairan dana escrow.")
        return redirect('order_detail', order_id=order.id)

    if order.escrow_status == 'FROZEN':
        messages.error(request, "Pesanan dalam status sengketa. Pembayaran ditangguhkan.")
        return redirect('order_detail', order_id=order.id)

    milestone.status = 'RELEASED'
    milestone.released_at = timezone.now()
    milestone.save()

    # Update overall order escrow status
    if milestone.milestone_index == 1:
        order.escrow_status = 'MILESTONE_1_PAID'
    elif milestone.milestone_index == 2:
        order.escrow_status = 'MILESTONE_2_PAID'
    elif milestone.milestone_index == 3:
        order.escrow_status = 'COMPLETED'
        order.vendor.total_completed_events += 1
        order.vendor.save()

    order.save()

    messages.success(
        request,
        f"Dana termin '{milestone.title}' sebesar Rp {milestone.amount:,.0f} telah dicairkan ke saldo vendor."
    )
    return redirect('order_detail', order_id=order.id)
