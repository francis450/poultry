# 01_ARCHITECTURE.md — System Design & Data Flow

## Module Map

```
┌─────────────────────────────────────────────────────────────────┐
│                      POULTRY MODULE                             │
│                                                                 │
│  ┌──────────────────┐     ┌───────────────────────────────┐    │
│  │  Poultry Crop    │────▶│  Flock Daily Record           │    │
│  │  (Master Batch)  │  1:N│  (One row per day per crop)   │    │
│  └──────────────────┘     └───────────────────────────────┘    │
│           │                                                     │
│           │ 1:N           ┌───────────────────────────────┐    │
│           ├──────────────▶│  Feed Purchase Entry          │    │
│           │               │  └─ Feed Purchase Item (child)│    │
│           │               └───────────────────────────────┘    │
│           │                        │                           │
│           │                        ▼ creates                   │
│           │               ┌───────────────────────────────┐    │
│           │               │  ERPNext Stock Entry          │    │
│           │               │  (Material Receipt)           │    │
│           │               └───────────────────────────────┘    │
│           │                                                     │
│           │ 1:N           ┌───────────────────────────────┐    │
│           ├──────────────▶│  Bird Collection Entry        │    │
│           │               │  └─ Bird Collection Detail    │    │
│           │               │     (by weight band)          │    │
│           │               └───────────────────────────────┘    │
│           │                        │                           │
│           │                        ▼ creates                   │
│           │               ┌───────────────────────────────┐    │
│           │               │  ERPNext Delivery Note        │    │
│           │               └───────────────────────────────┘    │
│           │                                                     │
│           │ 1:1           ┌───────────────────────────────┐    │
│           └──────────────▶│  Crop Financial Summary       │    │
│                           │  (auto-generated on Close)    │    │
│                           └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ERPNext Modules Leveraged

| ERPNext Module | How Used |
|---------------|----------|
| **Stock** | Feed items as stock items; warehouse per farm; Stock Entries for receipt and issue |
| **Buying** | Supplier master for feed suppliers; Purchase Orders optional |
| **Item** | Feed types (Pre-Starter, C1, C2, C3, Finisher) as stock items |
| **Warehouse** | One warehouse per farm location |
| **Project** | Optional: one Project per crop for cost centre tagging |
| **Customer** | Anirita Poultry Farm Ltd as the integrator/buyer of birds |

---

## Doctype Dependency Graph

```
Farm (Branch/Warehouse group)
    └── Poultry Crop
            ├── Flock Daily Record (N)
            ├── Feed Purchase Entry (N)
            │       └── Feed Purchase Item (child, N rows)
            ├── Bird Collection Entry (N)
            │       └── Bird Collection Detail (child, N rows)
            └── Crop Financial Summary (1)
```

Create doctypes in this exact order to avoid LinkValidation errors:
1. Feed Purchase Item *(child table — no dependencies)*
2. Bird Collection Detail *(child table — no dependencies)*
3. Poultry Crop *(master — no custom dependencies)*
4. Flock Daily Record *(depends on Poultry Crop)*
5. Feed Purchase Entry *(depends on Poultry Crop + Feed Purchase Item)*
6. Bird Collection Entry *(depends on Poultry Crop + Bird Collection Detail)*
7. Crop Financial Summary *(depends on Poultry Crop)*

---

## Data Flow: Day-to-Day Operations

### Morning — Farm Manager opens the app

```
1. Open today's Flock Daily Record (auto-created by scheduled job at midnight)
2. Enter mortality count
3. System auto-calculates:
   - Closing Stock = Previous Closing Stock − Mortality
   - Mortality % = Mortality / Opening Stock × 100
4. Enter actual feed consumed (KGs)
5. System shows variance vs. Feed Std GMS for that age
6. Enter body weight (if weigh day)
7. Save → alert triggered if mortality % > threshold
```

### Feed Purchase — Store Manager

```
1. Create Feed Purchase Entry
2. Add rows: Feed Type, No. of Bags, Pack Weight (KG), Total KGs
3. On Submit:
   - System creates Stock Entry (Material Receipt) for each feed type
   - Stock updates in Farm Warehouse automatically
4. Feed cost auto-posted to crop's running cost
```

### Slaughter / Collection Day

```
1. Create Bird Collection Entry
2. Add rows per weight band: Below 1.6kg / 1.6–1.8kg / Above 1.8kg
3. Enter price per KG per band
4. System calculates:
   - Total birds collected
   - Average weight
   - Revenue per band and total
5. On Submit → creates Delivery Note in ERPNext
6. Closing Stock updated on linked Flock Daily Record
```

### Crop Closure

```
1. Manager clicks "Close Crop" button on Poultry Crop
2. System validates: all birds collected (Closing Stock = 0 or negligible)
3. Crop Financial Summary auto-generated:
   - Chick Cost
   - Total Feed Cost (sum of all Feed Purchase Entries)
   - Total Revenue (sum of all Bird Collection Entries)
   - Mortality Loss (dead birds × average chick cost)
   - Net P&L
   - Revenue per Bird, Cost per Bird
4. Crop status → Closed (read-only)
```

---

## Standard Feed Schedule (Reference from Paper Forms)

| Age (Days) | Feed Type | Daily Std (GMS/bird) | Weekly Feed Std (KGs) |
|------------|-----------|---------------------|-----------------------|
| 1–7        | Pre-Starter | 5–35 rising       | 140 GM std            |
| 8–14       | C1 Grower  | 40–55 rising       | 340 GM std            |
| 15–21      | C2 Grower  | 60–80 rising       | 500 GM std            |
| 22–28      | C3 Grower  | 90–135 rising      | 805 GM std            |
| 29–35      | C3/Finisher | 140–175 rising    | 1100 GM std           |
| 36+        | Finisher   | 175+               | 1850 GM std           |

Store this in a **Feed Standard** configuration doctype or as a JSON fixture so it
can be used by client scripts to auto-populate `Feed Std GMS` on Flock Daily Records.

---

## Body Weight Standards (Reference)

| Week | B.Wt Std (GMS) |
|------|----------------|
| 1    | 165 GM         |
| 2    | 420 GM         |
| 3    | 765 GM         |
| 4    | 1250 GM        |
| 5    | 1850 GM        |

---

## Warehouse Strategy

```
Warehouse Structure (create in ERPNext):
All Warehouses
└── Anirita Poultry Farm Ltd
    ├── Belmonte Farm - Store
    ├── Paul Farm - Store
    └── [FarmName] - Store   ← pattern for new farms
```

Each `Poultry Crop` links to one warehouse. Feed receipts and issues
transact against that warehouse only.

---

## Naming Conventions

| Doctype | Naming Rule | Example |
|---------|------------|---------|
| Poultry Crop | `CROP-{farm_code}-{YYYY}-{####}` | `CROP-PAUL-2023-0014` |
| Flock Daily Record | `FDR-{crop}-{day_age}` | `FDR-CROP-PAUL-2023-0014-001` |
| Feed Purchase Entry | `FPE-{crop}-{####}` | `FPE-CROP-PAUL-2023-0014-001` |
| Bird Collection Entry | `BCE-{crop}-{####}` | `BCE-CROP-PAUL-2023-0014-001` |
| Crop Financial Summary | `CFS-{crop}` | `CFS-CROP-PAUL-2023-0014` |

---

## Permissions Design

| Role | Poultry Crop | Flock Daily Record | Feed Purchase Entry | Bird Collection | Financial Summary |
|------|-------------|-------------------|--------------------|-----------------|--------------------|
| Farm Manager | Read, Write | Read, Write, Create | Read | Read | Read |
| Store Manager | Read | Read | Read, Write, Create, Submit | Read | Read |
| Farm Director | All | All | All | All | All |
| Accounts User | Read | — | Read | Read | Read, Write |

Create these roles in ERPNext Role master before assigning permissions.
