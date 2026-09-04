from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BookingOrder, DisputeTicket
from .forms import DisputeFilingForm


@login_required
def file_dispute_view(request, order_id):
    order = get_object_or_404(BookingOrder, id=order_id, customer=request.user)

    if hasattr(order, 'dispute'):
        messages.warning(request, "Pesanan ini sudah memiliki tiket dispute yang sedang berjalan.")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        form = DisputeFilingForm(request.POST)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.order = order
            dispute.complainant = request.user
            dispute.status = 'OPEN'
            dispute.save()

            # Automatically FREEZE the escrow payouts
            order.escrow_status = 'FROZEN'
            order.save()

            messages.success(
                request,
                f"Dispute Tiket #{dispute.ticket_code} berhasil dibuat! Seluruh pencairan dana Escrow telah DIBEKUKAN demi melindungi hak finansial Anda. Tim Vendorama akan memediasi kasus ini."
            )
            return redirect('order_detail', order_id=order.id)
    else:
        form = DisputeFilingForm()

    return render(request, 'dispute/file_dispute.html', {
        'order': order,
        'form': form,
    })
