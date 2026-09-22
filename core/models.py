from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('VENDOR', 'Vendor'),
        ('OPERATOR', 'Operator / CS Shopee'),
        ('ADMIN', 'Admin / Platform Operator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    phone_number = models.CharField(max_length=25, blank=True, default='')
    premium_until = models.DateField(null=True, blank=True, help_text='Langganan premium aktif sampai tanggal ini')

    def is_customer(self):
        return self.role == 'CUSTOMER'

    def is_vendor_user(self):
        return self.role == 'VENDOR'

    def is_operator(self):
        return self.role == 'OPERATOR'

    def is_platform_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    def can_manage_shopee_and_templates(self):
        return self.role in ('OPERATOR', 'ADMIN') or self.is_superuser

    def is_premium(self):
        import datetime
        return bool(self.premium_until and self.premium_until >= datetime.date.today())


class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon_name = models.CharField(max_length=50, default='calendar', help_text='Lucide icon name (strictly no emoji)')
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'Event Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorProfile(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved & Vetted'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended / Penalized'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=200)
    anonymized_code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='vendors')
    city = models.CharField(max_length=100, default='Jakarta')
    address = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField()
    pic_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=30)
    contact_email = models.EmailField()
    is_vetted = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    total_completed_events = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} ({self.anonymized_code})"

    def save(self, *args, **kwargs):
        if not self.anonymized_code:
            prefix = self.category.slug[:3].upper() if self.category else "VND"
            self.anonymized_code = f"VND-{prefix}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class VendorPackage(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    pax_capacity = models.PositiveIntegerField(default=100)
    specifications = models.TextField(help_text='Itemized specifications (comma or newline separated)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.business_name} - {self.name}"

    def get_spec_list(self):
        return [line.strip() for line in self.specifications.splitlines() if line.strip()]

    @property
    def platform_fee(self):
        return round(self.price * Decimal('0.10'))

    @property
    def net_price(self):
        return self.price - self.platform_fee


class EventPlan(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_plans')
    title = models.CharField(max_length=200)
    event_category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True)
    event_date = models.DateField()
    city = models.CharField(max_length=100)
    estimated_pax = models.PositiveIntegerField(default=100)
    budget_min = models.DecimalField(max_digits=12, decimal_places=0)
    budget_max = models.DecimalField(max_digits=12, decimal_places=0)
    selected_services = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.customer.username})"

    def is_unlocked_for(self, user):
        if not user.is_authenticated:
            return False
        if user == self.customer or user.is_staff or user.role == 'ADMIN':
            return self.access_unlocks.filter(is_unlocked=True).exists()
        return False


class PlannerAccess(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='planner_accesses')
    event_plan = models.ForeignKey(EventPlan, on_delete=models.CASCADE, related_name='access_unlocks')
    fee_paid = models.DecimalField(max_digits=10, decimal_places=0, default=150000)
    is_unlocked = models.BooleanField(default=True)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'event_plan')

    def __str__(self):
        return f"Paid Access: {self.customer.username} -> {self.event_plan.title}"


class EventSavingsVault(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='savings_vaults')
    event_plan = models.OneToOneField(EventPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='savings_vault')
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=0)
    current_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vault: {self.title} ({self.customer.username})"

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0
        pct = (self.current_amount / self.target_amount) * 100
        return min(round(float(pct), 1), 100.0)

    @property
    def remaining_amount(self):
        rem = self.target_amount - self.current_amount
        return max(rem, 0)


class SavingsDeposit(models.Model):
    vault = models.ForeignKey(EventSavingsVault, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_method = models.CharField(max_length=50, default='Virtual Account (Escrow Vault)')
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        amt_str = f"{int(self.amount):,}".replace(',', '.')
        return f"Deposit Rp {amt_str} to {self.vault.title}"


class BookingOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Konfirmasi Vendor'),
        ('CONFIRMED', 'Dikonfirmasi Vendor'),
        ('COMPLETED', 'Event Selesai'),
        ('CANCELLED', 'Dibatalkan'),
    ]
    COMMISSION_STATUS_CHOICES = [
        ('PENDING', 'Menunggu Settlement'),
        ('PAID', 'Komisi Terbayar'),
    ]

    order_code = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='orders')
    package = models.ForeignKey(VendorPackage, on_delete=models.CASCADE, related_name='orders')
    event_date = models.DateField()
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')

    # Commission-based fee from vendor
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="Persentase komisi platform yang diambil dari vendor (misal 10.00%)"
    )
    commission_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Nominal komisi platform"
    )
    vendor_net_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Pendapatan bersih yang diterima vendor setelah potongan komisi"
    )
    commission_status = models.CharField(
        max_length=20, choices=COMMISSION_STATUS_CHOICES, default='PENDING'
    )

    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_code} - {self.vendor.business_name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        if self.total_price is not None:
            from decimal import Decimal
            rate = Decimal(str(self.commission_rate)) if self.commission_rate is not None else Decimal('10.00')
            price = Decimal(str(self.total_price))
            self.commission_amount = (price * rate / Decimal('100')).quantize(Decimal('1'))
            self.vendor_net_amount = price - self.commission_amount
        super().save(*args, **kwargs)


class FreeTemplateSettings(models.Model):
    """Singleton: controls the hidden free-template download page.

    The page is NOT linked from the navbar/footer/sitemap — it is only
    reachable via its direct URL, and only when ``is_enabled`` is True.
    Toggle it from Django Admin (Core > Free template settings).
    """
    is_enabled = models.BooleanField(
        default=False,
        help_text='Aktif = halaman template gratis bisa dibuka & file bisa diunduh. '
                  'Nonaktif = halaman mengembalikan 404.'
    )
    original_price = models.DecimalField(
        max_digits=12, decimal_places=0, default=15000,
        help_text='Harga coret yang ditampilkan (misal 15000 = Rp 15.000). Harga bayar selalu Rp 0.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Free template settings'
        verbose_name_plural = 'Free template settings'

    def __str__(self):
        state = 'AKTIF' if self.is_enabled else 'NONAKTIF'
        return f'Template Gratis: {state} (coret Rp {int(self.original_price):,})'

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton: exactly one row
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'is_enabled': False})
        return obj


class FreeTemplateLead(models.Model):
    """Email + HP captured before a free-template download (lead magnet)."""
    email = models.EmailField()
    phone_number = models.CharField(max_length=25)
    is_verified = models.BooleanField(default=False, help_text='True = e-mail lolos verifikasi OTP')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        mark = '✓' if self.is_verified else '?'
        return f'{self.email} / {self.phone_number} [{mark}]'


class EmailVerification(models.Model):
    """One-time 6-digit code proving an e-mail address really exists."""
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    attempts = models.PositiveIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP {self.email} ({self.code})'

    def is_expired(self):
        import datetime
        from django.utils import timezone
        return timezone.now() > self.created_at + datetime.timedelta(minutes=15)

    @classmethod
    def new_code(cls, email):
        import secrets
        email = email.strip().lower()
        cls.objects.filter(email=email, verified_at__isnull=True).delete()
        return cls.objects.create(email=email, code=f'{secrets.randbelow(900000) + 100000}')


class Voucher(models.Model):
    """Voucher langganan (dijual via Shopee, diaktivasi langsung di aplikasi).

    No payment gateway: admin creates codes, customer redeems a code,
    redemption extends the subscription. Usage counted to enforce max_uses.
    """
    code = models.CharField(max_length=32, unique=True, help_text='Kode persis seperti di Shopee (huruf besar disarankan)')
    duration_days = models.PositiveIntegerField(default=30, help_text='Berapa hari langganan bertambah per redeem')
    max_uses = models.PositiveIntegerField(default=1, help_text='Berapa kali kode ini bisa dipakai total')
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True, help_text='Opsional: kode kedaluwarsa tanggal ini')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.code} ({self.used_count}/{self.max_uses} dipakai)'

    def usages_left(self):
        return max(self.max_uses - self.used_count, 0)

    def is_valid(self):
        import datetime
        if not self.is_active:
            return False, 'Voucher sudah dinonaktifkan.'
        if self.valid_until and self.valid_until < datetime.date.today():
            return False, 'Voucher sudah kedaluwarsa.'
        if self.used_count >= self.max_uses:
            return False, 'Kuota pemakaian voucher ini sudah habis.'
        return True, ''


class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='voucher_redemptions')
    email = models.EmailField()
    expires_at = models.DateField(help_text='Langganan aktif sampai tanggal ini')
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-redeemed_at']

    def __str__(self):
        return f'{self.voucher.code} → {self.email} (s/d {self.expires_at})'


class PaidTemplateDownload(models.Model):
    """Satu user hanya boleh memilih SATU template kategori berbayar."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='paid_template')
    event_category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        cat = self.event_category.name if self.event_category else '-'
        return f'{self.user.username} → {cat}'


class TemplateDownloadCode(models.Model):
    """Kode unik untuk mengunduh template Excel kategori tertentu tanpa perlu login."""
    code = models.CharField(max_length=40, unique=True, db_index=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='download_codes')
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    # Tracking fields
    first_visited_at = models.DateTimeField(null=True, blank=True, help_text="Waktu pertama kali pembeli membuka link web")
    last_activity_at = models.DateTimeField(null=True, blank=True, help_text="Waktu aktivitas terakhir di web")
    time_spent_seconds = models.PositiveIntegerField(default=0, help_text="Durasi berada di web dalam detik")
    visit_count = models.PositiveIntegerField(default=0, help_text="Frekuensi pembukaan halaman web")
    last_page_viewed = models.CharField(max_length=255, blank=True, default='', help_text="Halaman terakhir yang dilihat")
    downloaded_category = models.ForeignKey(
        EventCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='downloaded_codes', help_text="Kategori template yang akhirnya diunduh"
    )
    downloaded_at = models.DateTimeField(null=True, blank=True, help_text="Waktu unduh file")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    device_type = models.CharField(max_length=50, blank=True, default='', help_text="Mobile / Desktop / Tablet")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        cat_name = self.category.name if self.category else 'Universal (All)'
        return f"{self.code} [{cat_name}] ({self.used_count}/{self.max_uses})"

    @property
    def formatted_time_spent(self):
        if not self.first_visited_at and self.time_spent_seconds == 0:
            return "Belum dibuka"
        secs = self.time_spent_seconds
        if secs < 60:
            return f"{secs} dtk"
        mins = secs // 60
        rem_secs = secs % 60
        return f"{mins}m {rem_secs}s"

    @property
    def tracking_badge(self):
        if self.used_count >= self.max_uses:
            return {'label': 'Sudah Download', 'color': '#2e7d32', 'bg': 'rgba(46, 125, 50, 0.12)'}
        if self.first_visited_at:
            return {'label': 'Pernah Buka Web', 'color': '#b45309', 'bg': 'rgba(217, 119, 6, 0.12)'}
        return {'label': 'Belum Dibuka', 'color': '#64748b', 'bg': 'rgba(100, 116, 139, 0.1)'}

    def generate_chat_message(self, base_url='https://vendoraman.vitnite.cloud'):
        link = f"{base_url.rstrip('/')}/templates/?code={self.code}"
        return (
            f"Halo Kak! Terima kasih banyak sudah order di Vendoraman Official. ✨\n\n"
            f"Ini kode akses unik untuk unduh template Anda:\n"
            f"🔑 KODE AKSES: {self.code}\n\n"
            f"📥 LINK UNDUH LANGSUNG:\n{link}\n\n"
            f"⚠️ PENTING SEBELUM MEMILIH TEMPLATE:\n"
            f"1. Kode akses ini bersifat UNIVERSAL (dapat digunakan untuk template kategori apa pun: Pernikahan, Corporate, Ulang Tahun, Pameran, Seminar, atau Intimate Gathering).\n"
            f"2. Kode ini HANYA BISA DIGUNAKAN 1 KALI UNDUH.\n"
            f"3. Mohon pastikan Kakak memilih kategori template yang benar dan sesuai kebutuhan sebelum menekan tombol unduh.\n\n"
            f"CARA PENGGUNAAN:\n"
            f"1. Klik link di atas (atau buka menu Template Excel).\n"
            f"2. Pilih kategori template yang ingin Kakak unduh.\n"
            f"3. Masukkan kode akses di atas (akan terisi otomatis jika klik link).\n"
            f"4. Klik \"Unduh Template Excel\", file .xlsx berformula lengkap akan langsung tersimpan di perangkat Kakak.\n\n"
            f"Jika butuh bantuan atau ada pertanyaan teknis, silakan balas chat ini ya Kak. Selamat merencanakan event! 😊🙏"
        )

    def is_valid_for(self, target_category):
        import datetime
        if not self.is_active:
            return False, "Kode unik tidak aktif atau telah dinonaktifkan."
        if self.valid_until and self.valid_until < datetime.date.today():
            return False, "Kode unik telah kedaluwarsa."
        if self.used_count >= self.max_uses:
            return False, "Batas pemakaian kode unik ini sudah habis."
        if self.category and self.category != target_category:
            return False, f"Kode ini hanya berlaku untuk kategori '{self.category.name}'."
        return True, ""


class TemplateDownloadLog(models.Model):
    """Mencatat riwayat audit pemakaian kode unik unduh file template."""
    download_code = models.ForeignKey(TemplateDownloadCode, on_delete=models.CASCADE, related_name='logs')
    event_category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True)
    email = models.EmailField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-downloaded_at']

    def __str__(self):
        cat_str = self.event_category.name if self.event_category else '-'
        return f"{self.download_code.code} -> {cat_str} at {self.downloaded_at.strftime('%Y-%m-%d %H:%M')}"


class ExcelTemplate(models.Model):
    """Katalog file template Excel yang dapat dikelola oleh Operator CS dan Admin."""
    category = models.OneToOneField(
        EventCategory,
        on_delete=models.CASCADE,
        related_name='excel_template',
        help_text='Kategori event yang diasosiasikan dengan template ini'
    )
    title = models.CharField(max_length=200, help_text='Judul lengkap / headline template')
    slug = models.SlugField(unique=True, help_text='Slug URL template')
    subheadline = models.TextField(blank=True, default='', help_text='Deskripsi singkat / subheadline manfaat')
    target_audience = models.CharField(max_length=255, blank=True, default='', help_text='Target pengguna (misal: Calon Pengantin & WO)')
    estimated_savings = models.CharField(max_length=255, blank=True, default='', help_text='Estimasi penghematan (misal: Hemat s/d Rp 15 - 30 Juta)')
    key_perks = models.JSONField(default=list, blank=True, help_text='Daftar checklist keunggulan (JSON array of strings)')
    file = models.FileField(
        upload_to='excel_templates/',
        null=True,
        blank=True,
        help_text='File master .xlsx kustom (opsional; jika kosong maka otomatis digenerate oleh sistem)'
    )
    shopee_product_url = models.URLField(blank=True, default='', help_text='Tautan produk di Shopee (opsional)')
    is_active = models.BooleanField(default=True, help_text='Status aktif di katalog publik')
    downloads_count = models.PositiveIntegerField(default=0, help_text='Akumulasi total unduhan')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__name']
        verbose_name = 'Excel Template'
        verbose_name_plural = 'Excel Templates'

    def __str__(self):
        return f"{self.title} ({self.category.name})"

    def get_perks_list(self):
        if isinstance(self.key_perks, list):
            return self.key_perks
        return []


