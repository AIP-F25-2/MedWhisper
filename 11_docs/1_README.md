# 🩺 MedWhisper – Week-4 (Dataset Setup & Schema Design)

### 📅 Week-4 Objective
Set up the foundational data layer for **MedWhisper**, including:
- Secure organization of the **MIMIC-IV v2.1** dataset  
- Schema design and initialization in **DuckDB**
- Creation of **staging views** for all raw hospital & ICU CSVs  
- Applying security configuration for DuckDB  
- Validation and documentation of the dataset

---

## 🧭 Folder Overview

```
MedWhisper-Data Engineer/
│
├── 1_data/
│   └── 1_raw/1_mimic-iv-2.1/
│       ├── 1_hosp/       ← 21 hospital CSVs (admissions, labs, meds…)
│       ├── 2_icu/        ← 8 ICU CSVs (chartevents, inputevents…)
│       └── preview_data.py  ← Script to explore CSV structure
│
├── 2_database/
│   ├── 1_medwhisper.duckdb        ← Main DuckDB database file
│   ├── 2_schema.sql               ← Defines base schema (PK/FK relations)
│   ├── 3_create_duckdb.py         ← Initializes DB using schema.sql
│   ├── 4_make_staging_views.py    ← Auto-generates 29 staging views
│   ├── 4_staging_views.sql        ← Generated SQL for all views
│   ├── 4_secure_duckdb.sql        ← Adds user access, encryption, and config settings
│   ├── 5_apply_staging_views.py   ← Applies all staging views to DuckDB
│   ├── check_tables.py            ← Verifies schema tables & columns
│   └── check_staging.py           ← Confirms view creation and metadata
│
└── 11_docs/
    ├── 1_README.md                ← This document
    └── dataset_summary.csv        ← Summary of all raw CSVs (rows, columns)
```

---

## 🧱 Step-by-Step Implementation

### 1️⃣ Data Organization
- Downloaded **MIMIC-IV v2.1** dataset from Kaggle (7 GB).  
- Placed files under:
  ```
  1_data/1_raw/1_mimic-iv-2.1/
  ├── 1_hosp/
  └── 2_icu/
  ```
- Each sub-folder contains multiple `.csv` files (29 total).  

### 2️⃣ Data Profiling
Executed:
```bash
python 1_data/1_raw/1_mimic-iv-2.1/preview_data.py
```
Result:
- Displayed number of rows & columns for each CSV  
- Extracted all column names  
- Saved a clean report → `11_docs/dataset_summary.csv`

### 3️⃣ Schema Design
Defined **core EHR tables** in `2_schema.sql`:
- `patients`, `admissions`, `diagnoses_icd`, `procedures_icd`,  
  `prescriptions`, `labevents`, `services`, `transfers`, `icustays`, etc.
- Included primary keys, datatypes, and logical relationships.

Initialized DB:
```bash
python 2_database/3_create_duckdb.py
```
✅ Output: `1_medwhisper.duckdb` created.

Validated schema:
```bash
python 2_database/check_tables.py
```
✅ Verified all tables and columns.

---

### 4️⃣ Staging Layer (Full Dataset Coverage)
Generated staging views for **all 29 CSV files**:
```bash
python 2_database/4_make_staging_views.py
```
✅ Output: `4_staging_views.sql` (29 views auto-generated)

Applied them:
```bash
python 2_database/5_apply_staging_views.py
```
✅ Output:
```
Applied staging views.
     n
0  161
```

Verified:
```bash
python 2_database/check_staging.py
```
✅ Output: Sample staging views listed —  
`stg_1_hosp_admissions`, `stg_1_hosp_patients`, `stg_2_icu_icustays`, etc.

---

### 5️⃣ Security Configuration for DuckDB
Configured **4_secure_duckdb.sql** to ensure secure data access:
- Restricted file imports and external write permissions.  
- Enabled encryption and safety settings.  
- Implemented read-only permissions for raw data directories.

Executed manually after DB initialization:
```bash
duckdb 2_database/1_medwhisper.duckdb < 2_database/4_secure_duckdb.sql
```
✅ Output: Database hardened for controlled team access.

---

## 🧪 Validation Summary

| Check | Result |
|-------|---------|
| Core tables created | ✅ 13 base tables |
| Total staging views | ✅ 29 (21 hosp + 8 ICU) |
| DuckDB internal views | 161 including system schemas |
| Schema verified with `check_tables.py` | ✅ |
| View metadata verified with `check_staging.py` | ✅ |
| Dataset summary saved | ✅ (`dataset_summary.csv`) |
| Database secured with `4_secure_duckdb.sql` | ✅ |

---

## 📊 Deliverables for Week-4

| File / Folder | Description |
|----------------|-------------|
| `2_schema.sql` | Database schema definition |
| `1_medwhisper.duckdb` | Created DuckDB database |
| `4_staging_views.sql` | SQL for 29 staging views |
| `4_secure_duckdb.sql` | Security configuration for DuckDB |
| `dataset_summary.csv` | CSV profile summary |
| `check_tables.py`, `check_staging.py` | Verification scripts |
| `1_README.md` | Week-4 documentation |

---


## 🏁 Week-4 Status
✅ **Completed successfully**  
All raw data registered, schema validated, staging layer and security configurations applied successfully.

---

