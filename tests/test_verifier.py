from copy import deepcopy

import pytest
from slimconfig import build_output

import verifier
from contract import AllocationInput, AllocationOutput
from tests.cases import BASE, CASES, EXPECTED


def verdict(arguments, output):
    return verifier.verify_task("allocate-claims", build_output(arguments, AllocationInput),
                                build_output(output, AllocationOutput), None, ".")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["label"])
def test_hand_calculated_results(case):
    assert verdict(case["arguments"], case["expected"])["valid"]


@pytest.mark.parametrize("field", [
    "billed_cents", "allowed_cents", "remaining_deductible_cents", "deductible_share_cents",
    "coinsurance_cents", "insurer_before_limit_cents", "limit_reduction_cents", "insurer_cents", "patient_cents",
])
def test_each_monetary_component_is_checked(field):
    output = deepcopy(EXPECTED)
    output["allocations"][0][field] += 1
    assert not verdict(BASE, output)["valid"]


def test_conserved_total_does_not_hide_wrong_allocation():
    output = deepcopy(EXPECTED)
    output["allocations"][0]["insurer_cents"] -= 1
    output["allocations"][0]["patient_cents"] += 1
    assert not verdict(BASE, output)["valid"]


def test_output_order_is_irrelevant():
    output = deepcopy(EXPECTED)
    output["allocations"].reverse()
    assert verdict(BASE, output)["valid"]


@pytest.mark.parametrize("change", ["empty", "missing", "duplicate", "invented"])
def test_missing_duplicate_and_extra_claims_fail(change):
    output = deepcopy(EXPECTED)
    if change == "empty":
        output["allocations"] = []
    elif change == "missing":
        output["allocations"].pop()
    elif change == "duplicate":
        output["allocations"][1] = deepcopy(output["allocations"][0])
    else:
        output["allocations"][0]["claim_id"] = "invented"
    assert not verdict(BASE, output)["valid"]


@pytest.mark.parametrize("output", [None, {}, [], {"allocations": "wrong"}, {"allocations": [{}]}])
def test_missing_and_malformed_output_shapes_fail(output):
    with pytest.raises((TypeError, ValueError)):
        build_output(output, AllocationOutput)


@pytest.mark.parametrize("wrong", [True, 1.5, "100", None])
def test_noninteger_money_fails_contract(wrong):
    output = deepcopy(EXPECTED)
    output["allocations"][0]["insurer_cents"] = wrong
    with pytest.raises((TypeError, ValueError)):
        build_output(output, AllocationOutput)


@pytest.mark.parametrize("field,value", [
    ("deductible_cents", -1), ("deductible_cents", 10**12 + 1),
    ("deductible_used_cents", -1), ("limit_cents", -1),
    ("coinsurance_bps", -1), ("coinsurance_bps", 10001),
])
def test_invalid_source_terms_fail(field, value):
    given = deepcopy(BASE)
    given["claims"][0][field] = value
    assert not verifier.verify_input("allocate_claims", build_output(given, AllocationInput))["valid"]


@pytest.mark.parametrize("field", ["deductible_used_cents", "coinsurance_bps"])
def test_auto_rejects_health_specific_terms(field):
    given = deepcopy(BASE)
    given["claims"][1][field] = 1
    assert not verifier.verify_input("allocate_claims", build_output(given, AllocationInput))["valid"]


def test_duplicate_source_claim_and_line_ids_fail():
    given = deepcopy(BASE)
    given["claims"].append(deepcopy(given["claims"][0]))
    assert not verifier.verify_input("allocate_claims", build_output(given, AllocationInput))["valid"]
    given = deepcopy(BASE)
    given["claims"][0]["line_items"].append(deepcopy(given["claims"][0]["line_items"][0]))
    assert not verifier.verify_input("allocate_claims", build_output(given, AllocationInput))["valid"]


def test_allowed_over_billed_fails():
    given = deepcopy(BASE)
    given["claims"][0]["line_items"][0]["allowed_cents"] = 20001
    assert not verifier.verify_input("allocate_claims", build_output(given, AllocationInput))["valid"]


def test_none_submission_fails_cleanly():
    assert not verifier.verify_task("allocate-claims", build_output(BASE, AllocationInput), None, None, ".")["valid"]


def test_unknown_tool_and_task_fail_cleanly():
    given = build_output(BASE, AllocationInput)
    made = build_output(EXPECTED, AllocationOutput)
    assert not verifier.verify_input("invented", given)["valid"]
    assert not verifier.verify_task("invented", given, made, None, ".")["valid"]
