# Vendorama Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Vendorama, a Django-based event vendor discovery platform featuring dual planner tiers (Free Anonymized vs Paid Full Access), an Event Savings Vault for flexible pre-event deposits, milestone-based Escrow payments (30%-40%-30%), a financial dispute guarantee system, and a comprehensive database seeder.

**Architecture:** Django monolithic application with SQLite database, cleanly modularized models (User/Auth, Catalog/Vendors, Planners, Escrow/Savings, Disputes), server-rendered templates using modern typography and Lucide SVG icons (strictly zero emojis), and dedicated dashboards for Customer, Vendor, and Admin roles.

**Tech Stack:** Python 3.14, Django 5.x, SQLite, Pillow, Lucide Icons, Vanilla CSS Design System (Slate/Cobalt/Emerald tokens).

**Spec:** `docs/superpowers/specs/2026-09-04-vendorama-event-marketplace-design.md`

## Global Constraints
- Strictly zero emojis across all templates, flash messages, seeders, and notifications. Use Lucide SVG icons instead.
- Tech stack: Django with SQLite.
- Three distinct user roles: Customer, Vendor, Admin.
- Clear separation between Free Planner (anonymized code, specs, price breakdown, aggregate rating) and Paid Planner (full identity, direct contacts, direct booking).
- Milestone escrow workflow: 30% DP, 40% Mid-Term, 30% Final Settlement post-event.
- Escrow freeze and full/partial financial refund upon customer dispute approval.
- Comprehensive database seeder runnable via `python manage.py seed_data`.

---

### Task 1: Environment Setup and Django Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `vendorama/settings.py`
- Create: `vendorama/urls.py`
- Create: `manage.py`
- Create: `core/models.py`
- Create: `core/apps.py`

**Interfaces:**
- Produces: Base Django configuration with custom user model settings, static files, and media directories.

- [ ] **Step 1: Create requirements.txt and setup virtual environment**
- [ ] **Step 2: Install Django and Pillow**
- [ ] **Step 3: Initialize Django project `vendorama` and application `core`**
- [ ] **Step 4: Configure `settings.py` for SQLite, templates, static/media, and custom user model**
- [ ] **Step 5: Verify Django startup via `python manage.py check`**
- [ ] **Step 6: Commit**

---

### Task 2: Custom User Model & Authentication (3 Roles)

**Files:**
- Modify: `core/models.py`
- Create: `core/forms.py`
- Create: `core/views_auth.py`
- Create: `templates/auth/login.html`
- Create: `templates/auth/register_customer.html`
- Create: `templates/auth/register_vendor.html`
- Test: `core/tests/test_auth.py`

**Interfaces:**
- Produces: `CustomUser` (`role` in `['CUSTOMER', 'VENDOR', 'ADMIN']`), role-aware login, registration, and logout views.

- [ ] **Step 1: Write test for user creation and role assignments**
- [ ] **Step 2: Implement `CustomUser` with roles: `CUSTOMER`, `VENDOR`, `ADMIN`**
- [ ] **Step 3: Implement registration and login views/forms**
- [ ] **Step 4: Run auth unit tests and verify they pass**
- [ ] **Step 5: Commit**

---

### Task 3: Vendor Catalog, Packages & Anonymization Models

**Files:**
- Modify: `core/models.py`
- Create: `core/views_vendor.py`
- Create: `templates/vendor/profile_manage.html`
- Create: `templates/vendor/package_form.html`
- Test: `core/tests/test_vendor_catalog.py`

**Interfaces:**
- Produces: `EventCategory`, `VendorProfile` (with `anonymized_code`, `is_vetted`, `verification_status`), `VendorPackage`.

- [ ] **Step 1: Write test for VendorProfile and anonymized code generation**
- [ ] **Step 2: Implement models `EventCategory`, `VendorProfile`, and `VendorPackage`**
- [ ] **Step 3: Implement vendor profile management & package creation forms/views**
- [ ] **Step 4: Run tests to verify catalog persistence**
- [ ] **Step 5: Commit**

---

### Task 4: Multi-Step Search Wizard & Dual Planner (Free vs Paid)

**Files:**
- Modify: `core/models.py` (add `EventPlan`, `PlannerAccess`)
- Create: `core/views_planner.py`
- Create: `templates/planner/wizard.html`
- Create: `templates/planner/results.html`
- Create: `templates/planner/vendor_detail.html`
- Test: `core/tests/test_planner.py`

**Interfaces:**
- Consumes: `VendorProfile`, `VendorPackage`, `EventCategory`.
- Produces: Multi-step matching engine, Free Planner (anonymized masks), Paid Planner unlock action.

- [ ] **Step 1: Write test for matching logic and masking of vendor details in Free Planner**
- [ ] **Step 2: Implement `EventPlan` and `PlannerAccess` models**
- [ ] **Step 3: Implement multi-step event search wizard (Category, City, Date, Pax, Budget, Services)**
- [ ] **Step 4: Implement Free Planner masked view vs Paid Planner unblinded view**
- [ ] **Step 5: Implement Unlock Planner action (mock flat-fee payment)**
- [ ] **Step 6: Run tests and verify**
- [ ] **Step 7: Commit**

---

### Task 5: Event Savings Vault (Flexible Deposit Pre-Event)

**Files:**
- Modify: `core/models.py` (add `EventSavingsVault`, `SavingsDeposit`)
- Create: `core/views_savings.py`
- Create: `templates/savings/vault_detail.html`
- Create: `templates/savings/deposit_modal.html`
- Test: `core/tests/test_savings.py`

**Interfaces:**
- Produces: Savings goal management, flexible deposit tracking, visual progress bar calculation.

- [ ] **Step 1: Write test for savings deposits and progress percentage calculations**
- [ ] **Step 2: Implement `EventSavingsVault` and `SavingsDeposit` models**
- [ ] **Step 3: Implement deposit transaction handler and vault views**
- [ ] **Step 4: Run tests and verify**
- [ ] **Step 5: Commit**

---

### Task 6: Milestone Escrow Booking Engine (30% - 40% - 30%)

**Files:**
- Modify: `core/models.py` (add `BookingOrder`, `EscrowMilestone`)
- Create: `core/views_escrow.py`
- Create: `templates/escrow/order_detail.html`
- Create: `templates/escrow/checkout.html`
- Test: `core/tests/test_escrow.py`

**Interfaces:**
- Consumes: `CustomUser`, `VendorProfile`, `VendorPackage`.
- Produces: 3-tier milestone disbursement (`DP 30%`, `Mid-Term 40%`, `Final Settlement 30%`), status triggers.

- [ ] **Step 1: Write test for milestone generation and escrow status transitions**
- [ ] **Step 2: Implement `BookingOrder` and `EscrowMilestone` models**
- [ ] **Step 3: Implement checkout view (holding funds in escrow)**
- [ ] **Step 4: Implement milestone release triggers (Vendor request -> Customer/Admin release)**
- [ ] **Step 5: Run tests and verify**
- [ ] **Step 6: Commit**

---

### Task 7: Dispute Resolution, Financial Guarantee & Admin Arbitration

**Files:**
- Modify: `core/models.py` (add `DisputeTicket`)
- Create: `core/views_dispute.py`
- Create: `core/views_admin.py`
- Create: `templates/dispute/file_dispute.html`
- Create: `templates/admin/dispute_list.html`
- Create: `templates/admin/dispute_detail.html`
- Test: `core/tests/test_dispute.py`

**Interfaces:**
- Consumes: `BookingOrder`, `EscrowMilestone`.
- Produces: Escrow freezing, Admin refund execution, Vendor penalty/suspension.

- [ ] **Step 1: Write test for dispute filing, escrow freeze, and refund execution**
- [ ] **Step 2: Implement `DisputeTicket` model and customer filing form**
- [ ] **Step 3: Implement Admin arbitration dashboard (Refund Customer, Penalize Vendor)**
- [ ] **Step 4: Run tests and verify**
- [ ] **Step 5: Commit**

---

### Task 8: Professional UI/UX Design System & Dashboards

**Files:**
- Create: `static/css/main.css`
- Create: `templates/base.html`
- Create: `templates/home.html`
- Create: `templates/customer/dashboard.html`
- Create: `templates/vendor/dashboard.html`
- Create: `templates/admin/dashboard.html`

**Interfaces:**
- Produces: Responsive modern UI, Lucide SVG icon integration, zero emojis, role-specific navbars and dashboard views.

- [ ] **Step 1: Implement `main.css` design tokens (Slate, Cobalt, Emerald, Amber, Crimson)**
- [ ] **Step 2: Implement `base.html` with SVG Lucide icon helper/macro**
- [ ] **Step 3: Implement landing page (`home.html`) with Hero, Trust Guarantee highlights, and Wizard entrance**
- [ ] **Step 4: Implement Role-specific dashboards for Customer, Vendor, and Admin**
- [ ] **Step 5: Verify responsiveness and zero emojis compliance**
- [ ] **Step 6: Commit**

---

### Task 9: Comprehensive Seeder Management Command (`seed_data`)

**Files:**
- Create: `core/management/commands/seed_data.py`
- Test: `core/tests/test_seeder.py`

**Interfaces:**
- Produces: Ready-to-demo dataset: 1 Admin, 3 Customers (savings state, paid planner state, completed dispute state), 8 Curated Vendors across categories/cities, packages, milestones, and sample disputes.

- [ ] **Step 1: Write test to verify `seed_data` command execution**
- [ ] **Step 2: Implement `seed_data.py` with realistic Indonesian event vendor data and scenarios**
- [ ] **Step 3: Execute `python manage.py seed_data` and verify record counts**
- [ ] **Step 4: Commit**

---

### Task 10: End-to-End System Verification

**Files:**
- Verification across browser flows and test suite.

- [ ] **Step 1: Run full unit test suite (`python manage.py test`)**
- [ ] **Step 2: Verify Free Planner vs Paid Planner masking in browser**
- [ ] **Step 3: Verify Savings Vault deposit progress bar**
- [ ] **Step 4: Verify Escrow Milestone release and Dispute refund workflow**
- [ ] **Step 5: Final documentation update and commit**
