from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, VendorProfile, EventCategory, EventSavingsVault, BookingOrder, DisputeTicket


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nama@email.com'}))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '081234567890'}))

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

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

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

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


class DisputeFilingForm(forms.ModelForm):
    class Meta:
        model = DisputeTicket
        fields = ['reason', 'evidence_text']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Jelaskan kronologi kelalaian vendor atau ketidaksesuaian spesifikasi'}),
            'evidence_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tautan bukti foto, dokumen, atau catatan percakapan'}),
        }
