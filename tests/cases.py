"""Synthetic examples with explicit hand-calculated expected components."""


BASE = {"claims": [
    {"claim_id": "health", "category": "health", "line_items": [
        {"line_id": "visit", "billed_cents": 20000, "allowed_cents": 18000},
        {"line_id": "lab", "billed_cents": 5000, "allowed_cents": 2000},
    ], "deductible_cents": 10000, "deductible_used_cents": 6000, "coinsurance_bps": 2000, "limit_cents": 10000},
    {"claim_id": "auto", "category": "auto", "line_items": [
        {"line_id": "repair", "billed_cents": 25000, "allowed_cents": 20000},
    ], "deductible_cents": 5000, "deductible_used_cents": 0, "coinsurance_bps": 0, "limit_cents": 50000},
]}
EXPECTED = {"allocations": [
    {"claim_id": "health", "billed_cents": 25000, "allowed_cents": 20000,
     "remaining_deductible_cents": 4000, "deductible_share_cents": 4000, "coinsurance_cents": 3200,
     "insurer_before_limit_cents": 12800, "limit_reduction_cents": 2800, "insurer_cents": 10000, "patient_cents": 10000},
    {"claim_id": "auto", "billed_cents": 25000, "allowed_cents": 20000,
     "remaining_deductible_cents": 5000, "deductible_share_cents": 5000, "coinsurance_cents": 0,
     "insurer_before_limit_cents": 15000, "limit_reduction_cents": 0, "insurer_cents": 15000, "patient_cents": 5000},
]}

HALF_UP = {"claims": [
    {"claim_id": "half-cent", "category": "health", "line_items": [
        {"line_id": "l1", "billed_cents": 1, "allowed_cents": 1},
    ], "deductible_cents": 0, "deductible_used_cents": 0, "coinsurance_bps": 5000, "limit_cents": 100},
    {"claim_id": "overused", "category": "health", "line_items": [
        {"line_id": "l1", "billed_cents": 101, "allowed_cents": 101},
    ], "deductible_cents": 100, "deductible_used_cents": 200, "coinsurance_bps": 5000, "limit_cents": 50},
]}
HALF_UP_EXPECTED = {"allocations": [
    {"claim_id": "half-cent", "billed_cents": 1, "allowed_cents": 1,
     "remaining_deductible_cents": 0, "deductible_share_cents": 0, "coinsurance_cents": 1,
     "insurer_before_limit_cents": 0, "limit_reduction_cents": 0, "insurer_cents": 0, "patient_cents": 1},
    {"claim_id": "overused", "billed_cents": 101, "allowed_cents": 101,
     "remaining_deductible_cents": 0, "deductible_share_cents": 0, "coinsurance_cents": 51,
     "insurer_before_limit_cents": 50, "limit_reduction_cents": 0, "insurer_cents": 50, "patient_cents": 51},
]}
ZERO = {"claims": [
    {"claim_id": "empty-lines", "category": "health", "line_items": [],
     "deductible_cents": 100, "deductible_used_cents": 25, "coinsurance_bps": 10000, "limit_cents": 0},
]}
ZERO_EXPECTED = {"allocations": [
    {"claim_id": "empty-lines", "billed_cents": 0, "allowed_cents": 0,
     "remaining_deductible_cents": 75, "deductible_share_cents": 0, "coinsurance_cents": 0,
     "insurer_before_limit_cents": 0, "limit_reduction_cents": 0, "insurer_cents": 0, "patient_cents": 0},
]}
CASES = [
    {"label": "health-cap-and-auto-deductible", "arguments": BASE, "expected": EXPECTED},
    {"label": "half-up-and-exhausted-deductible", "arguments": HALF_UP, "expected": HALF_UP_EXPECTED},
    {"label": "zero-allowed-and-zero-cap", "arguments": ZERO, "expected": ZERO_EXPECTED},
]
