from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, VendorProfile, EventCategory, EventSavingsVault, BookingOrder


class CustomerRegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nama@email.com'}))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '081234567890'}))
    # Honeypot anti-spam: invisible to humans, bots fill it. Must stay empty.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Pendaftaran ditolak.')
        return ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CUSTOMER'
        if commit:
            user.save()
        return user


class VendorRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    business_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Usaha / Brand Vendor'}))
    category = forms.ModelChoiceField(queryset=EventCategory.objects.all(), required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    city = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kota Operasional (misal: Jakarta Selatan)'}))
    pic_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap PIC / Penanggung Jawab'}))
    description = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Profil singkat dan spesialisasi layanan Anda'}))
    # Honeypot anti-spam: invisible to humans, bots fill it. Must stay empty.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Pendaftaran ditolak.')
        return ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'VENDOR'
        if commit:
            user.save()
            VendorProfile.objects.create(
                user=user,
                business_name=self.cleaned_data['business_name'],
                category=self.cleaned_data['category'],
                city=self.cleaned_data['city'],
                pic_name=self.cleaned_data['pic_name'],
                contact_phone=self.cleaned_data['phone_number'],
                contact_email=self.cleaned_data['email'],
                description=self.cleaned_data['description'],
                verification_status='PENDING',
                is_vetted=False
            )
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class EventSearchWizardForm(forms.Form):
    category = forms.ModelChoiceField(queryset=EventCategory.objects.all(), empty_label='Pilih Kategori Event', widget=forms.Select(attrs={'class': 'form-select'}))
    city = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Jakarta, Bandung, Surabaya'}))
    event_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    estimated_pax = forms.IntegerField(min_value=10, initial=200, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Estimasi jumlah tamu'}))
    budget_min = forms.DecimalField(max_digits=12, decimal_places=0, initial=10000000, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Budget minimal'}))
    budget_max = forms.DecimalField(max_digits=12, decimal_places=0, initial=50000000, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Budget maksimal'}))
    event_title = forms.CharField(required=True, initial='Rencana Event Saya', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Beri nama rencana event ini'}))


class EventSavingsVaultForm(forms.ModelForm):
    class Meta:
        model = EventSavingsVault
        fields = ['title', 'target_amount', 'target_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Tabungan Pernikahan Dimas & Sarah'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Target total dana yang dibutuhkan'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class SavingsDepositForm(forms.Form):
    amount = forms.DecimalField(min_value=50000, max_digits=12, decimal_places=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nominal setoran (contoh: 5000000)'}))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Catatan setoran (opsional)'}))


class BookingOrderForm(forms.ModelForm):
    class Meta:
        model = BookingOrder
        fields = ['event_date', 'notes']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Catatan khusus untuk vendor terkait acara...'}),
        }


class FreeTemplateLeadForm(forms.Form):
    """Lead magnet gate: e-mail + HP wajib diisi sebelum tombol unduh terbuka."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nama@email.com', 'autocomplete': 'email'}))
    phone_number = forms.CharField(
        required=True, min_length=9, max_length=16,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '081234567890', 'inputmode': 'tel', 'autocomplete': 'tel'}))

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip().replace(' ', '').replace('-', '')
        digits = phone[1:] if phone.startswith('+') else phone
        if not digits.isdigit():
            raise forms.ValidationError('Nomor HP hanya boleh berisi angka (contoh: 081234567890).')
        if len(digits) < 9 or len(digits) > 16:
            raise forms.ValidationError('Nomor HP harus 9–16 digit angka.')
        return phone


class OtpVerificationForm(forms.Form):
    """6-digit code sent to the visitor's e-mail (proves the address exists)."""
    code = forms.CharField(
        required=True, min_length=6, max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123456',
                                      'inputmode': 'numeric', 'autocomplete': 'one-time-code',
                                      'style': 'letter-spacing: 6px; text-align: center; font-size: 1.3rem; font-weight: 700;'}))

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit():
            raise forms.ValidationError('Kode OTP hanya berisi 6 digit angka.')
        return code


class VoucherRedeemForm(forms.Form):
    """Activate a Shopee-bought voucher code directly in the app."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nama@email.com yang dipakai beli voucher'}))
    code = forms.CharField(
        required=True, max_length=32,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: SHOPEE-PREMIUM-30',
                                      'style': 'text-transform: uppercase;'}))

    def clean_code(self):
        return self.cleaned_data.get('code', '').strip().upper()

