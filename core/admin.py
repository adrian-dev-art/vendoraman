from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import (
    CustomUser, EventCategory, VendorProfile, VendorPackage,
    EventPlan, PlannerAccess, EventSavingsVault, SavingsDeposit,
    BookingOrder, FreeTemplateSettings, FreeTemplateLead,
    EmailVerification, Voucher, VoucherRedemption, PaidTemplateDownload,
    TemplateDownloadCode, TemplateDownloadLog, ExcelTemplate
)


@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin, UserAdmin):
    list_display = ['username', 'email', 'role_badge', 'phone_number', 'is_staff_badge', 'is_active']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'phone_number']
    fieldsets = UserAdmin.fieldsets + (
        ('Vendoraman Role & Info', {'fields': ('role', 'phone_number', 'premium_until')}),
    )

    @display(
        description='Role',
        label={
            'CUSTOMER': 'info',
            'VENDOR': 'warning',
            'ADMIN': 'success',
        }
    )
    def role_badge(self, obj):
        return obj.role

    @display(
        description='Staff Access',
        boolean=True
    )
    def is_staff_badge(self, obj):
        return obj.is_staff


class VendorPackageInline(TabularInline):
    model = VendorPackage
    extra = 0
    fields = ['name', 'price', 'pax_capacity', 'is_active']


@admin.register(VendorProfile)
class VendorProfileAdmin(ModelAdmin):
    list_display = ['business_name', 'anonymized_code', 'category', 'city', 'status_badge', 'is_vetted_badge', 'rating', 'created_at']
    list_filter = ['verification_status', 'is_vetted', 'category', 'city']
    search_fields = ['business_name', 'anonymized_code', 'pic_name', 'contact_phone', 'contact_email']
    inlines = [VendorPackageInline]
    actions = ['approve_and_vet_vendor', 'suspend_vendor']

    @display(
        description='Verifikasi Status',
        label={
            'PENDING': 'warning',
            'APPROVED': 'success',
            'REJECTED': 'danger',
            'SUSPENDED': 'danger',
        }
    )
    def status_badge(self, obj):
        return obj.verification_status

    @display(
        description='Vetted Partner',
        boolean=True
    )
    def is_vetted_badge(self, obj):
        return obj.is_vetted

    @admin.action(description='Setujui dan beri lencana Vetted Partner')
    def approve_and_vet_vendor(self, request, queryset):
        queryset.update(verification_status='APPROVED', is_vetted=True)
        self.message_user(request, "Vendor terpilih berhasil disetujui dan diverifikasi.")

    @admin.action(description='Tangguhkan / Suspend vendor terpilih')
    def suspend_vendor(self, request, queryset):
        queryset.update(verification_status='SUSPENDED', is_vetted=False)
        self.message_user(request, "Vendor terpilih telah ditangguhkan.")


@admin.register(VendorPackage)
class VendorPackageAdmin(ModelAdmin):
    list_display = ['name', 'vendor', 'formatted_price', 'pax_capacity', 'is_active_badge']
    list_filter = ['is_active', 'vendor__category']
    search_fields = ['name', 'vendor__business_name']

    @display(description='Harga (Rp)')
    def formatted_price(self, obj):
        return f"Rp {int(obj.price):,}".replace(',', '.')

    @display(description='Aktif', boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


@admin.register(EventCategory)
class EventCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'icon_name', 'total_vendors', 'total_packages']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    @display(description='Total Vendor')
    def total_vendors(self, obj):
        return obj.vendors.count()

    @display(description='Total Paket')
    def total_packages(self, obj):
        return VendorPackage.objects.filter(vendor__category=obj).count()


@admin.register(EventPlan)
class EventPlanAdmin(ModelAdmin):
    list_display = ['title', 'customer', 'event_category', 'city', 'event_date', 'estimated_pax', 'created_at']
    list_filter = ['event_category', 'city', 'event_date']
    search_fields = ['title', 'customer__username', 'city']


@admin.register(PlannerAccess)
class PlannerAccessAdmin(ModelAdmin):
    list_display = ['customer', 'event_plan', 'fee_paid_display', 'is_unlocked_badge', 'unlocked_at']
    list_filter = ['is_unlocked']
    search_fields = ['customer__username', 'event_plan__title']

    @display(description='Fee Paid')
    def fee_paid_display(self, obj):
        return f"Rp {int(obj.fee_paid):,}".replace(',', '.')

    @display(description='Unlocked', boolean=True)
    def is_unlocked_badge(self, obj):
        return obj.is_unlocked


@admin.register(EventSavingsVault)
class EventSavingsVaultAdmin(ModelAdmin):
    list_display = ['title', 'customer', 'current_amount_display', 'target_amount_display', 'target_date']
    search_fields = ['title', 'customer__username']

    @display(description='Terkumpul')
    def current_amount_display(self, obj):
        return f"Rp {int(obj.current_amount):,}".replace(',', '.')

    @display(description='Target')
    def target_amount_display(self, obj):
        return f"Rp {int(obj.target_amount):,}".replace(',', '.')


@admin.register(SavingsDeposit)
class SavingsDepositAdmin(ModelAdmin):
    list_display = ['vault', 'amount_display', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['vault__title', 'vault__customer__username']

    @display(description='Jumlah Setoran')
    def amount_display(self, obj):
        return f"Rp {int(obj.amount):,}".replace(',', '.')


@admin.register(BookingOrder)
class BookingOrderAdmin(ModelAdmin):
    list_display = [
        'order_code', 'customer', 'vendor', 'package',
        'total_price_display', 'commission_display', 'vendor_net_display',
        'status_badge', 'commission_badge', 'event_date'
    ]
    list_filter = ['status', 'commission_status', 'event_date']
    search_fields = ['order_code', 'customer__username', 'vendor__business_name', 'customer__phone_number']

    @display(
        description='Status Order',
        label={
            'PENDING': 'warning',
            'CONFIRMED': 'info',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
        }
    )
    def status_badge(self, obj):
        return obj.status

    @display(
        description='Status Fee Komisi',
        label={
            'UNPAID': 'warning',
            'PAID': 'success',
            'REFUNDED': 'danger',
        }
    )
    def commission_badge(self, obj):
        return obj.commission_status

    @display(description='Total (Rp)')
    def total_price_display(self, obj):
        return f"Rp {int(obj.total_price):,}".replace(',', '.')

    @display(description='Komisi 10% (Rp)')
    def commission_display(self, obj):
        return f"Rp {int(obj.commission_amount):,}".replace(',', '.')

    @display(description='Hak Vendor (Rp)')
    def vendor_net_display(self, obj):
        return f"Rp {int(obj.vendor_net_amount):,}".replace(',', '.')


@admin.register(FreeTemplateSettings)
class FreeTemplateSettingsAdmin(ModelAdmin):
    list_display = ['__str__', 'is_enabled_badge', 'original_price_display', 'updated_at']
    list_editable = []
    actions = ['enable_page', 'disable_page']

    @display(description='Aktif (Online)', boolean=True)
    def is_enabled_badge(self, obj):
        return obj.is_enabled

    @display(description='Harga Coret')
    def original_price_display(self, obj):
        return f"Rp {int(obj.original_price):,}".replace(',', '.')

    def has_add_permission(self, request):
        return not FreeTemplateSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description='Aktifkan halaman template gratis')
    def enable_page(self, request, queryset):
        queryset.update(is_enabled=True)
        self.message_user(request, "Halaman template gratis diaktifkan.")

    @admin.action(description='Nonaktifkan halaman template gratis (404)')
    def disable_page(self, request, queryset):
        queryset.update(is_enabled=False)
        self.message_user(request, "Halaman template gratis dinonaktifkan.")


@admin.register(FreeTemplateLead)
class FreeTemplateLeadAdmin(ModelAdmin):
    list_display = ['email', 'phone_number', 'is_verified_badge', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'phone_number']
    readonly_fields = ['email', 'phone_number', 'is_verified', 'created_at']

    @display(description='Verified OTP', boolean=True)
    def is_verified_badge(self, obj):
        return obj.is_verified

    def has_add_permission(self, request):
        return False


@admin.register(EmailVerification)
class EmailVerificationAdmin(ModelAdmin):
    list_display = ['email', 'code', 'attempts', 'verified_at', 'created_at']
    search_fields = ['email', 'code']
    readonly_fields = ['email', 'code', 'attempts', 'verified_at', 'created_at']

    def has_add_permission(self, request):
        return False


@admin.register(Voucher)
class VoucherAdmin(ModelAdmin):
    list_display = ['code', 'duration_days', 'quota_display', 'is_active_badge', 'valid_until', 'created_at']
    list_filter = ['is_active', 'valid_until']
    search_fields = ['code']

    @display(description='Kuota Terpakai')
    def quota_display(self, obj):
        return f"{obj.used_count} / {obj.max_uses}"

    @display(description='Aktif', boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(ModelAdmin):
    list_display = ['voucher', 'email', 'user', 'expires_at', 'redeemed_at']
    search_fields = ['email', 'voucher__code', 'user__username']
    readonly_fields = ['voucher', 'user', 'email', 'expires_at', 'redeemed_at']

    def has_add_permission(self, request):
        return False


@admin.register(PaidTemplateDownload)
class PaidTemplateDownloadAdmin(ModelAdmin):
    list_display = ['user', 'event_category', 'created_at']
    list_filter = ['event_category', 'created_at']
    search_fields = ['user__username', 'event_category__name']


@admin.register(TemplateDownloadCode)
class TemplateDownloadCodeAdmin(ModelAdmin):
    list_display = [
        'code', 'category_display', 'quota_display',
        'is_active_badge', 'valid_until', 'notes', 'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['code', 'notes']
    actions = ['generate_10_universal_codes', 'generate_10_wedding_codes', 'deactivate_codes']

    @display(description='Kategori')
    def category_display(self, obj):
        return obj.category.name if obj.category else 'Universal (All Categories)'

    @display(description='Kuota (Pakai / Maks)')
    def quota_display(self, obj):
        return f"{obj.used_count} / {obj.max_uses}"

    @display(
        description='Status Kode',
        label={
            'Aktif': 'success',
            'Nonaktif / Habis': 'danger',
        }
    )
    def is_active_badge(self, obj):
        if obj.is_active and (obj.max_uses == 0 or obj.used_count < obj.max_uses):
            return 'Aktif'
        return 'Nonaktif / Habis'

    @admin.action(description='Generate 10 Kode Baru: Universal (All Categories)')
    def generate_10_universal_codes(self, request, queryset):
        import secrets
        created = 0
        for _ in range(10):
            token = secrets.token_hex(3).upper()
            code_str = f"VND-MSTR-{token}"
            if not TemplateDownloadCode.objects.filter(code=code_str).exists():
                TemplateDownloadCode.objects.create(code=code_str, category=None, max_uses=1, notes="Batch Generated (Universal)")
                created += 1
        self.message_user(request, f"{created} kode universal berhasil dibuat.")

    @admin.action(description='Generate 10 Kode Baru: Wedding Kategori')
    def generate_10_wedding_codes(self, request, queryset):
        import secrets
        cat = EventCategory.objects.filter(slug='wedding').first()
        created = 0
        for _ in range(10):
            token = secrets.token_hex(3).upper()
            code_str = f"VND-WED-{token}"
            if not TemplateDownloadCode.objects.filter(code=code_str).exists():
                TemplateDownloadCode.objects.create(code=code_str, category=cat, max_uses=1, notes="Batch Generated (Wedding)")
                created += 1
        self.message_user(request, f"{created} kode kategori Wedding berhasil dibuat.")

    @admin.action(description='Nonaktifkan kode yang dipilih')
    def deactivate_codes(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} kode berhasil dinonaktifkan.")


@admin.register(TemplateDownloadLog)
class TemplateDownloadLogAdmin(ModelAdmin):
    list_display = ['downloaded_at', 'download_code', 'event_category', 'email', 'ip_address']
    list_filter = ['event_category', 'downloaded_at']
    search_fields = ['download_code__code', 'email', 'ip_address']
    readonly_fields = ['download_code', 'event_category', 'email', 'ip_address', 'user_agent', 'downloaded_at']

    def has_add_permission(self, request):
        return False


@admin.register(ExcelTemplate)
class ExcelTemplateAdmin(ModelAdmin):
    list_display = [
        'category', 'title', 'has_custom_file_badge',
        'downloads_count', 'is_active_badge', 'updated_at'
    ]
    list_filter = ['is_active', 'category']
    search_fields = ['title', 'category__name', 'subheadline']
    prepopulated_fields = {'slug': ('title',)}

    @display(description='Tipe Master File', boolean=True)
    def has_custom_file_badge(self, obj):
        return bool(obj.file)

    @display(description='Aktif', boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active
