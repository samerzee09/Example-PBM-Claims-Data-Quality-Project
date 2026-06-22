/* =============================================================================
   Project:     Healthcare PBM Data Validation & Analytics Project
   Author:      Samer Zeeshan Mohsin
   Date:        2026-06-22
   Description: Production-style T-SQL validation suite for the synthetic PBM
                claims dataset (pbm_claims_data.csv, loaded into table
                dbo.pbm_claims_data). Performs completeness, format, logic,
                and duplication checks; summarizes rejection codes, drug-tier
                spend, and monthly claim volume; and produces an executive
                data-quality summary with an overall quality grade.
   Target table: dbo.pbm_claims_data
   ============================================================================= */

SET NOCOUNT ON;
GO

/* -----------------------------------------------------------------------------
   1. RECORD COUNT AUDIT
   Total record count, distinct member count, and claim date range.
   ----------------------------------------------------------------------------- */
SELECT
    COUNT(claim_id)                    AS total_records,
    COUNT(DISTINCT member_id)          AS distinct_members,
    MIN(dispensing_date)               AS earliest_dispensing_date,
    MAX(dispensing_date)               AS latest_dispensing_date,
    MIN(claim_submission_date)         AS earliest_submission_date,
    MAX(claim_submission_date)         AS latest_submission_date
FROM dbo.pbm_claims_data;
GO

/* -----------------------------------------------------------------------------
   2. NULL / COMPLETENESS CHECK
   Counts NULL (or blank) values in key required fields.
   ----------------------------------------------------------------------------- */
SELECT
    SUM(CASE WHEN claim_id              IS NULL THEN 1 ELSE 0 END) AS null_claim_id,
    SUM(CASE WHEN member_id             IS NULL THEN 1 ELSE 0 END) AS null_member_id,
    SUM(CASE WHEN member_dob            IS NULL THEN 1 ELSE 0 END) AS null_member_dob,
    SUM(CASE WHEN plan_type             IS NULL THEN 1 ELSE 0 END) AS null_plan_type,
    SUM(CASE WHEN ndc_code              IS NULL THEN 1 ELSE 0 END) AS null_ndc_code,
    SUM(CASE WHEN drug_tier             IS NULL THEN 1 ELSE 0 END) AS null_drug_tier,
    SUM(CASE WHEN prescriber_npi        IS NULL
              OR prescriber_npi = ''    THEN 1 ELSE 0 END)         AS missing_prescriber_npi,
    SUM(CASE WHEN dispensing_date       IS NULL THEN 1 ELSE 0 END) AS null_dispensing_date,
    SUM(CASE WHEN claim_submission_date IS NULL THEN 1 ELSE 0 END) AS null_submission_date,
    SUM(CASE WHEN paid_amount           IS NULL THEN 1 ELSE 0 END) AS null_paid_amount,
    SUM(CASE WHEN copay_amount          IS NULL THEN 1 ELSE 0 END) AS null_copay_amount,
    SUM(CASE WHEN plan_paid_amount      IS NULL THEN 1 ELSE 0 END) AS null_plan_paid_amount
FROM dbo.pbm_claims_data;
GO

/* -----------------------------------------------------------------------------
   3. NDC FORMAT VALIDATION
   Valid NDC codes are 11 numeric digits (5-4-2 format stored without dashes).
   Flags any code that is not exactly 11 digits or contains non-numeric characters.
   ----------------------------------------------------------------------------- */
WITH ndc_check AS (
    SELECT
        claim_id,
        ndc_code,
        CASE
            WHEN ndc_code IS NULL THEN 'MISSING'
            WHEN LEN(ndc_code) <> 11 THEN 'INVALID_LENGTH'
            WHEN ndc_code LIKE '%[^0-9]%' THEN 'NON_NUMERIC'
            ELSE 'VALID'
        END AS ndc_validation_status
    FROM dbo.pbm_claims_data
)
SELECT
    claim_id,
    ndc_code,
    ndc_validation_status
FROM ndc_check
WHERE ndc_validation_status <> 'VALID'
ORDER BY claim_id;
GO

/* -----------------------------------------------------------------------------
   4. DATE INTEGRITY CHECK
   Claim submission date should never be earlier than the dispensing date.
   ----------------------------------------------------------------------------- */
SELECT
    claim_id,
    member_id,
    dispensing_date,
    claim_submission_date,
    DATEDIFF(DAY, dispensing_date, claim_submission_date) AS days_between
FROM dbo.pbm_claims_data
WHERE claim_submission_date < dispensing_date
ORDER BY claim_id;
GO

/* -----------------------------------------------------------------------------
   5. COPAY LOGIC CHECK
   Flags claims where the member copay exceeds the total paid amount, which is
   not logically possible under standard adjudication rules.
   ----------------------------------------------------------------------------- */
SELECT
    claim_id,
    member_id,
    paid_amount,
    copay_amount,
    plan_paid_amount,
    (copay_amount - paid_amount) AS overage_amount
FROM dbo.pbm_claims_data
WHERE copay_amount > paid_amount
ORDER BY overage_amount DESC;
GO

/* -----------------------------------------------------------------------------
   6. FORMULARY CONFLICT CHECK
   Flags off-formulary claims that were paid without a prior authorization
   on file -- a compliance and improper-payment risk.
   ----------------------------------------------------------------------------- */
SELECT
    claim_id,
    member_id,
    drug_name,
    formulary_status,
    prior_auth_flag,
    claim_status,
    paid_amount
FROM dbo.pbm_claims_data
WHERE formulary_status = 'Off-Formulary'
  AND prior_auth_flag  = 'N'
  AND claim_status     = 'Paid'
ORDER BY paid_amount DESC;
GO

/* -----------------------------------------------------------------------------
   7. DUPLICATE CLAIM DETECTION
   Identifies potential duplicate claims: same member, drug, and dispensing
   date submitted more than once.
   ----------------------------------------------------------------------------- */
WITH duplicate_ranked AS (
    SELECT
        claim_id,
        member_id,
        ndc_code,
        dispensing_date,
        paid_amount,
        ROW_NUMBER() OVER (
            PARTITION BY member_id, ndc_code, dispensing_date
            ORDER BY claim_id
        ) AS occurrence_number
    FROM dbo.pbm_claims_data
)
SELECT
    claim_id,
    member_id,
    ndc_code,
    dispensing_date,
    paid_amount,
    occurrence_number
FROM duplicate_ranked
WHERE occurrence_number > 1
ORDER BY member_id, ndc_code, dispensing_date;
GO

/* -----------------------------------------------------------------------------
   8. REJECTION CODE DISTRIBUTION
   Count and percentage share of each rejection code among rejected claims.
   ----------------------------------------------------------------------------- */
WITH rejected_claims AS (
    SELECT
        claim_id,
        rejection_code
    FROM dbo.pbm_claims_data
    WHERE claim_status = 'Rejected'
),
rejection_totals AS (
    SELECT COUNT(claim_id) AS total_rejected
    FROM rejected_claims
)
SELECT
    rc.rejection_code,
    COUNT(rc.claim_id)                                              AS rejection_count,
    CAST(ROUND(100.0 * COUNT(rc.claim_id) / rt.total_rejected, 2) AS DECIMAL(5,2)) AS pct_of_rejections
FROM rejected_claims rc
CROSS JOIN rejection_totals rt
GROUP BY rc.rejection_code, rt.total_rejected
ORDER BY rejection_count DESC;
GO

/* -----------------------------------------------------------------------------
   9. DRUG TIER SPEND SUMMARY
   Total paid, average paid, and claim count by drug tier.
   ----------------------------------------------------------------------------- */
SELECT
    drug_tier,
    COUNT(claim_id)                          AS claim_count,
    SUM(paid_amount)                         AS total_paid,
    CAST(AVG(paid_amount) AS DECIMAL(10,2))  AS avg_paid_per_claim
FROM dbo.pbm_claims_data
GROUP BY drug_tier
ORDER BY total_paid DESC;
GO

/* -----------------------------------------------------------------------------
   10. MONTHLY VOLUME TREND
   Claim volume and total paid amount by dispensing month.
   ----------------------------------------------------------------------------- */
SELECT
    DATEPART(YEAR, dispensing_date)  AS claim_year,
    DATEPART(MONTH, dispensing_date) AS claim_month,
    COUNT(claim_id)                  AS claim_count,
    SUM(paid_amount)                 AS total_paid
FROM dbo.pbm_claims_data
GROUP BY DATEPART(YEAR, dispensing_date), DATEPART(MONTH, dispensing_date)
ORDER BY claim_year, claim_month;
GO

/* -----------------------------------------------------------------------------
   11. EXECUTIVE SUMMARY
   Rolls up overall record counts, total errors flagged, error rate, and
   assigns a letter quality grade based on the error rate threshold.
   ----------------------------------------------------------------------------- */
WITH base_counts AS (
    SELECT
        COUNT(claim_id) AS total_records,
        SUM(CASE WHEN data_quality_flag <> 'CLEAN' THEN 1 ELSE 0 END) AS total_errors
    FROM dbo.pbm_claims_data
),
error_rate_calc AS (
    SELECT
        total_records,
        total_errors,
        CAST(ROUND(100.0 * total_errors / total_records, 2) AS DECIMAL(5,2)) AS error_rate_pct
    FROM base_counts
)
SELECT
    total_records,
    total_errors,
    error_rate_pct,
    CASE
        WHEN error_rate_pct <= 5.0  THEN 'A'
        WHEN error_rate_pct <= 10.0 THEN 'B'
        WHEN error_rate_pct <= 20.0 THEN 'C'
        ELSE 'D'
    END AS data_quality_grade
FROM error_rate_calc;
GO
