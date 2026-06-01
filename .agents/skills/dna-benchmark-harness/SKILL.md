---
name: dna-benchmark-harness
description: Run and maintain the DNA reconstruction benchmark workflow for teammate algorithm submissions.
---

# DNA Benchmark Harness

Use this skill when working on the DNA reconstruction benchmark environment.

## Workflow

1. Confirm teammate algorithms live in `algorithms/` as C++ `*.cpp` files that read reference-guided stdin input and print only the estimated genome to stdout.
2. Use `docker compose run --rm benchmark python -m pytest` to validate the harness in the team environment.
3. Use `docker compose run --rm benchmark python -m benchmark.run --quick --out results/quick` before full experiments.
4. Run full experiments with `docker compose run --rm benchmark python -m benchmark.run --config configs/default.yaml --out results/latest`.
4. Inspect `results/latest/results.csv`, `results/latest/figures/`, and `results/latest/report.html`.

## Guardrails

- Do not implement teammate algorithms unless explicitly asked.
- Keep C++ algorithm logic in `algorithms/`; keep input generation, testing, metrics, and graphs in Python.
- Pass mutation-before reference slices to C++ algorithms, but keep the generated `my genome` hidden as the gold standard for Python-side evaluation.
- Keep experiment variables controlled and recorded in every result row.
- Treat crashes and timeouts as benchmark results, not as reasons to stop the whole run.
- Keep report figures readable: labeled axes, legends, high DPI, and clear titles.
