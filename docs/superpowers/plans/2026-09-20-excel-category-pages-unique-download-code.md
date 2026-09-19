# Halaman Kategori Template Excel & Unduh Kode Unik Tanpa Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun halaman publik untuk setiap kategori template Excel (Wedding, Corporate, Birthday, Exhibition, Seminar, Intimate) dan sistem unduh langsung file `.xlsx` menggunakan kode unik tanpa harus registrasi/login.

**Architecture:** Model `TemplateDownloadCode` menyimpan kuota unduh dan kategori target (atau universal), sedangkan `TemplateDownloadLog` mencatat jejak audit. View publik di `core/views_templates.py` memvalidasi kode, menambah hitungan unduh, dan men-generate file spreadsheet melalui `services_export.generate_planner_excel(..., vendor_mode='basic')`.

**Tech Stack:** Django 5, SQLite, OpenPyXL, HTML5/Vanilla CSS (desain sistem Vendoraman).

**Spec:** `docs/superpowers/specs/2026-09-20-excel-category-pages-unique-download-code-design.md`

## Global Constraints
- Kode unik validasi case-insensitive dan whitespace-trimmed.
- Bebas login (tidak memerlukan akun `CustomUser`).
- File Excel yang diunduh berformat `.xlsx` dengan 5 sheet formula dan direktori vendor terkurasi kategori.
- Menggunakan skema desain Vendoraman: warna `--berry`, `--sage`, `--ink`, typography Outfit & Inter, tanpa emoji di UI sesuai aturan repo.

---

### Task 1: Database Models & Migration (`TemplateDownloadCode` & `TemplateDownloadLog`)

**Files:**
- Modify: `core/models.py:360-366`
- Create: `core/migrations/0007_templatedownloadcode_templatedownloadlog.py` (via `makemigrations`)
- Test: `core/tests.py`

**Interfaces:**
- Produces: 
  - `TemplateDownloadCode(code, category, max_uses, used_count, is_active, valid_until, notes, created_at)`
  - `TemplateDownloadCode.is_valid_for(category)` returning `(bool, str)`
  - `TemplateDownloadLog(download_code, event_category, email, ip_address, user_agent, downloaded_at)`

- [ ] **Step 1: Write failing tests for the models**
Add tests in `core/tests.py`:
```python
    def test_template_download_code_validation(self):
        from core.models import TemplateDownloadCode, EventCategory
        cat = EventCategory.objects.first()
        code = TemplateDownloadCode.objects.create(
            code="VND-TEST-01",
            category=cat,
            max_uses=2
        )
        ok, msg = code.is_valid_for(cat)
        self.assertTrue(ok)
        
        # Test quota exhaustion
        code.used_count = 2
        code.save()
        ok, msg = code.is_valid_for(cat)
        self.assertFalse(ok)
        self.assertIn("habis", msg.lower())
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python manage.py test core.tests.CoreModelTests.test_template_download_code_validation`
Expected: FAIL (cannot import `TemplateDownloadCode`).

- [ ] **Step 3: Implement `TemplateDownloadCode` and `TemplateDownloadLog` in `core/models.py`**
```python
class TemplateDownloadCode(models.Model):
    code = models.CharField(max_length=40, unique=True, db_index=True)
    category = models.ForeignKey('EventCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='download_codes')
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        cat_name = self.category.name if self.category else 'Universal (All)'
        return f"{self.code} [{cat_name}] ({self.used_count}/{self.max_uses})"

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
    download_code = models.ForeignKey(TemplateDownloadCode, on_delete=models.CASCADE, related_name='logs')
    event_category = models.ForeignKey('EventCategory', on_delete=models.SET_NULL, null=True)
    email = models.EmailField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-downloaded_at']

    def __str__(self):
        cat_str = self.event_category.name if self.event_category else '-'
        return f"{self.download_code.code} -> {cat_str} at {self.downloaded_at.strftime('%Y-%m-%d %H:%M')}"
```

- [ ] **Step 4: Run `makemigrations` and `migrate`**
Run: `python manage.py makemigrations core; python manage.py migrate`

- [ ] **Step 5: Run tests and verify they pass**
Run: `python manage.py test core.tests.CoreModelTests.test_template_download_code_validation`
Expected: PASS

- [ ] **Step 6: Commit**
Run: `git add core/models.py core/migrations/ core/tests.py; git commit -m "feat: add TemplateDownloadCode and TemplateDownloadLog models"`

---

### Task 2: Django Admin Integration & Batch Code Generator

**Files:**
- Modify: `core/admin.py`
- Test: Manual check & Django Admin check

**Interfaces:**
- Produces:
  - `TemplateDownloadCodeAdmin` with list display, filters, search, and a batch generator form/action.
  - `TemplateDownloadLogAdmin` with readonly fields for audit.

- [ ] **Step 1: Add `TemplateDownloadCodeAdmin` and `TemplateDownloadLogAdmin` in `core/admin.py`**
Include:
- List display: `code`, `category`, `quota_status`, `is_active`, `valid_until`, `notes`, `created_at`
- Admin action: `generate_10_codes_action` (or batch generation)
- Register `TemplateDownloadLog` as readonly audit log.

- [ ] **Step 2: Verify admin runs cleanly**
Run: `python manage.py check`
Expected: System check identified no issues (0 silenced).

- [ ] **Step 3: Commit**
Run: `git add core/admin.py; git commit -m "feat: register TemplateDownloadCode and TemplateDownloadLog in admin"`

---

### Task 3: Views and URLs for Catalog, Category Detail, and Direct Download

**Files:**
- Create: `core/views_templates.py`
- Modify: `vendorama/urls.py`
- Test: `core/tests.py`

**Interfaces:**
- Produces:
  - `excel_templates_catalog_view(request)` -> renders catalog page
  - `excel_template_category_view(request, category_slug)` -> renders category page
  - `excel_template_download_action(request, category_slug)` -> handles code validation & streams `.xlsx`

- [ ] **Step 1: Write failing tests for views**
In `core/tests.py`:
```python
    def test_excel_templates_catalog_view(self):
        resp = self.client.get('/templates/')
        self.assertEqual(resp.status_code, 200)

    def test_excel_template_category_view(self):
        cat = EventCategory.objects.first()
        resp = self.client.get(f'/templates/{cat.slug}/')
        self.assertEqual(resp.status_code, 200)

    def test_excel_template_download_without_login(self):
        from core.models import TemplateDownloadCode, TemplateDownloadLog
        cat = EventCategory.objects.first()
        code = TemplateDownloadCode.objects.create(code="VND-TEST-DL", category=cat, max_uses=1)
        resp = self.client.post(f'/templates/{cat.slug}/unduh/', {'code': 'vnd-test-dl', 'email': 'buyer@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        code.refresh_from_db()
        self.assertEqual(code.used_count, 1)
        self.assertTrue(TemplateDownloadLog.objects.filter(download_code=code, email='buyer@example.com').exists())
```

- [ ] **Step 2: Run tests to verify they fail**
Run: `python manage.py test core.tests.CoreViewTests.test_excel_templates_catalog_view`
Expected: FAIL (404 not found)

- [ ] **Step 3: Implement `core/views_templates.py`**
Implement the views with robust validation, clean error messages, and direct streaming of Excel via `generate_planner_excel(..., vendor_mode='basic')`.

- [ ] **Step 4: Wire URLs in `vendorama/urls.py`**
```python
    path('templates/', excel_templates_catalog_view, name='excel_templates_catalog'),
    path('templates/<slug:category_slug>/', excel_template_category_view, name='excel_template_category'),
    path('templates/<slug:category_slug>/unduh/', excel_template_download_action, name='excel_template_download'),
```

- [ ] **Step 5: Run tests and verify they pass**
Run: `python manage.py test core.tests.CoreViewTests`

- [ ] **Step 6: Commit**
Run: `git add core/views_templates.py vendorama/urls.py core/tests.py; git commit -m "feat: add views and urls for excel templates and unique code download"`

---

### Task 4: Template UI Design (`catalog.html` & `category_detail.html`)

**Files:**
- Create: `templates/templates/catalog.html`
- Create: `templates/templates/category_detail.html`
- Modify: `templates/base.html` (add navbar link to Template Excel if helpful, or keep clean)

**Interfaces:**
- Produces:
  - Responsive, high-conversion landing page for all categories (`catalog.html`)
  - Detail landing page per category with interactive unique code download form (`category_detail.html`)
  - Visual presentation of 5 Excel sheets, formula perks, compatibility info, Shopee CTA, and FAQ.

- [ ] **Step 1: Create `templates/templates/catalog.html`**
Implement layout with hero banner, 6 category cards, sheet highlights, and Shopee official store banner.

- [ ] **Step 2: Create `templates/templates/category_detail.html`**
Implement category-specific layout with breadcrumb, hero, prominent unique code download form card, 5-sheet breakdown with visual cards, compatibility guide, and FAQ.

- [ ] **Step 3: Verify templates render without template errors**
Run test suite to verify HTML rendering.

- [ ] **Step 4: Commit**
Run: `git add templates/templates/; git commit -m "feat: create UI templates for excel catalog and category detail with download form"`

---

### Task 5: Comprehensive Verification & Knowledge Graph Update

**Files:**
- Modify: `core/tests.py`
- Run: `python manage.py test`
- Run: `graphify update .`

- [ ] **Step 1: Run all test cases in `core/tests.py`**
Run: `python manage.py test core`
Ensure 100% pass rate.

- [ ] **Step 2: Run graphify update as per AGENTS.md rule**
Run: `graphify update .` (or python graphify script if configured)

- [ ] **Step 3: Final Commit**
Run: `git add .; git commit -m "test: add full verification tests for excel category pages and unique download codes"`
