# Healthcare PBM Data Validation & Analytics Project

## Project Summary

This project simulates a Pharmacy Benefit Manager (PBM) claims data quality and analytics workflow, the kind of work performed by data analysts supporting claims operations, formulary management, and compliance teams at health plans and PBMs. It combines a synthetic 400-record claims dataset, a production-style T-SQL validation suite, and a Power BI dashboard specification to demonstrate an end-to-end data quality and reporting pipeline: generate data, validate it, surface the issues, and report on them.

## Business Problem

PBM claims data quality is not just an operational nuisance — it is a compliance and financial exposure issue. Invalid NDC codes can cause claims to be misadjudicated or trigger downstream audit findings. Missing prescriber NPIs break provider attribution required for regulatory reporting. Claims paid off-formulary without prior authorization represent improper payments that plans are required to identify and recover. Copay amounts that exceed the total paid amount point to adjudication logic errors that, left unchecked, erode member trust and plan financials. Left undetected, these issues compound across millions of claims and become the subject of CMS audits, SOX-style internal control findings, and member grievances. Systematic, repeatable validation is the control that catches these issues before they reach that scale.

## Tools Used

- **Python** (pandas, numpy) — synthetic dataset generation with seeded randomness for reproducibility
- **SQL** (T-SQL) — data validation, completeness checks, and analytical summaries
- **Power BI** — dashboard design and DAX measures for executive and operational reporting
- **Excel** — ad hoc validation spot-checks and pivot summaries during development
- **DAX** — calculated measures powering the Power BI dashboard

## Methodology

1. **Data Generation** — Built a 400-record synthetic PBM claims dataset (`pbm_claims_data.csv`) using Python with a fixed random seed (42) for reproducibility. Records span Commercial, Medicare Part D, and Medicaid plan types, a 30-drug formulary mix spanning generic and brand-name medications across five drug tiers, and realistic claim economics (paid amount, copay, plan-paid split). Approximately 15% of records were seeded with one of five intentional data quality defects: `INVALID_NDC`, `MISSING_NPI`, `DATE_MISMATCH`, `COPAY_EXCEEDS_PAID`, and `FORMULARY_CONFLICT`.
2. **SQL Validation** — Wrote a T-SQL validation script (`pbm_claims_validation.sql`) covering record-count audits, completeness checks, NDC format validation, date integrity checks, copay logic checks, formulary conflict detection, duplicate claim detection, rejection code distribution, drug tier spend summaries, monthly volume trends, and an executive summary with an overall data quality grade.
3. **Dashboard Design** — Specified a 3-page Power BI dashboard (`powerbi_dashboard_spec.md`) covering an executive summary, a data quality audit view, and a spend and drug utilization view, each with supporting DAX measures.
4. **Reporting** — Synthesized findings into the key metrics below, intended to mirror the kind of summary a PBM data analyst would present to operations or compliance leadership.

## Key Findings

- **Overall data quality rate:** Of 400 claims processed, 60 records (15.0%) were flagged with at least one data quality defect, resulting in an overall quality grade of **C** under the project's A/B/C/D grading scale (A ≤5%, B ≤10%, C ≤20%, D >20%).
- **NDC formatting errors:** 15 claims (3.75% of total volume) carried an invalid or malformed NDC code, the kind of defect that can cause a claim to be misadjudicated or rejected at the point of sale.
- **Copay logic errors:** 14 claims showed a member copay amount exceeding the total paid amount, indicating an adjudication logic defect that would require a system configuration review in a production environment.
- **Provider attribution gaps:** 15 claims were missing a prescriber NPI, which would block accurate provider-level reporting required for regulatory and network performance analysis.
- **Formulary conflict exposure:** 4 claims were identified as off-formulary drugs paid without a prior authorization on file — the highest-risk category per claim from a compliance and improper-payment recovery standpoint, despite the lower count.
- **Spend concentration in Specialty and Tier 4 drugs:** Despite representing a smaller share of claim volume, Specialty and Tier 4 medications (e.g., biologics and GLP-1 therapies) accounted for a disproportionately large share of total plan-paid dollars, consistent with industry-wide trends in specialty drug spend management.

## Author

**Samer Zeeshan Mohsin**
Email: samzee06@gmail.com
LinkedIn: [linkedin.com/in/samer-zeeshan-759417212](https://linkedin.com/in/samer-zeeshan-759417212)
