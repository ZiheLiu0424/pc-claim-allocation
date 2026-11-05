"""Independent Decimal rederivation checks every component, including conservation."""

import re
from decimal import ROUND_HALF_UP, Decimal

from contract import Category

from .checks import result


def money(value):
    return type(value) is int and 0 <= value <= 10**12


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", value) is not None


def verify_input(value):
    claims = value.claims
    if len(claims) > 1000 or len({row.claim_id for row in claims}) != len(claims):
        return result(False, "too many claims or duplicate claim identifiers")
    for claim in claims:
        if not identifier(claim.claim_id) or claim.category not in list(Category):
            return result(False, "invalid claim identifier or category")
        if not all(money(amount) for amount in [claim.deductible_cents, claim.deductible_used_cents, claim.limit_cents]):
            return result(False, "invalid deductible, prior usage, or cap")
        if type(claim.coinsurance_bps) is not int or not 0 <= claim.coinsurance_bps <= 10000:
            return result(False, "invalid coinsurance basis points")
        if claim.category == Category.AUTO and (claim.coinsurance_bps or claim.deductible_used_cents):
            return result(False, "auto does not have annual deductible usage or coinsurance in this simulation")
        lines = claim.line_items
        if len(lines) > 200 or len({line.line_id for line in lines}) != len(lines):
            return result(False, "too many lines or duplicate line identifiers")
        for line in lines:
            if not identifier(line.line_id) or not money(line.billed_cents) or not money(line.allowed_cents):
                return result(False, "invalid line identifier or money")
            if line.billed_cents < line.allowed_cents:
                return result(False, "allowed amount exceeds billed amount")
        if not money(sum(line.billed_cents for line in lines)) or not money(sum(line.allowed_cents for line in lines)):
            return result(False, "summed line amounts exceed the supported range")
    return result(True, "claim source records satisfy the simulation contract")


def verify_output(given, made, workspace):
    valid = verify_input(given)
    if not valid["valid"]:
        return valid
    rows = made.allocations
    ids = {claim.claim_id for claim in given.claims}
    if len(rows) != len(ids) or {row.claim_id for row in rows} != ids:
        return result(False, "return every input claim exactly once")
    indexed = {row.claim_id: row for row in rows}
    for claim in given.claims:
        row = indexed[claim.claim_id]
        billed = sum(Decimal(line.billed_cents) for line in claim.line_items)
        allowed = sum(Decimal(line.allowed_cents) for line in claim.line_items)
        remaining = Decimal(claim.deductible_cents) - Decimal(claim.deductible_used_cents)
        if remaining < 0:
            remaining = Decimal(0)
        deductible = min(remaining, allowed)
        remainder = allowed - deductible
        coinsurance = (remainder * Decimal(claim.coinsurance_bps) / Decimal(10000)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        gross_insurer = remainder - coinsurance
        capped_insurer = min(gross_insurer, Decimal(claim.limit_cents))
        expected = [billed, allowed, remaining, deductible, coinsurance, gross_insurer,
                    gross_insurer - capped_insurer, capped_insurer, allowed - capped_insurer]
        observed = [row.billed_cents, row.allowed_cents, row.remaining_deductible_cents, row.deductible_share_cents,
                    row.coinsurance_cents, row.insurer_before_limit_cents, row.limit_reduction_cents,
                    row.insurer_cents, row.patient_cents]
        if any(type(amount) is not int for amount in observed) or observed != expected:
            return result(False, "allocation has an incorrect monetary component", claim_id=claim.claim_id)
        if row.insurer_cents + row.patient_cents != row.allowed_cents:
            return result(False, "allocation does not conserve allowed cents", claim_id=claim.claim_id)
    return result(True, "all components match independent Decimal arithmetic", claims=len(rows))


def verify_task(arguments, output, reference, workspace):
    return verify_output(arguments, output, workspace)
