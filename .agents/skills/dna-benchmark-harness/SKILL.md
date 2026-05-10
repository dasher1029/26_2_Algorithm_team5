---
name: dna-benchmark-harness
description: Run and maintain the DNA reconstruction benchmark workflow for teammate algorithm submissions.
---

# DNA Benchmark Harness

Use this skill when working on the DNA reconstruction benchmark environment.

## Workflow

1. Confirm teammate algorithms live in `algorithms/` and expose `reconstruct(reads, reference_length, metadata) -> str`.
2. Use `python -m benchmark.run --quick --out results/quick` before full experiments.
3. Run full experiments with `python -m benchmark.run --config configs/default.yaml --out results/latest`.
4. Inspect `results/latest/results.csv`, `results/latest/figures/`, and `results/latest/report.html`.

## Guardrails

- Do not implement teammate algorithms unless explicitly asked.
- Keep experiment variables controlled and recorded in every result row.
- Treat crashes and timeouts as benchmark results, not as reasons to stop the whole run.
- Keep report figures readable: labeled axes, legends, high DPI, and clear titles.
