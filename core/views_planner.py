from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EventCategory, VendorProfile, VendorPackage, EventPlan, PlannerAccess
from .forms import EventSearchWizardForm


def planner_wizard_view(request):
    categories = EventCategory.objects.all()
    initial_category_slug = request.GET.get('category')
    initial_cat = None
    if initial_category_slug:
        initial_cat = EventCategory.objects.filter(slug=initial_category_slug).first()

    if request.method == 'POST':
        form = EventSearchWizardForm(request.POST)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            # If user is anonymous, we can find or create a guest customer or prompt login
            if not user or not user.is_authenticated:
                messages.info(request, "Silakan masuk atau daftar akun terlebih dahulu untuk menyimpan rencana event Anda.")
                # Save form data to session and redirect to login
                request.session['pending_wizard_data'] = {
                    'category_id': form.cleaned_data['category'].id,
                    'city': form.cleaned_data['city'],
                    'event_date': str(form.cleaned_data['event_date']),
                    'estimated_pax': form.cleaned_data['estimated_pax'],
                    'budget_min': str(form.cleaned_data['budget_min']),
                    'budget_max': str(form.cleaned_data['budget_max']),
                    'title': form.cleaned_data['event_title'],
                    'services': request.POST.getlist('services'),
                }
                return redirect('login')

            plan = EventPlan.objects.create(
                customer=user,
                title=form.cleaned_data['event_title'],
                event_category=form.cleaned_data['category'],
                city=form.cleaned_data['city'],
                event_date=form.cleaned_data['event_date'],
                estimated_pax=form.cleaned_data['estimated_pax'],
                budget_min=form.cleaned_data['budget_min'],
                budget_max=form.cleaned_data['budget_max'],
                selected_services=request.POST.getlist('services') or ['catering', 'decoration', 'venue']
            )
            messages.success(request, "Rencana event berhasil disusun! Menampilkan rekomendasi vendor.")
            return redirect('planner_results', plan_id=plan.id)
    else:
        initial_data = {}
        if initial_cat:
            initial_data['category'] = initial_cat
        form = EventSearchWizardForm(initial=initial_data)

    return render(request, 'planner/wizard.html', {
        'form': form,
        'categories': categories,
    })


def planner_results_view(request, plan_id):
    plan = get_object_or_404(EventPlan, id=plan_id)
    is_unlocked = plan.is_unlocked_for(request.user)

    # Filter vetted vendors matching category and city or general
    vendors_qs = VendorProfile.objects.filter(
        verification_status='APPROVED',
        is_vetted=True
    ).select_related('category', 'user').prefetch_related('packages')

    if plan.event_category:
        vendors_qs = vendors_qs.filter(category=plan.event_category)

    if plan.city:
        # Match city or case-insensitive contains
        city_vendors = vendors_qs.filter(city__icontains=plan.city)
        if city_vendors.exists():
            vendors_qs = city_vendors

    vendors_list = list(vendors_qs)

    # Budget calculation and breakdown
    total_budget = float(plan.budget_max)
    budget_allocations = {
        'Catering': round(total_budget * 0.40),
        'Dekorasi & Venue': round(total_budget * 0.30),
        'Dokumentasi (Foto/Video)': round(total_budget * 0.15),
        'Sound, Lighting & MC': round(total_budget * 0.15),
    }

    return render(request, 'planner/results.html', {
        'plan': plan,
        'is_unlocked': is_unlocked,
        'vendors': vendors_list,
        'budget_allocations': budget_allocations,
        'planner_fee': 150000,
    })


@login_required
def unlock_planner_view(request, plan_id):
    plan = get_object_or_404(EventPlan, id=plan_id)
    access, created = PlannerAccess.objects.get_or_create(
        customer=request.user,
        event_plan=plan,
        defaults={'fee_paid': 150000, 'is_unlocked': True}
    )
    if not access.is_unlocked:
        access.is_unlocked = True
        access.save()

    messages.success(
        request,
        f"Paid Planner berhasil dibuka! Anda kini memiliki akses tak terbatas ke profil resmi dan kontak langsung seluruh vendor untuk event '{plan.title}'."
    )
    return redirect('planner_results', plan_id=plan.id)


def vendor_detail_view(request, plan_id, vendor_id):
    plan = get_object_or_404(EventPlan, id=plan_id)
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    is_unlocked = plan.is_unlocked_for(request.user)
    packages = vendor.packages.filter(is_active=True)

    return render(request, 'planner/vendor_detail.html', {
        'plan': plan,
        'vendor': vendor,
        'is_unlocked': is_unlocked,
        'packages': packages,
    })
