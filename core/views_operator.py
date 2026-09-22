import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from .models import ExcelTemplate, EventCategory


def is_operator_or_admin_check(user):
    return user.is_authenticated and user.can_manage_shopee_and_templates()


@login_required
@user_passes_test(is_operator_or_admin_check)
def operator_templates_list_view(request):
    """Halaman daftar manajemen template Excel untuk Operator CS Shopee dan Admin."""
    templates = ExcelTemplate.objects.select_related('category').all().order_by('category__name')
    total_templates = templates.count()
    active_templates = templates.filter(is_active=True).count()
    total_downloads = templates.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0

    return render(request, 'operator/template_list.html', {
        'templates': templates,
        'total_templates': total_templates,
        'active_templates': active_templates,
        'total_downloads': total_downloads,
    })


@login_required
@user_passes_test(is_operator_or_admin_check)
@require_http_methods(['GET', 'POST'])
def operator_template_edit_view(request, template_id):
    """Form pengeditan konten dan upload file master Excel untuk template tertentu."""
    tmpl = get_object_or_404(ExcelTemplate.objects.select_related('category'), id=template_id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        subheadline = request.POST.get('subheadline', '').strip()
        target_audience = request.POST.get('target_audience', '').strip()
        estimated_savings = request.POST.get('estimated_savings', '').strip()
        shopee_product_url = request.POST.get('shopee_product_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Key perks from textarea (one perk per line)
        perks_raw = request.POST.get('key_perks_text', '')
        perks_list = [line.strip() for line in perks_raw.splitlines() if line.strip()]

        if not title:
            messages.error(request, 'Judul template tidak boleh kosong.')
            return redirect('operator_template_edit', template_id=tmpl.id)

        tmpl.title = title
        tmpl.subheadline = subheadline
        tmpl.target_audience = target_audience
        tmpl.estimated_savings = estimated_savings
        tmpl.shopee_product_url = shopee_product_url
        tmpl.is_active = is_active
        tmpl.key_perks = perks_list

        # Handle file upload if provided
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                messages.error(request, 'Format file harus berupa spreadsheet Excel (.xlsx atau .xls).')
                return redirect('operator_template_edit', template_id=tmpl.id)
            tmpl.file = uploaded_file

        # Handle remove file if requested
        if request.POST.get('remove_file') == 'true':
            if tmpl.file:
                tmpl.file.delete(save=False)
                tmpl.file = None

        tmpl.save()
        messages.success(request, f'Template "{tmpl.title}" ({tmpl.category.name}) berhasil diperbarui.')
        return redirect('operator_templates')

    # Convert perks list to newline-separated text for textarea
    perks_text = '\n'.join(tmpl.get_perks_list())

    return render(request, 'operator/template_edit.html', {
        'tmpl': tmpl,
        'perks_text': perks_text,
    })
