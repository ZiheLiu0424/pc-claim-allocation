from copy import deepcopy
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import AllocationInput
from plugin.allocation import allocate_claims
from tests.cases import BASE, CASES


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["label"])
def test_tool_matches_hand_calculated_results(case):
    assert plain_output(allocate_claims(build_output(case["arguments"], AllocationInput), Path("."))) == case["expected"]


def test_no_claims_has_empty_complete_result():
    given = build_output({"claims": []}, AllocationInput)
    made = allocate_claims(given, Path("."))
    assert plain_output(made) == {"allocations": []}
    assert verifier.verify_output("allocate_claims", given, made, ".")["valid"]


@pytest.mark.parametrize("allowed,deductible,used,bps,cap,insurer,patient", [
    (100, 100, 0, 2000, 1000, 0, 100),
    (101, 100, 100, 0, 101, 101, 0),
    (101, 0, 0, 10000, 1000, 0, 101),
    (101, 0, 0, 0, 0, 0, 101),
    (101, 0, 0, 0, 100, 100, 1),
    (9999, 0, 0, 1, 10**12, 9998, 1),
    (10**12, 0, 0, 3333, 10**12, 666700000000, 333300000000),
])
def test_exact_deductible_rates_caps_and_large_integer_boundaries(allowed, deductible, used, bps, cap, insurer, patient):
    given = {"claims": [{
        "claim_id": "C", "category": "health", "line_items": [{"line_id": "L", "billed_cents": allowed, "allowed_cents": allowed}],
        "deductible_cents": deductible, "deductible_used_cents": used, "coinsurance_bps": bps, "limit_cents": cap,
    }]}
    typed = build_output(given, AllocationInput)
    made = allocate_claims(typed, Path("."))
    assert made.allocations[0].insurer_cents == insurer
    assert made.allocations[0].patient_cents == patient
    assert verifier.verify_output("allocate_claims", typed, made, ".")["valid"]


@pytest.mark.parametrize("kind", ["negative", "duplicate", "bad_line", "too_many_lines", "total_overflow", "auto_usage"])
def test_tool_rejects_invalid_sources(kind):
    given = deepcopy(BASE)
    if kind == "negative":
        given["claims"][0]["deductible_cents"] = -1
    elif kind == "duplicate":
        given["claims"].append(deepcopy(given["claims"][0]))
    elif kind == "bad_line":
        given["claims"][0]["line_items"][0]["allowed_cents"] = 20001
    elif kind == "too_many_lines":
        given["claims"][0]["line_items"] *= 101
    elif kind == "total_overflow":
        given["claims"][0]["line_items"][0]["billed_cents"] = 10**12
    else:
        given["claims"][1]["deductible_used_cents"] = 1
    with pytest.raises(ValueError):
        allocate_claims(build_output(given, AllocationInput), Path("."))
