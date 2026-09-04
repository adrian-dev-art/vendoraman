from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import VendorProfile, BookingOrder, DisputeTicket, EscrowMilestone


def is_admin_check(user):
    return user.is_authenticated and user.is_platform_admin()


@login_required
@user_passes_test(is_admin_check)
def admin_dashboard_view(request):
    pending_vendors = VendorProfile.objects.filter(verification_status='PENDING').order_by('-created_at')
    active_orders = BookingOrder.objects.exclude(escrow_status__in=['COMPLETED', 'REFUNDED']).order_by('-created_at')
    active_disputes = DisputeTicket.objects.filter(status__in=['OPEN', 'INVESTIGATING']).order_by('-created_at')
    resolved_disputes = DisputeTicket.objects.filter(status__in=['REFUNDED_TO_CUSTOMER', 'SETTLED_PARTIAL', 'REJECTED']).order_by('-resolved_at')[:5]

    # Metrics
    total_escrow_held = BookingOrder.objects.filter(escrow_status__in=['HELD', 'MILESTONE_1_PAID', 'MILESTONE_2_PAID', 'FROZEN']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_vetted_vendors = VendorProfile.objects.filter(is_vetted=True).count()

    return render(request, 'admin/dashboard.html', {
        'pending_vendors': pending_vendors,
        'active_orders': active_orders,
        'active_disputes': active_disputes,
        'resolved_disputes': resolved_disputes,
        'total_escrow_held': total_escrow_held,
        'total_vetted_vendors': total_vetted_vendors,
    })


@login_required
@user_passes_test(is_admin_check)
def admin_dispute_detail_view(request, dispute_id):
    dispute = get_object_or_404(DisputeTicket, id=dispute_id)
    order = dispute.order
    milestones = order.milestones.all().order_by('milestone_index')

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')

        if action == 'REFUND':
            # Execute Financial Guarantee: refund customer and penalize vendor
            dispute.status = 'REFUNDED_TO_CUSTOMER'
            dispute.admin_notes = admin_notes or "Terbukti terjadi kelalaian / wanprestasi vendor. Dana escrow dikembalikan penuh ke customer."
            dispute.penalty_applied = True
            dispute.resolved_at = timezone.now()
            dispute.save()

            order.escrow_status = 'REFUNDED'
            order.save()

            # Penalize and suspend vendor
            vendor = order.vendor
            vendor.verification_status = 'SUSPENDED'
            vendor.is_vetted = False
            vendor.save()

            messages.success(
                request,
                f"Garansi Finansial Berhasil Dieksekusi! 100% sisa dana Escrow (Rp {order.total_price:,.0f}) telah direfund ke {order.customer.username}. Vendor '{vendor.business_name}' telah resmi disuspensi."
            )
            return redirect('admin_dashboard')

        elif action == 'REJECT':
            dispute.status = 'REJECTED'
            dispute.admin_notes = admin_notes or "Dispute ditolak setelah investigasi membuktikan spesifikasi terpenuhi."
            dispute.resolved_at = timezone.now()
            dispute.save()

            order.escrow_status = 'HELD'
            order.save()

            messages.info(request, f"Dispute #{dispute.ticket_code} ditolak. Pembekuan Escrow telah dilepas.")
            return redirect('admin_dashboard')

    return render(request, 'admin/dispute_detail.html', {
        'dispute': dispute,
        'order': order,
        'milestones': milestones,
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
        messages.warning(request, f"Pendaftaran Vendor '{vendor.business_name}' telah ditolak.")

    return redirect('admin_dashboard')
