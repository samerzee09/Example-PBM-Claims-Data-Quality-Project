"""
Project: Healthcare PBM Data Validation & Analytics Project
Author: Samer Zeeshan Mohsin
Description: Generates a synthetic Pharmacy Benefit Manager (PBM) claims dataset
             (pbm_claims_data.csv) for downstream SQL data-quality validation and
             Power BI dashboard reporting. Approximately 15% of records contain
             intentionally injected data-quality errors to simulate real-world
             claims processing issues encountered in PBM operations.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Reproducibility
# ----------------------------------------------------------------------------
np.random.seed(42)

N_RECORDS = 400

# ----------------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------------
PLAN_TYPES = ["Commercial", "Medicare Part D", "Medicaid"]
PLAN_TYPE_WEIGHTS = [0.55, 0.30, 0.15]

US_STATES = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
             "AZ", "WA", "MA", "VA", "NJ", "CO", "TN", "MO", "IN", "WI"]

DRUG_TIERS = ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Specialty"]
DRUG_TIER_WEIGHTS = [0.30, 0.28, 0.20, 0.12, 0.10]

# Real generic and brand drug names paired with a plausible NDC and tier/cost profile
DRUGS = [
    # (drug_name, ndc_code, tier, low_cost, high_cost)
    ("Atorvastatin 20mg", "00071015523", "Tier 1", 8, 35),
    ("Lisinopril 10mg", "00378180101", "Tier 1", 5, 25),
    ("Metformin 500mg", "00093715801", "Tier 1", 4, 20),
    ("Levothyroxine 50mcg", "00074339113", "Tier 1", 6, 22),
    ("Amlodipine 5mg", "00591080501", "Tier 1", 5, 18),
    ("Omeprazole 20mg", "00378005501", "Tier 1", 7, 28),
    ("Sertraline 50mg", "00555090102", "Tier 2", 9, 32),
    ("Gabapentin 300mg", "00093015601", "Tier 2", 10, 40),
    ("Losartan 50mg", "00378180201", "Tier 2", 8, 30),
    ("Albuterol HFA Inhaler", "00173068220", "Tier 2", 45, 90),
    ("Crestor (rosuvastatin) 10mg", "00310075190", "Tier 3", 55, 140),
    ("Eliquis 5mg", "00003089421", "Tier 3", 380, 520),
    ("Jardiance 25mg", "00597014530", "Tier 3", 480, 600),
    ("Trulicity 1.5mg/0.5mL Pen", "00002143380", "Tier 4", 750, 920),
    ("Symbicort 160/4.5mcg", "00186035060", "Tier 3", 250, 340),
    ("Humira 40mg/0.4mL Pen", "00074433902", "Specialty", 5200, 6400),
    ("Enbrel 50mg/mL Pen", "58406044506", "Specialty", 4800, 6100),
    ("Ozempic 1mg/3mL Pen", "00169413013", "Tier 4", 850, 1050),
    ("Xarelto 20mg", "50458057930", "Tier 3", 420, 540),
    ("Stelara 90mg/mL", "57894006003", "Specialty", 11000, 13500),
    ("Januvia 100mg", "00006027731", "Tier 3", 460, 580),
    ("Synthroid 100mcg", "00074705213", "Tier 2", 15, 38),
    ("Insulin Glargine (Lantus) 100u/mL", "00088221033", "Tier 4", 280, 420),
    ("Duloxetine 30mg", "00555900502", "Tier 2", 12, 35),
    ("Apixaban (generic Eliquis) 5mg", "68382040910", "Tier 3", 320, 450),
    ("Hydrochlorothiazide 25mg", "00185015301", "Tier 1", 4, 16),
    ("Montelukast 10mg", "00006077531", "Tier 1", 9, 26),
    ("Escitalopram 10mg", "60429070110", "Tier 2", 8, 24),
    ("Tamsulosin 0.4mg", "00378180601", "Tier 2", 10, 28),
    ("Rosuvastatin 10mg", "00378600477", "Tier 1", 9, 30),
]

FORMULARY_STATUSES = ["On-Formulary", "Off-Formulary"]
CLAIM_STATUSES = ["Paid", "Rejected", "Reversed"]
CLAIM_STATUS_WEIGHTS = [0.82, 0.13, 0.05]

REJECTION_CODES = ["NDC_NOT_COVERED", "PA_REQUIRED", "REFILL_TOO_SOON",
                    "MEMBER_NOT_ELIGIBLE", "QTY_LIMIT_EXCEEDED", "DUPLICATE_CLAIM"]

ERROR_TYPES = ["INVALID_NDC", "MISSING_NPI", "DATE_MISMATCH",
               "COPAY_EXCEEDS_PAID", "FORMULARY_CONFLICT"]

# ----------------------------------------------------------------------------
# Helper generators
# ----------------------------------------------------------------------------
def random_dob():
    start = datetime(1935, 1, 1)
    end = datetime(2006, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=int(np.random.randint(0, delta_days)))

def random_dispensing_date():
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    delta_days = (end - start).days
    return start + timedelta(days=int(np.random.randint(0, delta_days)))

def random_npi():
    # 10-digit NPI
    return "".join(str(np.random.randint(0, 10)) for _ in range(10))

def random_member_id(i):
    return f"M{100000 + i}"

def random_pharmacy_id():
    return f"PH{np.random.randint(1000, 9999)}"

# ----------------------------------------------------------------------------
# Build base records
# ----------------------------------------------------------------------------
records = []

for i in range(1, N_RECORDS + 1):
    claim_id = f"CLM{10000 + i}"
    member_id = random_member_id(np.random.randint(1, 261))  # ~260 distinct members across 400 claims (repeat fills)
    member_dob = random_dob()
    member_state = np.random.choice(US_STATES)
    plan_type = np.random.choice(PLAN_TYPES, p=PLAN_TYPE_WEIGHTS)

    drug_name, ndc_code, drug_tier, low_cost, high_cost = DRUGS[np.random.randint(0, len(DRUGS))]

    days_supply = int(np.random.choice([30, 60, 90]))
    quantity_dispensed = int(days_supply * np.random.choice([1, 2, 3]) / np.random.choice([1, 1, 2]))
    quantity_dispensed = max(quantity_dispensed, days_supply)

    prescriber_npi = random_npi()
    pharmacy_id = random_pharmacy_id()

    dispensing_date = random_dispensing_date()
    claim_submission_date = dispensing_date + timedelta(days=int(np.random.randint(0, 4)))

    base_paid = round(np.random.uniform(low_cost, high_cost), 2)
    plan_paid_amount = round(base_paid * np.random.uniform(0.65, 0.92), 2)
    copay_amount = round(base_paid - plan_paid_amount, 2)
    paid_amount = round(plan_paid_amount + copay_amount, 2)

    formulary_status = np.random.choice(FORMULARY_STATUSES, p=[0.82, 0.18])
    prior_auth_flag = "Y" if (drug_tier in ("Tier 4", "Specialty") and np.random.rand() < 0.7) else \
                       ("Y" if np.random.rand() < 0.1 else "N")

    claim_status = np.random.choice(CLAIM_STATUSES, p=CLAIM_STATUS_WEIGHTS)
    rejection_code = np.random.choice(REJECTION_CODES) if claim_status == "Rejected" else ""

    records.append({
        "claim_id": claim_id,
        "member_id": member_id,
        "member_dob": member_dob.strftime("%Y-%m-%d"),
        "member_state": member_state,
        "plan_type": plan_type,
        "drug_name": drug_name,
        "ndc_code": ndc_code,
        "drug_tier": drug_tier,
        "days_supply": days_supply,
        "quantity_dispensed": quantity_dispensed,
        "prescriber_npi": prescriber_npi,
        "pharmacy_id": pharmacy_id,
        "dispensing_date": dispensing_date.strftime("%Y-%m-%d"),
        "claim_submission_date": claim_submission_date.strftime("%Y-%m-%d"),
        "paid_amount": paid_amount,
        "copay_amount": copay_amount,
        "plan_paid_amount": plan_paid_amount,
        "formulary_status": formulary_status,
        "prior_auth_flag": prior_auth_flag,
        "claim_status": claim_status,
        "rejection_code": rejection_code,
        "data_quality_flag": "CLEAN",
    })

df = pd.DataFrame(records)

# ----------------------------------------------------------------------------
# Inject ~15% data-quality errors across 5 error types
# ----------------------------------------------------------------------------
n_errors = int(round(N_RECORDS * 0.15))
error_indices = np.random.choice(df.index, size=n_errors, replace=False)
# Split the error budget roughly evenly across the 5 error types
error_assignments = np.random.choice(ERROR_TYPES, size=n_errors,
                                      p=[0.20, 0.20, 0.20, 0.20, 0.20])

for idx, err_type in zip(error_indices, error_assignments):
    if err_type == "INVALID_NDC":
        # Corrupt NDC format (wrong digit count / non-numeric)
        bad_ndc_options = ["INVALID", "00012-XYZ", "123", "ABCDE12345", "00000000000"]
        df.at[idx, "ndc_code"] = np.random.choice(bad_ndc_options)
        df.at[idx, "data_quality_flag"] = "INVALID_NDC"

    elif err_type == "MISSING_NPI":
        df.at[idx, "prescriber_npi"] = ""
        df.at[idx, "data_quality_flag"] = "MISSING_NPI"

    elif err_type == "DATE_MISMATCH":
        # Submission date before dispensing date (logically invalid)
        dispensing_dt = datetime.strptime(df.at[idx, "dispensing_date"], "%Y-%m-%d")
        bad_submission = dispensing_dt - timedelta(days=int(np.random.randint(1, 10)))
        df.at[idx, "claim_submission_date"] = bad_submission.strftime("%Y-%m-%d")
        df.at[idx, "data_quality_flag"] = "DATE_MISMATCH"

    elif err_type == "COPAY_EXCEEDS_PAID":
        paid = df.at[idx, "paid_amount"]
        inflated_copay = round(paid + np.random.uniform(5, 50), 2)
        df.at[idx, "copay_amount"] = inflated_copay
        df.at[idx, "data_quality_flag"] = "COPAY_EXCEEDS_PAID"

    elif err_type == "FORMULARY_CONFLICT":
        # Off-formulary drug paid without prior authorization
        df.at[idx, "formulary_status"] = "Off-Formulary"
        df.at[idx, "prior_auth_flag"] = "N"
        df.at[idx, "claim_status"] = "Paid"
        df.at[idx, "rejection_code"] = ""
        df.at[idx, "data_quality_flag"] = "FORMULARY_CONFLICT"

# ----------------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------------
output_path = "pbm_claims_data.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} records -> {output_path}")
print(f"Records with data quality issues: {(df['data_quality_flag'] != 'CLEAN').sum()} "
      f"({(df['data_quality_flag'] != 'CLEAN').mean() * 100:.1f}%)")
print(df["data_quality_flag"].value_counts())
