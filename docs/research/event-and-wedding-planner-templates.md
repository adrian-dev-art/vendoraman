# Deep Research: Event & Wedding Planner Templates (Architecture, Data Structures, and Calculations)

**Document:** `docs/research/event-and-wedding-planner-templates.md`  
**Date:** 2026-09-06  
**Purpose:** Benchmark industry-standard event and wedding planning spreadsheets and presentation decks to maximize the value proposition of Vendorama's Paid Planner export pack.

---

## 1. Executive Summary: What Professional Event & Wedding Planners Manage

Professional event planners, Wedding Organizers (WO), and corporate event agencies do not treat event planning as a simple to-do list. They operate around **five core management pillars**:

```
+-------------------------------------------------------------------------------------------------------+
|                                    PROFESSIONAL PLANNER PILLARS                                       |
+-------------------------------------------------------------------------------------------------------+
|  1. FINANCIAL & CASHFLOW   |  2. VENDOR PROCUREMENT    |  3. TIMELINE & RUNSHEET |  4. GUEST & CATERING|
|  - Total budget ceilings   |  - Comparative matrix     |  - Month-by-month prep  |  - Pax count       |
|  - Category allocations    |  - Vetted packages & specs|  - Hari-H minute-by-min |  - Porsi ratio     |
|  - Milestone payments      |  - PIC & WhatsApp contact |  - Technical cues (A/V) |  - Seating & VIPs  |
|  - Variance (under/over)   |  - Contract & DP status   |  - Contingency buffers  |  - Dietary / crew  |
+-------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
                                      [ 5. STAKEHOLDER PITCH DECK ]
                               - Presentation deck for couple/family/clients
                               - Visual concept, budget summary, vendor cards
```

---

## 2. Deep Dive: The Anatomy of Master Planner Spreadsheets (Excel / Google Sheets)

Top industry templates (e.g. **Vertex42**, **The Knot**, **Smartsheet**, **Bridestory/Weddingku WO standards**) structure their workbooks across distinct tabs:

### Tab 1: Financial Dashboard & Budget Calculator
*What it manages:* Financial discipline, avoiding cost overruns, and cashflow disbursement.
* **Columns & Data Fields:**
  1. `Category` (Venue, Catering, Decoration, Photo/Video, Entertainment/MC, Attire/MUA, Souvenir/Invitation, Contingency).
  2. `Item Description` (e.g. Buffet 500 pax, Pelaminan 12m, Cinematic Teaser, Sound System 10,000 watt).
  3. `Vendor Assigned` (Name of selected vendor).
  4. `Estimated / Target Cost (Rp)` (Planned budget allocation).
  5. `Actual / Quotation Cost (Rp)` (Agreed contract price).
  6. `Variance (Rp)` (Difference: Savings vs Over-budget).
  7. `Down Payment / DP (Rp)` (Amount disbursed upfront).
  8. `Remaining Balance (Rp)` (Pending milestone payment).
  9. `Due Date` (Deadline for settlement).
  10. `Payment Status` (`Belum Bayar`, `DP 30% Terbayar`, `Lunas`).

* **What it counts (Formulas & Automated Calculations):**
  - **Total Projected vs Actual:** `=SUM(E5:E50)` and `=SUM(F5:F50)`
  - **Variance Calculation:** `=E5-F5` (Positive = Under Budget / Savings, Negative = Over Budget)
  - **Variance %:** `=(Actual - Estimated) / Estimated * 100`
  - **Category Weight Distribution:** `=(Category_Total / Total_Budget) * 100`
    * *Industry Benchmark Allocations:*
      - Catering & Venue: 40% – 50%
      - Decoration & Styling: 20% – 25%
      - Photography & Videography: 10% – 15%
      - Sound, Lighting, Band & MC: 10% – 12%
      - Buffer / Contingency Reserve: 5% – 10%
  - **Cost per Pax:** `=Total_Budget / Total_Pax`

---

### Tab 2: Curated Vendor Directory & Procurement Matrix
*What it manages:* Side-by-side vendor evaluation, official contacts, and booking deliverables.
* **Columns & Data Fields:**
  1. `No.`
  2. `Category` (Catering / Dekor / Dokumentasi / dll).
  3. `Nama Vendor Resmi` (Unmasked official brand name).
  4. `Status Kurasi` (`Vetted Partner`, `Verified Badge`, `Escrow Protected`).
  5. `Rating & Portofolio` (e.g., 4.9 / 5.0 - 120+ event).
  6. `Nama PIC (Person in Charge)` & Jabatan.
  7. `Nomor WhatsApp / Telp PIC` (Direct click-to-chat URL).
  8. `Email Resmi & Alamat Kantor`.
  9. `Nama Paket Terpilih` (e.g. Paket Gold Nusantara).
  10. `Harga Paket (Rp)` & `Kapasitas Pax`.
  11. `Spesifikasi & Deliverables` (Itemized scope of work).
  12. `Status Kontrak` (`Rekomendasi`, `Konsultasi`, `Locked / Booked`).

* **What it counts:**
  - Total committed spend across selected vendors.
  - Number of locked vs open vendor slots.

---

### Tab 3: Planning Milestones & Hari-H Runsheet (Timeline)
*What it manages:* Countdown deadlines and operational precision on the day of the event.

#### A. Countdown Checklist (D-90 down to D-1)
* **Milestones:**
  - **H-90 (Bulan ke-3):** Kunci venue, tentukan tema, pilih katering & food testing, booking vendor utama via DP escrow.
  - **H-60 (Bulan ke-2):** Finalisasi dekorasi, busana/seragam, draft rundown, pesan undangan & souvenir.
  - **H-30 (Bulan ke-1):** Technical meeting (TM) gabungan seluruh vendor, konfirmasi jumlah pax katering, fitting final.
  - **H-14 (Minggu ke-2):** Distribusi undangan selesai, rekapitulasi RSVP tamu, koordinasi parkir & keamanan venue.
  - **H-7 (Minggu terakhir):** Konfirmasi kesiapan vendor (H-7 readiness check), gladi resik, pelunasan milestone.
  - **H-1:** Loading dekorasi & sound, check-in keluarga/panitia di hotel venue, briefing singkat.

#### B. Hari-H Master Runsheet (Minute-by-Minute Table)
* **Columns:**
  1. `Waktu / Durasi` (e.g., 06.00 – 07.30, 08.00 – 09.30).
  2. `Sesi / Agenda` (Make up pengantin, Akad Nikah / Blessing, Kirab Pengantin, Resepsi, Lempar Bunga).
  3. `Lokasi / Area` (Ruang Rias, Ballroom Utama, Foyer).
  4. `PIC Utama` (WO Coordinator, MC, Vendor Lead).
  5. `Vendor Terlibat` (Dekorasi standby, Catering buffet open, Foto/Video candid shot, Sound audio cue).
  6. `Catatan Teknis / Audio Cue` (Backsound instrumental lembut, lighting spotlight panggung).

---

### Tab 4: Guest List, Pax & Catering Multiplier Calculator
*What it manages:* Estimating food consumption and seating capacity without shortages or massive waste.
* **Data Fields:**
  - `Guest Name`, `Category` (Keluarga Inti, VIP, Rekan Kerja, Teman Sekolah).
  - `Pax Estimasi` (e.g., 1 Undangan Fisik/Digital = 2 Pax kehadiran).
  - `RSVP Status` (`Hadir`, `Tidak Hadir`, `Belum Konfirmasi`).
* **What it counts (Catering Multiplier Formulas in Indonesia):**
  - **Total Estimated Attendance:** `=Total_Undangan * 1.8` to `2.0`
  - **Buffet vs Stall (Gubukan) Ratio:**
    - Standard Indonesia: 50% – 60% Porsi Buffet, 40% – 50% Porsi Food Stalls (biasanya 4x–5x porsi stall per tamu).
  - **Crew & Panitia Meals Buffer:** `Total Tamu + (Panitia + Vendor Crew + 10% Safety Buffer)`.

---

## 3. The Anatomy of an Executive Event Presentation Deck (PDF / PPT)

When couples, event committees, or corporate planners prepare an event, they must present the plan to family elders, corporate directors, or sponsors. They need a **concise, visually stunning pitch deck (10–12 slides)**, not a raw spreadsheet:

| Slide # | Slide Title | Core Purpose & Visual Content |
| :--- | :--- | :--- |
| **Slide 1** | **Title & Executive Brief** | Event title, couple/company names, date, venue city, guest count, and Vendorama Vetted seal. |
| **Slide 2** | **Event Vision & Concept Mood** | Color palette, aesthetic keywords (e.g. Modern Rustic, Traditional Elegance), core vibe. |
| **Slide 3** | **Budget Strategy & Allocation** | Pie/bar breakdown showing how the budget is distributed across categories and reserve funds. |
| **Slide 4** | **Curated Caterer Showcase** | Caterer profile, signature menu, hygiene rating, tasting feedback, starting package price. |
| **Slide 5** | **Curated Decorator & Venue** | Ambiance rendering, stage/pelaminan dimensions, floral setup, lighting specs. |
| **Slide 6** | **Curated Photo & Video Studio** | Team size, drone/cinematic cameras, deliverables (teaser, 1-min reel, album), portfolio links. |
| **Slide 7** | **Entertainment, Audio & MC** | Sound system capacity (wattage), acoustic band/MC profile, playlist direction. |
| **Slide 8** | **Preparation Milestone Roadmap** | Visual H-90 to H-1 timeline showing vendor lock-in dates and payment schedules. |
| **Slide 9** | **Hari-H Highlight Schedule** | Snapshot of the ceremony and reception hours for family and VIP attendees. |
| **Slide 10** | **Financial Security & Escrow Guarantee** | How funds are safeguarded via Vendorama Escrow (DP 30%, Mid-Term 40%, Final 30%). |
| **Slide 11** | **Next Steps & Contact Sheet** | List of locked vendor PIC numbers, platform concierge support, and booking call-to-action. |

---

## 4. How Vendorama Paid Planner Should Translate This Research

To deliver massive value for the **Paid Planner (Rp 150.000)** upgrade:

1. **Excel Deliverable (`.xlsx`) - "The Master Operational Workbook":**
   - **Sheet 1: `Anggaran & Alokasi`** — Auto-populates from the user's wizard input (`budget_min`, `budget_max`, `estimated_pax`), automatically calculates 4-category allocation percentages with live Excel formulas (`SUM`, `VARIANCE`).
   - **Sheet 2: `Direktori Vendor & Kontak PIC`** — Full unmasked vendor roster matching the event's city and categories, with official WhatsApp links, verified ratings, package specs, and starting prices.
   - **Sheet 3: `Rundown & Timeline Persiapan`** — Ready-to-use checklist from H-90 down to Hari-H rundown table with PIC & audio/technical columns.
   - **Sheet 4: `Kalkulator Porsi & Tamu`** — Automatic catering porsi calculator based on the plan's `estimated_pax`.

2. **PDF Presentation Deck (`.pdf` Landscape 16:9) - "The Executive Pitch Deck":**
   - Generates a beautifully styled multi-slide landscape presentation.
   - Includes Event Cover, Executive Budget Allocation, Curated Vendor Cards (with verified badges, package items, and direct contacts), Preparation Roadmap, and Vendorama Financial Guarantee.
   - Ideal for the couple to show their parents, family elders, or corporate committee.

3. **Web Slide Deck Preview (`/planner/<id>/deck/`):**
   - Allows users to present or browse the deck directly in any browser without requiring Microsoft Office or Adobe Acrobat.
   - Features a 1-click browser "Cetak / Simpan PDF" button with `@page { size: landscape; }` CSS.

---

## 5. Primary References & High-Trust Sources

- [Vertex42 Wedding Planner & Budget Spreadsheets](https://www.vertex42.com) — Standard formulas for estimated vs actual budget variance and checklist hierarchy.
- [The Knot & WeddingWire Event Budget Ecosystem](https://www.theknot.com) — Category breakdown percentages and vendor payment schedules.
- [Smartsheet Event Budget and Timeline Templates](https://www.smartsheet.com) — Milestone tracking and run sheet column standards.
- [Indonesian Wedding Organizer Operational Standards (BAB / Lovary / Weddingku)](https://www.weddingku.com) — Hari-H rundown format, catering buffet-to-stall porsi ratios (60:40), and PIC coordination protocols.
