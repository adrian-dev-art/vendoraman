from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EventSavingsVault, SavingsDeposit, EventPlan
from .forms import EventSavingsVaultForm, SavingsDepositForm
from .templatetags.currency_tags import intdot


@login_required
def savings_list_view(request):
    vaults = EventSavingsVault.objects.filter(customer=request.user).order_by('-created_at')

    if request.method == 'POST':
        form = EventSavingsVaultForm(request.POST)
        if form.is_valid():
            vault = form.save(commit=False)
            vault.customer = request.user
            vault.save()
            messages.success(request, f"Tabungan Event '{vault.title}' berhasil dibuat! Anda dapat mulai menyetor dana kapan saja.")
            return redirect('savings_detail', vault_id=vault.id)
    else:
        form = EventSavingsVaultForm()

    return render(request, 'savings/vault_list.html', {
        'vaults': vaults,
        'form': form,
    })


@login_required
def savings_detail_view(request, vault_id):
    vault = get_object_or_404(EventSavingsVault, id=vault_id, customer=request.user)
    deposits = vault.deposits.all().order_by('-created_at')

    if request.method == 'POST':
        deposit_form = SavingsDepositForm(request.POST)
        if deposit_form.is_valid():
            amount = deposit_form.cleaned_data['amount']
            notes = deposit_form.cleaned_data['notes']
            
            SavingsDeposit.objects.create(
                vault=vault,
                amount=amount,
                payment_method='Virtual Account Escrow',
                notes=notes or 'Setoran Tabungan Fleksibel'
            )
            vault.current_amount += amount
            vault.save()

            messages.success(request, f"Setoran tabungan sebesar Rp {intdot(amount)} berhasil diterima dan ditampung aman di Escrow Vault.")
            return redirect('savings_detail', vault_id=vault.id)
    else:
        deposit_form = SavingsDepositForm()

    return render(request, 'savings/vault_detail.html', {
        'vault': vault,
        'deposits': deposits,
        'deposit_form': deposit_form,
    })
