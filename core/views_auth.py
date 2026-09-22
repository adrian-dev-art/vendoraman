from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import CustomerRegistrationForm, VendorRegistrationForm, LoginForm


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_platform_admin():
            return redirect('admin_dashboard')
        elif request.user.is_vendor_user():
            return redirect('vendor_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Selamat datang kembali, {user.username}!")
            if user.is_platform_admin():
                return redirect('admin:index')
            elif user.is_operator():
                return redirect('admin_download_codes')
            elif user.is_vendor_user():
                return redirect('vendor_dashboard')
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Username atau kata sandi tidak sesuai.")
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def register_customer_view(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Akun Customer Anda berhasil didaftarkan!")
            return redirect('customer_dashboard')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'auth/register_customer.html', {'form': form})


def register_vendor_view(request):
    if request.user.is_authenticated:
        return redirect('vendor_dashboard')

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Pendaftaran Vendor terkirim! Tim kami akan meninjau kelayakan profil Anda.")
            return redirect('vendor_dashboard')
    else:
        form = VendorRegistrationForm()

    return render(request, 'auth/register_vendor.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah keluar dari akun.")
    return redirect('home')
