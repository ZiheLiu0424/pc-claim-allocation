"""Integer-only settlement arithmetic, separate from the Decimal verifier."""

import re
from pathlib import Path

from contract import AllocationInput, AllocationOutput, Category, ClaimAllocationOutput


def _money(value):
    if type(value) is not int or not 0 <= value <= 10**12:
        raise ValueError("money must be nonnegative integer cents no greater than 10^12")


def _id(value):
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", value) is None:
        raise ValueError("IDs must have 1..64 ASCII identifier characters")


def _validate(value):
    if len(value.claims) > 1000:
        raise ValueError("at most 1000 claims")
    ids = set()
    for claim in value.claims:
        _id(claim.claim_id)
        if claim.claim_id in ids:
            raise ValueError("duplicate claim ID")
        ids.add(claim.claim_id)
        if not isinstance(claim.category, Category):
            raise TypeError("unrecognized claim category")
        for amount in [claim.deductible_cents, claim.deductible_used_cents, claim.limit_cents]:
            _money(amount)
        if type(claim.coinsurance_bps) is not int or not 0 <= claim.coinsurance_bps <= 10000:
            raise ValueError("coinsurance must be integer basis points from 0 through 10000")
        if claim.category == Category.AUTO and (claim.deductible_used_cents != 0 or claim.coinsurance_bps != 0):
            raise ValueError("auto uses a per-event deductible, no annual usage or coinsurance")
        if len(claim.line_items) > 200:
            raise ValueError("at most 200 line items per claim")
        line_ids = set()
        for line in claim.line_items:
            _id(line.line_id)
            if line.line_id in line_ids:
                raise ValueError("duplicate line ID within claim")
            line_ids.add(line.line_id)
            _money(line.billed_cents)
            _money(line.allowed_cents)
            if line.allowed_cents > line.billed_cents:
                raise ValueError("allowed amount exceeds billed amount")
        _money(sum(line.billed_cents for line in claim.line_items))
        _money(sum(line.allowed_cents for line in claim.line_items))


def allocate_claims(value: AllocationInput, workspace: Path) -> AllocationOutput:
    _validate(value)
    rows = []
    for claim in value.claims:
        billed = sum(line.billed_cents for line in claim.line_items)
        allowed = sum(line.allowed_cents for line in claim.line_items)
        remaining = max(claim.deductible_cents - claim.deductible_used_cents, 0)
        deductible = min(allowed, remaining)
        after_deductible = allowed - deductible
        coinsurance = (after_deductible * claim.coinsurance_bps + 5000) // 10000
        before_limit = after_deductible - coinsurance
        insurer = min(before_limit, claim.limit_cents)
        rows.append(ClaimAllocationOutput(
            claim.claim_id, billed, allowed, remaining, deductible, coinsurance,
            before_limit, before_limit - insurer, insurer, allowed - insurer,
        ))
    return AllocationOutput(rows)
