# Design Spec: Halaman Kategori Template Excel & Unduh Kode Unik Tanpa Login

**Tanggal:** 2026-09-20  
**Status:** Approved by User  
**Penulis:** Antigravity AI  

---

## 1. Ringkasan Eksekutif (Executive Summary)
Fitur ini menyediakan halaman publik khusus untuk setiap kategori template Excel manajemen event dan pernikahan di platform Vendoraman (Wedding, Corporate, Birthday, Exhibition, Seminar, Intimate). Pembeli dari toko resmi Shopee dapat langsung mengakses halaman kategori yang dibeli, memasukkan **Kode Unik (Unique Download Code)**, dan mengunduh file `.xlsx` lengkap berformula tanpa harus registrasi atau login akun terlebih dahulu.

---

## 2. Arsitektur & Model Data (Database Schema)

### 2.1 Model `TemplateDownloadCode`
Tabel penyimpan kode unik download yang di-generate admin untuk pembeli:
- `code` (`CharField`, `max_length=40`, `unique=True`, `db_index=True`):
  Kode unik alfanumerik (misal: `VND-WED-8921A`, `VND-MSTR-7K3X1`). Validasi dilakukan case-insensitive.
- `category` (`ForeignKey(EventCategory, null=True, blank=True, on_delete=SET_NULL)`):
  Kategori target. Jika bernilai `NULL`, kode berlaku sebagai kode Universal / Master Bundle yang bisa dipakai mengunduh kategori mana pun.
- `max_uses` (`PositiveIntegerField`, `default=1`):
  Batas maksimal frekuensi pemakaian kode.
- `used_count` (`PositiveIntegerField`, `default=0`):
  Jumlah kali kode telah digunakan untuk mengunduh.
- `is_active` (`BooleanField`, `default=True`):
  Status aktifitas kode secara administratif.
- `valid_until` (`DateField`, `null=True`, `blank=True`):
  Masa kedaluwarsa kode (opsional, jika kosong berarti berlaku seumur hidup/lifetime).
- `notes` (`CharField`, `max_length=255`, `blank=True`):
  Catatan admin untuk pelacakan (misal: nomor pesanan Shopee atau nama pembeli).
- `created_at` (`DateTimeField`, `auto_now_add=True`).

### 2.2 Model `TemplateDownloadLog`
Tabel audit trail riwayat pengunduhan:
- `download_code` (`ForeignKey(TemplateDownloadCode, on_delete=CASCADE, related_name='logs')`).
- `event_category` (`ForeignKey(EventCategory, on_delete=SET_NULL, null=True)`).
- `email` (`EmailField`, `blank=True`):
  Email pembeli (opsional jika diinputkan di form).
- `ip_address` (`GenericIPAddressField`, `null=True`, `blank=True`).
- `user_agent` (`TextField`, `blank=True`).
- `downloaded_at` (`DateTimeField`, `auto_now_add=True`).

---

## 3. Alur URL & Controller (Views)

### 3.1 Routing (`vendorama/urls.py`)
1. `GET /templates/`  
   **View:** `excel_templates_catalog_view` (`core/views_templates.py` atau `core/views_home.py`)  
   **Template:** `templates/templates/catalog.html`  
   Menampilkan daftar seluruh kategori template Excel aktif, fitur utama 5-sheet, jaminan legalitas, dan tombol navigasi ke masing-masing kategori.
2. `GET /templates/<slug:category_slug>/`  
   **View:** `excel_template_category_view`  
   **Template:** `templates/templates/category_detail.html`  
   Menampilkan landing page persuasif per kategori, rincian 5 sheet, FAQ, dan Card Form Download Kode Unik.
3. `POST /templates/<slug:category_slug>/unduh/`  
   **View:** `excel_template_download_action`  
   Memproses validasi kode unik dan mengirimkan attachment file `.xlsx`.

### 3.2 Logika Validasi Kode Unik (Without Login)
1. Terima input `code` (wajib) dan `email` (opsional).
2. Format kode: bersihkan spasi awal/akhir (`strip()`), lakukan query `code__iexact=code`.
3. Validasi kegagalan:
   - Kode tidak ditemukan atau `is_active=False` -> Pesan error: "Kode unik tidak valid atau telah dinonaktifkan."
   - `valid_until` terlewati -> Pesan error: "Kode unik telah kedaluwarsa."
   - `used_count >= max_uses` -> Pesan error: "Batas pemakaian kode unik ini sudah habis."
   - `category` pada kode tidak cocok dengan kategori halaman yang dituju -> Pesan error: "Kode unik ini khusus untuk kategori [Nama Kategori Kode]. Silakan buka halaman tersebut untuk mengunduh."
4. Eksekusi sukses:
   - Tambah `used_count`: `TemplateDownloadCode.objects.filter(pk=code_obj.pk).update(used_count=F('used_count') + 1)`.
   - Simpan catatan `TemplateDownloadLog`.
   - Bangun dummy plan untuk kategori bersangkutan dan ambil vendor aktif terverifikasi (`is_vetted=True`).
   - Panggil `generate_planner_excel(plan, vendors, budget_allocations, vendor_mode='basic')`.
   - Return `HttpResponse` bertipe MIME spreadsheet OpenXML dengan header attachment `filename="Vendoraman_Template_{category.slug}.xlsx"`.

---

## 4. Antarmuka Pengguna (UI/UX Design)

### 4.1 Desain Halaman Katalog (`templates/templates/catalog.html`)
- Mengikuti sistem desain Vendoraman (`base.html`, warna `--berry`, `--sage`, `--ink`, typography Outfit & Inter).
- Hero section dengan penekanan pada:
  - Otomatis & Siap Pakai (rumus cerdas, anti-boncos).
  - Standar Industri EO/WO (checklist H-90 s/d Hari-H).
  - Legal & Berlisensi (Hak Cipta CERT-9A69A06DD581FCCE).
  - Kompatibel 100% dengan Excel & Google Sheets.
- Responsive Card Grid untuk 6 kategori:
  1. Pernikahan (Wedding)
  2. Corporate Gathering & Gala
  3. Ulang Tahun & Perayaan (Birthday)
  4. Pameran, Bazaar & Festival (Exhibition)
  5. Seminar & Workshop
  6. Intimate Gathering
- Navigasi cepat ke detail kategori dan form unduh.

### 4.2 Desain Halaman Detail Kategori (`templates/templates/category_detail.html`)
- Breadcrumb navigasi: `Beranda > Template Excel > [Nama Kategori]`.
- Hero banner persuasif sesuai persona kategori event (misal Wedding untuk calon pengantin & WO, Corporate untuk HR & Agency).
- **Download Box Interaktif (Hero Card):**
  - Input field kode unik dengan auto-uppercase CSS styling.
  - Input field email opsional.
  - Tombol aksi "Validasi Kode & Unduh Excel (.xlsx)".
  - Feedback visual (error alert & success messaging).
  - Tautan ke toko Shopee jika belum memiliki kode.
- **Visual Sheet Tabs & Previews:**
  - Sheet 1: Master Budget & Kontrol Finansial
  - Sheet 2: Direktori Vendor Terkurasi Kategori Terkait
  - Sheet 3: Timeline & Rundown Hari-H Menit-demi-Menit
  - Sheet 4: Simulator Tamu & Porsi Katering (Khusus Wedding/Event)
  - Sheet 5: Master Checklist Peralatan & Logistik
- Panduan cara membuka di Google Sheets & Excel.

---

## 5. Administrasi Django Admin

### 5.1 `TemplateDownloadCodeAdmin`
- Menampilkan kolom: `code`, `category`, `used_count` / `max_uses`, `is_active`, `valid_until`, `created_at`.
- Filter berdasarkan `category`, `is_active`, tanggal buat.
- Pencarian berdasarkan `code` dan `notes`.
- **Fitur Batch Generator:**
  - Admin Action atau Form khusus untuk men-generate N kode unik sekaligus (misal 10 atau 50 kode) dengan prefix kategori (contoh `VND-WED-XXXXX` atau `VND-MSTR-XXXXX`) dan batas pakai yang ditentukan.

### 5.2 `TemplateDownloadLogAdmin`
- Menampilkan riwayat unduhan: `downloaded_at`, `download_code`, `event_category`, `email`, `ip_address`.
- Readonly untuk menjaga integritas data audit.

---

## 6. Rencana Pengujian (Testing Strategy)
Unit test otomatis ditambahkan ke `core/tests.py`:
1. Verifikasi halaman katalog `/templates/` merespons HTTP 200 dan memuat semua kategori.
2. Verifikasi halaman detail `/templates/<slug>/` merespons HTTP 200 untuk slug valid dan HTTP 404 untuk slug fiktif.
3. Verifikasi pengunduhan sukses dengan kode kategori yang cocok: status HTTP 200, Content-Type `.xlsx`, `used_count` bertambah 1, `TemplateDownloadLog` tercatat.
4. Verifikasi pengunduhan sukses dengan kode Universal (`category=None`).
5. Verifikasi penolakan dengan kode tidak terdaftar.
6. Verifikasi penolakan dengan kode kategori yang tidak sesuai.
7. Verifikasi penolakan dengan kode yang sudah mencapai `max_uses`.
8. Verifikasi penolakan dengan kode kedaluwarsa atau nonaktif (`is_active=False`).
