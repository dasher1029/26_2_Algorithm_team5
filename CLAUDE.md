# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See also [AGENTS.md](AGENTS.md) for cross-team behavioral guidelines and [.agents/skills/dna-benchmark-harness/SKILL.md](.agents/skills/dna-benchmark-harness/SKILL.md) for the benchmark workflow skill.

## Project context

University algorithm team project (4 members). Each member submits **one** DNA reconstruction algorithm into `algorithms/`. The shared deliverable is the benchmark environment that compares all four submissions under identical, reproducible conditions.

**Do not implement teammates' algorithms unless explicitly asked.** Adding boilerplate, helper logic, or "improvements" inside `algorithms/*.py` files that don't belong to the current request crosses ownership boundaries.

## Commands

```bash
# Quick sanity check (tiny config: ref=80, read=20, cov=3, noise=0, seed=1, timeout=5s)
python -m benchmark.run --quick --out results/quick

# Full benchmark with default config
python -m benchmark.run --config configs/default.yaml --out results/latest

# Override the algorithms directory
python -m benchmark.run --algorithms path/to/algos --out results/custom

# Regenerate report from existing CSV (no re-run)
python -m benchmark.report --results results/latest/results.csv --out results/latest

# Tests (one file per benchmark/ module + an end-to-end integration test)
python -m pytest
python -m pytest tests/test_integration.py    # E2E: quick run produces CSV + figures + HTML
```

Setup (venv + `pip install -r requirements.txt`) is documented in [README.md](README.md).

## Architecture

DNA reconstruction benchmarking harness. Generates random reference strings, simulates noisy reads, runs each submitted algorithm in isolation, and produces CSV + PNG figures + HTML report.

**Data flow:**
```
configs/default.yaml
    → benchmark/run.py          # orchestrator: iterates (ref_length × read_length × coverage × noise_rate × seed)
        → benchmark/dna.py      # generate_reference() + simulate_reads() — seeded RNG for reproducibility
        → benchmark/algorithms.py  # discover_algorithms() — loads *.py in algorithms/ except template.py and _*.py
        → benchmark/worker.py   # runs each algorithm in an isolated subprocess (timeout + tracemalloc)
        → benchmark/metrics.py  # edit_distance() + normalized_accuracy()
    → results/<run>/results.csv
    → benchmark/report.py       # figures/*.png + report.html
```

**Algorithm submission contract** (`algorithms/your_name.py`):
```python
def reconstruct(reads: list[str], reference_length: int, metadata: dict) -> str:
    ...
```
`metadata` keys: `alphabet`, `seed`, `read_length`, `read_count`, `coverage`, `noise_rate`, `reference_length`.

Files named `template.py` or starting with `_` are excluded from discovery. Shared helpers go in `_utils.py`-style `_`-prefixed files. The algorithm's parent directory is prepended to `sys.path`, so siblings like `_assembly_utils.py` are importable.

**Result CSV columns:** `algorithm`, `status` (`ok`/`crash`/`timeout`), `runtime_seconds`, `accuracy`, `edit_distance`, `reference_length`, `read_length`, `coverage`, `read_count`, `noise_rate`, `seed`, `reconstructed_length`, `length_ratio`, `peak_memory_mb`, `error`.

**Included reference implementations** (baselines, not the final answer):
- `denovo_greedy.py` — suffix-prefix overlap greedy assembly
- `bwt_overlap.py` — BWT k-mer index + greedy overlap
- `position_table_mapping.py` — pigeonhole-based position table mapping with `e` mismatches

Shared helpers for these live in `algorithms/_assembly_utils.py`.

## Key constraints and invariants

- **Process isolation:** each algorithm runs in a `multiprocessing.Process`. Crash or timeout becomes a row in the CSV — the benchmark never stops mid-run. Don't add try/except in `run.py` that would swallow this.
- **Don't modify `benchmark/` casually.** Team members only add files under `algorithms/`. Changes to the harness affect everyone's results.
- **Reproducibility:** `generate_reference` uses `random.Random(seed)`; `simulate_reads` uses `random.Random(seed + 1_000_003)`. The offset is intentional — keep reference RNG and read RNG independent so changing one doesn't shift the other.
- **`read_count` is derived, not configured:** `ceil(coverage × reference_length / read_length)`. Configs control `coverage`, not `read_count`.
- **Algorithm return type:** must be `str`. Worker raises `TypeError` otherwise, which becomes a `crash` row.
- **Reports are deterministic from the CSV:** `benchmark.report` can rebuild everything from `results.csv` alone — no need to re-run experiments to tweak figures.
