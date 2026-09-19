from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder, FreeTemplateSettings, FreeTemplateLead,
    EmailVerification, Voucher, VoucherRedemption, PaidTemplateDownload
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone_number', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Vendoraman Role & Info', {'fields': ('role', 'phone_number')}),
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
    suspend_vendor.short_description = 'Suspend selected vendors'


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


@admin.register(BookingOrder)
class BookingOrderAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'customer', 'vendor', 'package', 'total_price', 'commission_amount', 'vendor_net_amount', 'status', 'commission_status', 'event_date']
    list_filter = ['status', 'commission_status']
    search_fields = ['order_code', 'customer__username', 'vendor__business_name']


@admin.register(FreeTemplateSettings)
class FreeTemplateSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_enabled', 'original_price', 'updated_at']
    list_editable = ['is_enabled']
    actions = ['enable_page', 'disable_page']

    def has_add_permission(self, request):
        # Singleton: never add a second row; edit the existing one.
        return not FreeTemplateSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def enable_page(self, request, queryset):
        queryset.update(is_enabled=True)
    enable_page.short_description = 'Aktifkan halaman template gratis'

    def disable_page(self, request, queryset):
        queryset.update(is_enabled=False)
    disable_page.short_description = 'Nonaktifkan halaman template gratis (jadi 404)'


@admin.register(FreeTemplateLead)
class FreeTemplateLeadAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone_number', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['email', 'phone_number']
    readonly_fields = ['email', 'phone_number', 'is_verified', 'created_at']

    def has_add_permission(self, request):
        return False


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'attempts', 'verified_at', 'created_at']
    search_fields = ['email']
    readonly_fields = ['email', 'code', 'attempts', 'verified_at', 'created_at']

    def has_add_permission(self, request):
        return False


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'duration_days', 'used_count', 'max_uses', 'is_active', 'valid_until', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code']


@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = ['voucher', 'email', 'user', 'expires_at', 'redeemed_at']
    search_fields = ['email', 'voucher__code']
    readonly_fields = ['voucher', 'user', 'email', 'expires_at', 'redeemed_at']

    def has_add_permission(self, request):
        return False


@admin.register(PaidTemplateDownload)
class PaidTemplateDownloadAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_category', 'created_at']
    search_fields = ['user__username', 'event_category__name']

