from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('VENDOR', 'Vendor'),
        ('ADMIN', 'Admin / Platform Operator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    phone_number = models.CharField(max_length=25, blank=True, default='')

    def is_customer(self):
        return self.role == 'CUSTOMER'

    def is_vendor_user(self):
        return self.role == 'VENDOR'

    def is_platform_admin(self):
        return self.role == 'ADMIN' or self.is_superuser


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
        return f"Deposit Rp {self.amount:,} to {self.vault.title}"


class BookingOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Menunggu Pembayaran Escrow'),
        ('HELD', 'Dana Aman Ditahan di Escrow'),
        ('MILESTONE_1_PAID', 'Termin 1 (DP 30%) Dicairkan'),
        ('MILESTONE_2_PAID', 'Termin 2 (Pelaksanaan 40%) Dicairkan'),
        ('COMPLETED', 'Event Sukses & Pelunasan 30% Selesai'),
        ('FROZEN', 'Escrow Dibekukan (Dispute Aktif)'),
        ('REFUNDED', 'Dana Dikembalikan ke Customer (Garansi Finansial)'),
    ]

    order_code = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='orders')
    package = models.ForeignKey(VendorPackage, on_delete=models.CASCADE, related_name='orders')
    event_date = models.DateField()
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    escrow_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_code} - {self.vendor.business_name} ({self.escrow_status})"

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def create_default_milestones(self):
        if not self.milestones.exists():
            dp_amount = round(self.total_price * 30 / 100)
            mid_amount = round(self.total_price * 40 / 100)
            final_amount = self.total_price - dp_amount - mid_amount

            EscrowMilestone.objects.create(
                order=self,
                milestone_index=1,
                title='Down Payment (DP) Persiapan Vendor',
                percentage=30,
                amount=dp_amount,
                status='HELD'
            )
            EscrowMilestone.objects.create(
                order=self,
                milestone_index=2,
                title='Termin Pelaksanaan & Kesiapan H-3',
                percentage=40,
                amount=mid_amount,
                status='HELD'
            )
            EscrowMilestone.objects.create(
                order=self,
                milestone_index=3,
                title='Pelunasan Akhir Pasca-Event Sukses (H+1)',
                percentage=30,
                amount=final_amount,
                status='HELD'
            )


class EscrowMilestone(models.Model):
    STATUS_CHOICES = [
        ('HELD', 'Ditahan di Escrow'),
        ('REQUESTED', 'Pencairan Diajukan Vendor'),
        ('RELEASED', 'Dana Dicairkan ke Vendor'),
        ('DISPUTED', 'Ditahan karena Sengketa'),
    ]

    order = models.ForeignKey(BookingOrder, on_delete=models.CASCADE, related_name='milestones')
    milestone_index = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=150)
    percentage = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='HELD')
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['milestone_index']

    def __str__(self):
        return f"{self.order.order_code} - M{self.milestone_index} ({self.title}): Rp {self.amount:,}"


class DisputeTicket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Dispute Diajukan - Escrow Dibekukan'),
        ('INVESTIGATING', 'Sedang Dimediasi / Investigasi Tim Vendorama'),
        ('REFUNDED_TO_CUSTOMER', 'Garansi Finansial Disetujui: 100% Refund ke Customer'),
        ('SETTLED_PARTIAL', 'Penyelesaian Parsial Disepakati'),
        ('REJECTED', 'Dispute Ditolak - Payout Dilanjutkan'),
    ]

    ticket_code = models.CharField(max_length=50, unique=True)
    order = models.OneToOneField(BookingOrder, on_delete=models.CASCADE, related_name='dispute')
    complainant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disputes')
    reason = models.TextField(help_text='Rincian keluhan atau kelalaian vendor')
    evidence_text = models.TextField(blank=True, help_text='Link bukti atau rincian saksi/fakta lapangan')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    admin_notes = models.TextField(blank=True, default='')
    penalty_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Dispute {self.ticket_code} for {self.order.order_code}"

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = f"DSP-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
