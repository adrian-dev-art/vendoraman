from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder, EscrowMilestone, DisputeTicket
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone_number', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Vendorama Role & Info', {'fields': ('role', 'phone_number')}),
    )


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon_name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'anonymized_code', 'category', 'city', 'verification_status', 'is_vetted', 'rating']
    list_filter = ['verification_status', 'is_vetted', 'category', 'city']
    search_fields = ['business_name', 'anonymized_code', 'pic_name', 'contact_phone']
    actions = ['approve_and_vet_vendor', 'suspend_vendor']

    def approve_and_vet_vendor(self, request, queryset):
        queryset.update(verification_status='APPROVED', is_vetted=True)
    approve_and_vet_vendor.short_description = 'Approve and grant Vetted Trust Badge'

    def suspend_vendor(self, request, queryset):
        queryset.update(verification_status='SUSPENDED', is_vetted=False)
    suspend_vendor.short_description = 'Suspend and penalize selected vendors'


@admin.register(VendorPackage)
class VendorPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'pax_capacity', 'is_active']
    list_filter = ['is_active', 'vendor__category']
    search_fields = ['name', 'vendor__business_name']


@admin.register(EventPlan)
class EventPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'event_category', 'city', 'event_date', 'budget_min', 'budget_max']
    list_filter = ['event_category', 'city']


@admin.register(PlannerAccess)
class PlannerAccessAdmin(admin.ModelAdmin):
    list_display = ['customer', 'event_plan', 'fee_paid', 'is_unlocked', 'unlocked_at']


@admin.register(EventSavingsVault)
class EventSavingsVaultAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'target_amount', 'current_amount', 'target_date']


@admin.register(SavingsDeposit)
class SavingsDepositAdmin(admin.ModelAdmin):
    list_display = ['vault', 'amount', 'payment_method', 'created_at']


class EscrowMilestoneInline(admin.TabularInline):
    model = EscrowMilestone
    extra = 0


@admin.register(BookingOrder)
class BookingOrderAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'customer', 'vendor', 'package', 'total_price', 'escrow_status', 'event_date']
    list_filter = ['escrow_status']
    search_fields = ['order_code', 'customer__username', 'vendor__business_name']
    inlines = [EscrowMilestoneInline]


@admin.register(DisputeTicket)
class DisputeTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_code', 'order', 'complainant', 'status', 'penalty_applied', 'created_at']
    list_filter = ['status', 'penalty_applied']
    search_fields = ['ticket_code', 'order__order_code', 'complainant__username']
