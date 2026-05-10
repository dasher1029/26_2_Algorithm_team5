# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Repository Project Notes

Keep this section short and repo-wide. Put detailed workflow design in repo-local skills or docs.

## What
- This repository supports a university algorithm team project for DNA string reconstruction benchmarking.
- The shared goal is to generate random DNA references over `A/T/C/G`, simulate reads under controlled variables, run each teammate's reconstruction algorithm, and compare performance.
- The main deliverable is the evaluation environment: experiment setup, runners, metrics, result recording, and visualization/reporting.
- Do not implement teammates' reconstruction algorithms unless explicitly asked. Each of the four team members owns one algorithm submission.

## Why
- The project should compare four algorithms fairly under the same inputs and controlled variables.
- Experiments must be reproducible so results, graphs, and reports can be checked later.
- Benchmark code should make it easy to vary one factor at a time and explain what changed.

## How
- Keep changes simple and surgical. Avoid speculative framework code or extra abstractions.
- Prefer deterministic experiment configs and seeded random generation.
- Record the full experiment parameters with every result row or output artifact.
- Before running large experiments, include a small verification path that checks generation, read simulation, algorithm execution, and metric calculation end to end.
- Use `.agents/skills/harness/SKILL.md` or `.codex/skills/harness/SKILL.md` for larger workflow or harness design instead of expanding this file.

## Evaluation Defaults
- Controlled variables should include reference length, read length, read count or coverage, sequencing noise/error rate, and random seed.
- Primary metrics should include runtime, reconstruction accuracy or similarity to the reference, and failure/crash rate.
- Track memory usage only if it can be measured without making the benchmark environment unnecessarily complex.
- Graphs and tables must clearly label all controlled variables, fixed parameters, and measured metrics.
