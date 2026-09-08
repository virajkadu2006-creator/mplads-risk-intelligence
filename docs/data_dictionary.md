# MPLADS Risk Intelligence System - Data Dictionary

**Status:** Confirmed (Phase 0 Complete)

## Overview
The `data/raw/` directory contains three synthetic demo CSV files (`recommended_works.csv`, `sanctioned_works.csv`, `payments.csv`), generated to match the exact canonical requirements in Part 7.1 of the Master Specification. These files contain simulated anomalous patterns (Cost Overruns, Delays, Under Utilization, Duplicates, and Trust cap violations).

Below is the mapping of the dataset columns to the canonical fields from Part 7.1.

---

## 1. File: `recommended_works.csv`
**Row Count:** 1001 rows

| Real Column Name | Canonical Field (Part 7.1) | Dtype | Notes |
| :--- | :--- | :--- | :--- |
| `unique_work_number` | `unique_work_number` | `str` | Primary key |
| `mp_name` | `mp_name` | `str` | |
| `state` | `state` | `str` | |
| `constituency` | `constituency` | `str` | |
| `work_name` | `work_name` | `str` | |
| `work_category` | `work_category` | `str` | |
| `recommended_amount` | `recommended_amount` | `float64` | |
| `date_recommended` | `date_recommended` | `str` | YYYY-MM-DD |
| `implementing_agency`| `implementing_agency`| `str` | |

---

## 2. File: `sanctioned_works.csv`
**Row Count:** 904 rows

| Real Column Name | Canonical Field (Part 7.1) | Dtype | Notes |
| :--- | :--- | :--- | :--- |
| `unique_work_number` | `unique_work_number` | `str` | Primary key |
| `sanction_amount` | `sanction_amount` | `float64` | |
| `sanction_date` | `sanction_date` | `str` | YYYY-MM-DD (Contains nulls for simulating data quality issues/under utilization) |
| `work_status` | `work_status` | `str` | |
| `implementing_agency`| `implementing_agency`| `str` | |
| `district` | `district` | `str` | |

---

## 3. File: `payments.csv`
**Row Count:** 509 rows

| Real Column Name | Canonical Field (Part 7.1) | Dtype | Notes |
| :--- | :--- | :--- | :--- |
| `unique_work_number` | `unique_work_number` | `str` | Primary key |
| `amount_spent` | `amount_spent` | `float64` | Represents per-payment or aggregated spend. |
| `vendor_name` | `vendor_name` | `str` | Optional field for vendor concentration feature. |
| `payment_date` | `payment_date` | `str` | |
| `payment_status` | `payment_status` | `str` | |

---

## Deviations from Part 7.1 Assumed Schema
- **No Structural Deviations:** The generated sample dataset was explicitly tailored to map 1:1 against the canonical column names expected by Part 7.1 to guarantee smooth pipeline execution.
- **Amounts:** Amounts are formatted as pure numerical floats. Currency conversion logic (e.g., parsing "Lakh" or "Crore" text) is safely mocked, but the robust parsing code defined in Part 7.5 will still be implemented.

The dataset is ready, and we are clear to proceed to Phase 1.
