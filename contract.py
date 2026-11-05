"""Structured simulated claim cost allocation; declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    ALLOCATE_CLAIMS = "allocate_claims"


class Task(Enum):
    ALLOCATE_CLAIMS = "allocate-claims"
    ALLOCATE_CLAIMS_LOCAL = "allocate-claims-local"


class Category(Enum):
    HEALTH = "health"
    AUTO = "auto"


@dataclass
class ClaimLine(Output):
    line_id: Annotated[str, "Identifier unique within its claim"]
    billed_cents: Annotated[int, "Nonnegative billed integer cents"]
    allowed_cents: Annotated[int, "Nonnegative allowed integer cents, at most billed_cents"]


@dataclass
class ClaimRecord(Output):
    claim_id: Annotated[str, "Globally unique claim identifier"]
    category: Annotated[Category, "Health annual deductible with coinsurance, or auto per-event deductible"]
    line_items: Annotated[list[ClaimLine], "At most 200 billed/allowed lines, with totals no greater than 10^12 cents"]
    deductible_cents: Annotated[int, "Nonnegative deductible, no greater than 10^12 cents"]
    deductible_used_cents: Annotated[int, "Previously used health deductible; must be zero for auto"]
    coinsurance_bps: Annotated[int, "Patient health coinsurance, 0..10000 basis points; zero for auto"]
    limit_cents: Annotated[int, "Simulated per-claim insurer cap in cents, no greater than 10^12"]


@dataclass
class AllocationInput(Output):
    claims: Annotated[list[ClaimRecord], "Up to 1000 independent simulated health/auto claim records"]


@dataclass
class ClaimAllocationOutput(Output):
    claim_id: Annotated[str, "Source claim identifier"]
    billed_cents: Annotated[int, "Sum of source billed amounts"]
    allowed_cents: Annotated[int, "Sum of source allowed amounts"]
    remaining_deductible_cents: Annotated[int, "max(deductible-used,0) for health; event deductible for auto"]
    deductible_share_cents: Annotated[int, "Allowed amount consumed by the remaining deductible"]
    coinsurance_cents: Annotated[int, "Patient coinsurance on post-deductible allowed amount, half-up to cents"]
    insurer_before_limit_cents: Annotated[int, "Post-deductible amount minus coinsurance before applying the cap"]
    limit_reduction_cents: Annotated[int, "Amount of insurer liability shifted by the simulated cap"]
    insurer_cents: Annotated[int, "Final capped insurer share"]
    patient_cents: Annotated[int, "Allowed cents minus insurer cents; excludes billed-minus-allowed"]


@dataclass
class AllocationOutput(Output):
    allocations: Annotated[list[ClaimAllocationOutput], "Exactly one full monetary decomposition per input claim; order is irrelevant"]


TOOLS = {Tool.ALLOCATE_CLAIMS: (AllocationInput, AllocationOutput)}
TASKS = {Task.ALLOCATE_CLAIMS: (AllocationInput, AllocationOutput), Task.ALLOCATE_CLAIMS_LOCAL: (AllocationInput, AllocationOutput)}
