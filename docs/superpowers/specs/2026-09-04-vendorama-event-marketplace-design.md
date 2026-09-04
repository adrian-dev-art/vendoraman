# Specification: Vendorama - Event Vendor Discovery, Escrow & Financial Guarantee Platform

**Document Version:** 1.0.0  
**Date:** 2026-09-04  
**Author:** AI Pair Architect & Lead Engineer  
**Status:** Approved by Human Partner  

---

## 1. Executive Summary & Core Business Solution

### 1.1 Problem Statement
Planning any event (weddings, corporate gatherings, birthday parties, exhibitions) involves significant financial commitment and high anxiety regarding vendor reliability. Common risks include:
- Unresponsive or defaulting vendors (*wanprestasi*).
- Discrepancy between promised portfolio and actual execution.
- Financial loss with no legal leverage or recourse for customers.

### 1.2 The Business Solution: "Trust & Security as a Service"
Vendorama addresses this by operating not as a passive listing directory, but as a **curated marketplace with financial guarantees and escrow protection**:
1. **Strictly Vetted Vendors:** Vendors are vetted before being publicly recommended.
2. **Dual-Tier Discovery:**
   - **Free Planner:** Customers explore matching vendor specifications, estimated package breakdowns, anonymized portfolios, and aggregate ratings at zero cost.
   - **Paid Planner:** For a flat fee per event, customers unlock full vendor identities, direct communication channels, unblinded portfolios, and verified PIC contacts.
3. **Event Savings Vault:** Customers can flexibly save and deposit funds toward their event budget into a secure holding vault prior to the event date.
4. **Milestone Escrow Holding:** Customer payments are safely held in escrow and disbursed to vendors in strict operational milestones (DP 30%, Mid-Term 40%, Final Release 30% post-event).
5. **Direct Financial Guarantee & Dispute Arbitration:** If a vendor fails to deliver or defaults, the platform halts escrow payouts, mediates directly, and reimburses the customer financially while issuing penalties or suspensions to the vendor.

---

## 2. User Roles & Access Control

The platform enforces three distinct user roles:

| Role | Responsibilities & Capabilities |
| :--- | :--- |
| **Customer** | - Run event matching wizard based on budget, date, city, pax, and service category.<br>- View Free Planner (anonymized specs) or purchase Paid Planner access.<br>- Create Event Savings Vault to save funds incrementally.<br>- Book verified vendors with escrow protection.<br>- Confirm event completion or file a dispute ticket with evidence for financial refund. |
| **Vendor** | - Self-register business profile, submit KYC/portfolio verification docs.<br>- Create and manage event service packages with pricing and technical specs.<br>- View booking requests and assigned milestones.<br>- Request milestone payout releases upon completing deliverables.<br>- Respond to inquiries or dispute inquiries. |
| **Admin** | - Curate and review pending vendor applications (approve/reject verification badge).<br>- Monitor platform escrow balances and transactions.<br>- Arbitrate disputes: freeze payouts, execute financial refunds to customers, and issue penalties/bans.<br>- Manage master categories, pricing thresholds, and seeder fixtures. |

---

## 3. Detailed System Architecture & Workflows

```
+-----------------------------------------------------------------------------------+
|                                 CUSTOMER JOURNEY                                  |
+-----------------------------------------------------------------------------------+
       |
       v
[ Event Matching Wizard ] ---> Input: Category, City, Date, Pax, Budget, Services
       |
       +---> [ Free Planner Mode ]  ---> Anonymized vendor cards (#CAT-01, #DEC-04)
       |                                Specs, price estimates, aggregate ratings
       |                                Action: "Beli Planner untuk Buka Profil"
       |
       +---> [ Paid Planner Unlock ] ---> Flat fee payment (e.g. IDR 150,000)
                                         Full vendor profiles, direct contacts,
                                         direct booking with Escrow Guarantee
       |
       +---> [ Event Savings Vault ] ---> Flexible pre-event savings deposits
       |                                Progress tracking towards budget goal
       |
       v
[ Escrow Booking Checkout ] ---> Funds held safely in platform escrow
       |
       +---> Milestone 1: 30% Down Payment (Operational prep)
       +---> Milestone 2: 40% Mid-Term (H-3 confirmation & delivery readiness)
       +---> Milestone 3: 30% Final Settlement (H+1 after event confirmation)
       |
       +---> [ Incident / Dispute ] ---> Escrow FROZEN immediately
                                         Admin arbitrates -> Refund to Customer
                                         Vendor penalized / suspended
```

### 3.1 Data Anonymization (Free vs Paid Planner)
To prevent disintermediation while providing transparency:
- In **Free Planner**:
  - Vendor names are masked using system codes (e.g., `Vendor Terverifikasi #CAT-102`).
  - Contact information (phone, email, social links, physical address) is suppressed in both templates and serializers.
  - Image assets display platform protection badges and omit vendor watermarks.
  - Exact pricing ranges, capacity, itemized deliverables, and customer reviews remain visible.
- In **Paid Planner**:
  - Complete business name, verified badge, telephone/WhatsApp PIC, email, address, and unmasked reviews are revealed.
  - Generates a permanent unlock record (`PlannerAccess`) linking Customer to EventPlan.

### 3.2 Event Savings Vault (Flexible Deposit)
- Customer can define an event target (e.g., "Pernikahan Dimas & Sarah - Target IDR 75,000,000 pada 12 Desember 2026").
- Customer can make ad-hoc deposits of any amount at any time (e.g., IDR 2,000,000, IDR 5,000,000).
- Visual progress bar displays total collected, percentage, and remaining amount.
- Saved funds can be applied directly to pay for booking milestones when locking vendors.

### 3.3 Milestone Escrow Engine
1. **Contract Initialization:** Total agreed price is committed to the Escrow account.
2. **Milestone 1 (DP 30%):** Disbursed to vendor upon booking confirmation to cover materials and scheduling.
3. **Milestone 2 (Mid-Term 40%):** Disbursed at H-3 after vendor submits proof of preparation/readiness.
4. **Milestone 3 (Final 30%):** Disbursed H+1 post-event when customer clicks "Konfirmasi Selesai & Berikan Ulasan", or automatically released after 48 hours if no dispute is lodged.

### 3.4 Dispute Resolution & Financial Guarantee
- If a vendor violates terms, misses deadlines, or defaults, Customer clicks `Ajukan Klaim Garansi / Dispute` with supporting details.
- System automatically changes order escrow state to `FROZEN`.
- Admin dashboard surfaces dispute ticket with priority status.
- Admin options:
  - **Approve Refund:** Unreleased escrow balance is refunded immediately to customer. If vendor already received DP, platform claims penalty against vendor balance/guarantee.
  - **Mutual Settlement:** Split disbursement based on partial delivery.
  - **Reject Dispute:** Release scheduled funds if vendor delivered according to agreed specifications.

---

## 4. Database Schema Design (Django Models)

### 4.1 Users & Profiles
- `CustomUser`: `username`, `email`, `role` (`CUSTOMER`, `VENDOR`, `ADMIN`), `phone_number`, `created_at`.
- `VendorProfile`:
  - `user`: OneToOneField to `CustomUser`.
  - `business_name`: CharField (e.g., "Kencana Art Decoration").
  - `anonymized_code`: CharField unique (e.g., "VND-DEC-014").
  - `category`: ForeignKey to `EventCategory`.
  - `city`: CharField (e.g., "Jakarta Selatan", "Bandung", "Surabaya").
  - `description`: TextField.
  - `pic_name`: CharField.
  - `contact_phone`: CharField.
  - `is_vetted`: BooleanField (Default False).
  - `verification_status`: CharField (`PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`).
  - `rating`: DecimalField (e.g., 4.9).
  - `total_completed_events`: IntegerField.

### 4.2 Categories & Services
- `EventCategory`: `name`, `slug`, `icon_name` (Lucide icon identifier, no emojis), `description`.
- `VendorPackage`:
  - `vendor`: ForeignKey to `VendorProfile`.
  - `name`: CharField (e.g., "Paket Silver Nusantara Catering").
  - `price`: DecimalField.
  - `pax_capacity`: IntegerField.
  - `specifications`: TextField (JSON or line-delimited specs).
  - `is_active`: BooleanField.

### 4.3 Planner & Event Briefs
- `EventPlan`:
  - `customer`: ForeignKey to `CustomUser`.
  - `title`: CharField.
  - `event_category`: ForeignKey to `EventCategory`.
  - `event_date`: DateField.
  - `city`: CharField.
  - `estimated_pax`: IntegerField.
  - `budget_min`: DecimalField.
  - `budget_max`: DecimalField.
  - `selected_services`: JSONField (list of requested service types).
  - `created_at`: DateTimeField.
- `PlannerAccess`:
  - `customer`: ForeignKey to `CustomUser`.
  - `event_plan`: ForeignKey to `EventPlan`.
  - `fee_paid`: DecimalField.
  - `is_unlocked`: BooleanField (Default True).
  - `unlocked_at`: DateTimeField.

### 4.4 Savings & Escrow
- `EventSavingsVault`:
  - `customer`: ForeignKey to `CustomUser`.
  - `event_plan`: OneToOneField to `EventPlan` (optional).
  - `target_title`: CharField.
  - `target_amount`: DecimalField.
  - `current_amount`: DecimalField (Default 0).
  - `target_date`: DateField.
- `SavingsDeposit`:
  - `vault`: ForeignKey to `EventSavingsVault`.
  - `amount`: DecimalField.
  - `payment_method`: CharField.
  - `created_at`: DateTimeField.
- `BookingOrder`:
  - `order_code`: CharField unique (e.g., "ORD-202609-001").
  - `customer`: ForeignKey to `CustomUser`.
  - `vendor`: ForeignKey to `VendorProfile`.
  - `package`: ForeignKey to `VendorPackage`.
  - `event_date`: DateField.
  - `total_price`: DecimalField.
  - `escrow_status`: CharField (`PENDING_PAYMENT`, `HELD`, `MILESTONE_1_PAID`, `MILESTONE_2_PAID`, `COMPLETED`, `FROZEN`, `REFUNDED`).
- `EscrowMilestone`:
  - `order`: ForeignKey to `BookingOrder`.
  - `milestone_index`: IntegerField (1, 2, 3).
  - `title`: CharField (e.g., "Down Payment 30%").
  - `percentage`: IntegerField (30, 40, 30).
  - `amount`: DecimalField.
  - `status`: CharField (`HELD`, `REQUESTED`, `RELEASED`, `DISPUTED`).
  - `released_at`: DateTimeField null=True.

### 4.5 Disputes & Financial Guarantees
- `DisputeTicket`:
  - `ticket_code`: CharField unique.
  - `order`: OneToOneField to `BookingOrder`.
  - `complainant`: ForeignKey to `CustomUser`.
  - `reason`: TextField.
  - `evidence_url`: CharField / FileField.
  - `status`: CharField (`OPEN`, `INVESTIGATING`, `REFUNDED_TO_CUSTOMER`, `SETTLED_PARTIAL`, `REJECTED`).
  - `admin_notes`: TextField.
  - `resolved_at`: DateTimeField null=True.

---

## 5. User Interface & Aesthetics Guidelines

### 5.1 Design System Tokens
- **Typography:** Modern clean sans-serif (Inter / Plus Jakarta Sans via Google Fonts).
- **Color Palette:**
  - Primary / Brand: Deep Navy Indigo (`#0f172a`, `#1e293b`) with vibrant Trust Cobalt (`#2563eb`, `#3b82f6`).
  - Accent / Trust Guarantee: Emerald Mint (`#059669`, `#10b981`).
  - Escrow Protection Badge: Amber Gold (`#d97706`, `#f59e0b`).
  - Risk / Dispute Alert: Crimson Rose (`#dc2626`, `#f43f5e`).
  - Surface & Card Backgrounds: Clean neutral slate (`#f8fafc`, `#ffffff`) with subtle 1px border cards and soft elevation shadows.
- **Iconography:** Lucide Icons (SVG / CDN). **Strictly zero emojis across all pages and notifications.**

---

## 6. Seeder Strategy (`python manage.py seed_data`)

The seeder will generate a ready-to-demo dataset:
1. **Admin User:** `admin@vendorama.id` / `admin123`.
2. **Customer Profiles (3 Distinct States):**
   - Customer 1 (`andi@example.com`): Active Event Savings Vault for upcoming wedding (target IDR 60M, saved IDR 25M).
   - Customer 2 (`budi@example.com`): Purchased Paid Planner, actively booking 2 vetted vendors.
   - Customer 3 (`citra@example.com`): History of completed corporate event + 1 resolved dispute demonstrating the financial guarantee refund.
3. **Curated Vendors (8 Profiles across 5 Cities):**
   - Catering: Nusantara Royal Catering (Jakarta), Rasa Utama Banquet (Bandung).
   - Decoration: Flora & Glow Artistic Decor (Jakarta), Mahkota Pelaminan (Surabaya).
   - Photography: Lumina Visuals Studio (Bali), Frame of Life (Yogyakarta).
   - Entertainment / Sound: SoundVibe Pro Audio (Jakarta), Harmoni Akustik & MC (Bandung).
4. **Active Orders & Escrow Records:** Sample transactions demonstrating the DP release and escrow guarantee.

---

## 7. Verification & Acceptance Criteria

- [ ] Multi-step search wizard filters vendors accurately by budget, category, and location.
- [ ] Free Planner displays anonymized vendor cards with exact specs, pricing, and ratings, suppressing contact info.
- [ ] Purchasing Paid Planner unlocks full profiles and reveals direct booking actions.
- [ ] Event Savings Vault allows adding flexible deposits and accurately tracks progress bar.
- [ ] Escrow booking displays 3-tier milestone disbursement with clear status indicators.
- [ ] Filing a dispute halts escrow disbursements and provides admin with refund controls.
- [ ] UI is responsive, professional, and strictly free of emojis.
- [ ] Seeder command populates the database cleanly in one command.
