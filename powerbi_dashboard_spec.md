# PBM Claims Data Quality & Analytics Dashboard — Power BI Specification

**Project:** Healthcare PBM Data Validation & Analytics Project
**Author:** Samer Zeeshan Mohsin
**Data Source:** `pbm_claims_data.csv`

## Overview

This document specifies a 3-page Power BI dashboard built directly on top of `pbm_claims_data.csv`. The dashboard gives PBM operations and compliance stakeholders a single view into claim volume, payment accuracy, and data quality risk across the book of business. Each page below lists the visuals, the fields each visual is bound to, and the interactions/filters available to the user.

## Data Model Notes

- Single fact table: `pbm_claims_data` (one row per claim).
- Recommended calculated column `Is_Error` (1/0) based on `data_quality_flag <> "CLEAN"`, used to simplify several measures.
- Recommended date table relationship on `dispensing_date` for native time-intelligence support if extended beyond a single calendar year.
- Field formatting: `paid_amount`, `copay_amount`, `plan_paid_amount` as Currency; `member_dob`, `dispensing_date`, `claim_submission_date` as Date.

---

## Page 1 — Executive Summary

**Purpose:** A leadership-level snapshot of claim volume, spend, and overall data quality health.

**Visuals:**

1. **KPI Cards (top row, 4 cards)**
   - Total Claims — `[Total Claims]` measure
   - Total Members — distinct count of `member_id`
   - Total Paid — `[Total Plan Paid]` or sum of `paid_amount`, formatted as currency
   - Error Rate % — `[Error Rate %]` measure, conditional formatting (green ≤5%, yellow 5–10%, red >10%)

2. **Donut Chart — Claims by Status**
   - Legend: `claim_status` (Paid / Rejected / Reversed)
   - Values: Count of `claim_id`

3. **Monthly Trend Line Chart**
   - X-axis: `dispensing_date` (month granularity)
   - Y-axis: Count of `claim_id` (primary), Sum of `paid_amount` (secondary axis, line)

4. **Slicer — Plan Type**
   - Field: `plan_type` (Commercial / Medicare Part D / Medicaid)
   - Applies as a page-level filter to all visuals on Page 1

**Layout:** KPI cards span the top row; donut chart bottom-left; trend line bottom-right; plan type slicer docked top-right as a filter pane.

---

## Page 2 — Data Quality Audit

**Purpose:** Operational view for the data quality / compliance team to triage flagged claims.

**Visuals:**

1. **Flagged Records Table**
   - Columns: `claim_id`, `member_id`, `plan_type`, `drug_name`, `data_quality_flag`, `dispensing_date`, `paid_amount`, `copay_amount`
   - Filter: `data_quality_flag <> "CLEAN"`
   - Conditional formatting: background fill red on rows/cells where `data_quality_flag <> "CLEAN"` (rules-based formatting on the `data_quality_flag` column); white/default for `CLEAN` rows if included for context

2. **Bar Chart — Error Type Distribution**
   - Axis: `data_quality_flag` (excluding `CLEAN`)
   - Values: Count of `claim_id`
   - Sorted descending by count

3. **Bar Chart — Error Rate % by Plan Type**
   - Axis: `plan_type`
   - Values: `[Error Rate %]` measure (filtered to each plan type context via visual-level filter or implicit filter from axis)
   - Data labels showing percentage

**Layout:** Table occupies the full left two-thirds of the page; error type bar chart top-right; error rate by plan type bar chart bottom-right.

---

## Page 3 — Spend & Drug Analysis

**Purpose:** Drug-level and formulary-level spend analysis for pharmacy network and formulary management teams.

**Visuals:**

1. **Bar Chart — Claim Volume by Drug Tier**
   - Axis: `drug_tier` (Tier 1, Tier 2, Tier 3, Tier 4, Specialty)
   - Values: Count of `claim_id`
   - Sorted in tier order

2. **Top 10 Drugs by Paid Amount**
   - Axis: `drug_name` (Top N filter = 10, by Sum of `paid_amount`)
   - Values: Sum of `paid_amount`
   - Sorted descending

3. **Formulary Status Breakdown**
   - Donut or stacked bar: `formulary_status` (On-Formulary / Off-Formulary)
   - Values: Count of `claim_id`, with `prior_auth_flag` as a secondary breakdown (legend or stacked segment) to surface formulary conflict risk

**Layout:** Drug tier volume chart top-left; top 10 drugs chart top-right (wider, since drug names are long); formulary status breakdown bottom row, full width.

---

## DAX Measures

```dax
Total Claims =
COUNTROWS ( pbm_claims_data )
```

```dax
Flagged Claims Count =
CALCULATE (
    COUNTROWS ( pbm_claims_data ),
    pbm_claims_data[data_quality_flag] <> "CLEAN"
)
```

```dax
Error Rate % =
DIVIDE (
    [Flagged Claims Count],
    [Total Claims],
    0
)
```

```dax
Avg Paid Per Claim =
DIVIDE (
    SUM ( pbm_claims_data[paid_amount] ),
    [Total Claims],
    0
)
```

```dax
Total Plan Paid =
SUM ( pbm_claims_data[plan_paid_amount] )
```

**Formatting notes:** Format `[Error Rate %]` as a percentage with 1 decimal place. Format `[Avg Paid Per Claim]` and `[Total Plan Paid]` as Currency with 2 decimal places.

---

## Cross-Page Interactions

- A top-level **Plan Type** slicer (Page 1) is synced across all three pages via Power BI's "Sync Slicers" pane, so analysts can filter the entire book by Commercial, Medicare Part D, or Medicaid without re-selecting on each page.
- Drill-through is enabled from the Page 1 donut chart (claim status) to the Page 2 flagged records table, filtered to the selected status.
- Tooltips on all bar and line charts display the underlying claim count and paid amount on hover.
