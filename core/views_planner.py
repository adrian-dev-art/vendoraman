import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import EventCategory, VendorProfile, VendorPackage, EventPlan, PlannerAccess
from .forms import EventSearchWizardForm


def _is_plan_owner_or_admin(user, plan):
    if not user.is_authenticated:
        return False
    if user == plan.customer:
        return True
    if getattr(user, 'is_staff', False):
        return True
    try:
        return user.is_platform_admin()
    except Exception:
        return False


def _get_accessible_plan(request, plan_id):
    """Return (plan, error_response). Denies non-owners to prevent ID enumeration leaks."""
    plan = get_object_or_404(EventPlan, id=plan_id)
    if not _is_plan_owner_or_admin(request.user, plan):
        messages.error(request, "Anda tidak memiliki akses ke rencana event ini.")
        return None, redirect('home')
    return plan, None


def planner_wizard_view(request):
    categories = EventCategory.objects.all()
    initial_category_slug = request.GET.get('category')
    initial_cat = None
    if initial_category_slug:
        initial_cat = EventCategory.objects.filter(slug=initial_category_slug).first()

    if request.method == 'POST':
        cat_id = request.POST.get('category')
        city = request.POST.get('city', 'Jakarta').strip() or 'Jakarta'
        event_date_str = request.POST.get('event_date')
        if not event_date_str:
            event_date = timezone.now().date() + datetime.timedelta(days=90)
        else:
            try:
                event_date = datetime.date.fromisoformat(event_date_str)
            except ValueError:
                event_date = timezone.now().date() + datetime.timedelta(days=90)

        try:
            estimated_pax = int(request.POST.get('estimated_pax') or 150)
        except ValueError:
            estimated_pax = 150

        try:
            budget_min = float(request.POST.get('budget_min') or 10000000)
            budget_max = float(request.POST.get('budget_max') or 50000000)
        except ValueError:
            budget_min = 10000000
            budget_max = 50000000

        category = EventCategory.objects.filter(id=cat_id).first() if cat_id else (initial_cat or categories.first())
        title = request.POST.get('event_title') or request.POST.get('title')
        if not title:
            cat_name = category.name if category else 'Event'
            title = f"Rencana {cat_name}"

        services = request.POST.getlist('services') or ['catering', 'dekorasi', 'venue']

        user = request.user if request.user.is_authenticated else None
        if not user or not user.is_authenticated:
            messages.info(request, "Silakan masuk atau daftar akun terlebih dahulu untuk menyimpan rencana event Anda.")
            request.session['pending_wizard_data'] = {
                'category_id': category.id if category else None,
                'city': city,
                'event_date': str(event_date),
                'estimated_pax': estimated_pax,
                'budget_min': str(budget_min),
                'budget_max': str(budget_max),
                'title': title,
                'services': services,
            }
            return redirect('login')

        plan = EventPlan.objects.create(
            customer=user,
            title=title,
            event_category=category,
            city=city,
            event_date=event_date,
            estimated_pax=estimated_pax,
            budget_min=budget_min,
            budget_max=budget_max,
            selected_services=services
        )
        messages.success(request, "Rencana event berhasil disusun! Menampilkan rekomendasi vendor terbaik.")
        return redirect('planner_results', plan_id=plan.id)

    initial_data = {}
    if initial_cat:
        initial_data['category'] = initial_cat
    form = EventSearchWizardForm(initial=initial_data)

    return render(request, 'planner/wizard.html', {
        'form': form,
        'categories': categories,
        'initial_cat': initial_cat,
    })


def _get_plan_vendors_and_budget(plan):
    vendors_qs = VendorProfile.objects.filter(
        verification_status='APPROVED',
        is_vetted=True
    ).select_related('category', 'user').prefetch_related('packages')

    if plan.event_category:
        vendors_qs = vendors_qs.filter(category=plan.event_category)

    if plan.city:
        city_vendors = vendors_qs.filter(city__icontains=plan.city)
        if city_vendors.exists():
            vendors_qs = city_vendors

    vendors_list = list(vendors_qs)

    total_budget = float(plan.budget_max)
    budget_allocations = {
        'Catering': round(total_budget * 0.40),
        'Dekorasi & Venue': round(total_budget * 0.30),
        'Dokumentasi (Foto/Video)': round(total_budget * 0.15),
        'Sound, Lighting & MC': round(total_budget * 0.15),
    }
    return vendors_list, budget_allocations


@login_required
def planner_results_view(request, plan_id):
    plan, err = _get_accessible_plan(request, plan_id)
    if err:
        return err
    is_unlocked = plan.is_unlocked_for(request.user)
    vendors_list, budget_allocations = _get_plan_vendors_and_budget(plan)
    all_categories = EventCategory.objects.all()

    from .services_export import get_planner_master_data
    planner_data = get_planner_master_data(plan)

    return render(request, 'planner/results.html', {
        'plan': plan,
        'is_unlocked': is_unlocked,
        'vendors': vendors_list,
        'budget_allocations': budget_allocations,
        'planner_data': planner_data,
        'planner_fee': getattr(settings, 'PLANNER_UNLOCK_FEE', 150000),
        'categories': all_categories,
    })


@login_required
@require_POST
def unlock_planner_view(request, plan_id):
    plan = get_object_or_404(EventPlan, id=plan_id)
    # Only the plan owner (or staff/admin) may unlock — prevents unlocking others' plans.
    if not _is_plan_owner_or_admin(request.user, plan):
        messages.error(request, "Anda tidak memiliki akses ke rencana event ini.")
        return redirect('home')
    if request.user != plan.customer and not (request.user.is_staff or request.user.is_platform_admin()):
        messages.error(request, "Hanya pemilik rencana yang dapat membuka Paid Planner.")
        return redirect('home')

    # TODO: verify real payment (Midtrans/Xendit callback) before marking unlocked.
    # For now we record the fee and require an explicit POST confirmation.
    fee = getattr(settings, 'PLANNER_UNLOCK_FEE', 150000)
    access, created = PlannerAccess.objects.get_or_create(
        customer=plan.customer,
        event_plan=plan,
        defaults={'fee_paid': fee, 'is_unlocked': True}
    )
    if not access.is_unlocked:
        access.is_unlocked = True
        access.fee_paid = fee
        access.save()

    messages.success(
        request,
        f"Paid Planner berhasil dibuka! Anda kini memiliki akses tak terbatas ke profil resmi dan kontak langsung seluruh vendor untuk event '{plan.title}'."
    )
    return redirect('planner_results', plan_id=plan.id)


@login_required
def vendor_detail_view(request, plan_id, vendor_id):
    plan, err = _get_accessible_plan(request, plan_id)
    if err:
        return err
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    is_unlocked = plan.is_unlocked_for(request.user)
    packages = vendor.packages.filter(is_active=True)

    return render(request, 'planner/vendor_detail.html', {
        'plan': plan,
        'vendor': vendor,
        'is_unlocked': is_unlocked,
        'packages': packages,
    })


def export_planner_excel_view(request, plan_id):
    if not request.user.is_authenticated:
        return redirect('login')
    plan, err = _get_accessible_plan(request, plan_id)
    if err:
        return err
    if not plan.is_unlocked_for(request.user):
        messages.info(request, "Fitur ekspor Excel adalah fasilitas eksklusif Paid Planner. Silakan aktifkan planner Anda.")
        return redirect('planner_results', plan_id=plan.id)

    from django.http import HttpResponse
    from .services_export import generate_planner_excel

    vendors_list, budget_allocations = _get_plan_vendors_and_budget(plan)
    excel_bytes = generate_planner_excel(plan, vendors_list, budget_allocations)

    filename = f"Vendoraman_EventPlan_{plan.id}_{plan.city}.xlsx"
    response = HttpResponse(
        excel_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_planner_pdf_view(request, plan_id):
    if not request.user.is_authenticated:
        return redirect('login')
    plan, err = _get_accessible_plan(request, plan_id)
    if err:
        return err
    if not plan.is_unlocked_for(request.user):
        messages.info(request, "Fitur ekspor PDF Deck adalah fasilitas eksklusif Paid Planner. Silakan aktifkan planner Anda.")
        return redirect('planner_results', plan_id=plan.id)

    from django.http import HttpResponse
    from .services_export import generate_planner_pdf_deck

    vendors_list, budget_allocations = _get_plan_vendors_and_budget(plan)
    pdf_bytes = generate_planner_pdf_deck(plan, vendors_list, budget_allocations)

    filename = f"Vendoraman_ExecutiveDeck_{plan.id}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def planner_deck_view(request, plan_id):
    if not request.user.is_authenticated:
        return redirect('login')
    plan, err = _get_accessible_plan(request, plan_id)
    if err:
        return err
    if not plan.is_unlocked_for(request.user):
        messages.info(request, "Fitur Slide Deck adalah fasilitas eksklusif Paid Planner. Silakan aktifkan planner Anda.")
        return redirect('planner_results', plan_id=plan.id)

    vendors_list, budget_allocations = _get_plan_vendors_and_budget(plan)
    from .services_export import get_planner_master_data
    planner_data = get_planner_master_data(plan)

    return render(request, 'planner/deck.html', {
        'plan': plan,
        'vendors': vendors_list,
        'budget_allocations': budget_allocations,
        'planner_data': planner_data,
        'is_unlocked': True,
    })
