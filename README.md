# Claim Cost Allocation

Compute complete integer-cent allocations for structured synthetic health and auto claims. This original course task combines annual deductible usage, half-up coinsurance and a simulated per-claim insurer cap. It does not adjudicate real insurance claims.

## Tools

| Tool | Input → output | Purpose |
| --- | --- | --- |
| `allocate_claims` | `AllocationInput` → `AllocationOutput` | Compute billed, allowed, deductible, coinsurance, cap and insurer/patient components |

| Task | Runner | Behavior |
| --- | --- | --- |
| `allocate-claims` | `agent` | Call `allocate_claims` and submit its complete structured output |
| `allocate-claims-local` | `tool` | Run the identical computation directly without a model |

Rules apply independently per claim:

1. Sum billed and allowed cents from all lines. Each line requires `0 <= allowed <= billed`.
2. Health remaining deductible is `max(deductible - previously_used, 0)`. Auto uses the event deductible and requires annual usage and coinsurance to be zero.
3. Deductible share is `min(total_allowed, remaining_deductible)`.
4. Patient coinsurance is `(allowed - deductible_share) * basis_points / 10000`, rounded **half-up once at the aggregate claim level** to integer cents.
5. Before-limit insurer share is `allowed - deductible_share - coinsurance`. Final insurer share is the minimum of this amount and the cap. Their difference is the cap reduction.
6. Patient share is `allowed - insurer`, including deductible, coinsurance and simulated cap effects. Billed-minus-allowed is excluded; no balance-billing rule is implied.

Money inputs and summed line amounts are nonnegative integer cents up to 10^12. Rates are integer 0..10000 basis points; booleans, floats and numeric strings are not money. At most 1000 claims and 200 lines per claim are allowed. Claim IDs are globally unique; line IDs are unique within a claim. IDs have 1..64 ASCII alphanumeric/`_.:-` characters with an alphanumeric first character. Empty claims/lines are valid. Health prior usage above the deductible is valid and produces zero remaining deductible. Missing or invalid source facts raise an error.

The tool uses integer arithmetic; the independent verifier uses `Decimal` and `ROUND_HALF_UP`. It checks **every monetary component**, complete claim coverage and conservation. A correct total cannot hide an incorrect insurer/patient split. Claim output order may vary. Verification uses no model, network, clock, environment variables or randomness.

## Layout

`contract.py` declares source and result types. `nanoagent.yaml` registers the MCP tool and both runners. `src/plugin/allocation.py` implements integer arithmetic; `verifier/allocation.py` rederives every amount independently. `src/plugin/__main__.py` serves MCP. `tests/cases.py` contains three synthetic, hand-computed examples. `tests/test_verifier.py` covers malformed, missing and one-cent-wrong results. `ui/` delegates rendering to the host; `product/` contains marketplace metadata. `pyproject.toml` and `uv.lock` define dependencies.

Actual execution evidence and the course report are maintained outside this plugin repository. Public examples are reproducibility fixtures, not a hidden oracle.

## Develop and run

Requires Git, uv and Python 3.12 or later. Install exactly the checked-in dependency revisions:

```bash
uv sync --frozen --extra dev
uv run pytest -q
uv run ruff check .
uv lock --check
```

Inspect with a separately installed NanoAgent: `nanoagent plugin inspect /path/to/pc-claim-allocation`. Runtime is `[uv, run, --frozen, python, -m, plugin]`; NanoAgent sets `NANOAGENT_WORKSPACE`. No other variables or network hosts are required. Use `allocate-claims-local` for deterministic execution and `allocate-claims` for an actual configured agent session. Offline success does not establish model execution or marketplace publication.

Limitations: claims are independent and previous health deductible usage is supplied. The plugin does not update annual state across claims, evaluate exclusions, use out-of-pocket maximums, process provider networks, prorate limits, decide medical necessity, or extract documents. The insurer cap and patient share are explicit course simulation rules and do not describe real insurance obligations. The verifier establishes arithmetic under these rules only.
