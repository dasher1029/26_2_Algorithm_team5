"""Create benchmark figures and HTML reports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import os
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib_cache").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


FIGURE_DPI = 180
BROKEN_AXIS_RATIO = 8.0
ACCURACY_BREAK_GAP = 0.15
FACTOR_COLUMNS = [
    "reference_length",
    "read_length",
    "coverage",
    "noise_rate",
    "genome_mutation_rate",
    "reference_start",
]


@dataclass(frozen=True)
class FigureSpec:
    path: Path
    title: str
    description: str


def _set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook", palette="tab10")
    plt.rcParams.update(
        {
            "figure.figsize": (10, 5.8),
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.titlesize": 13,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def _label(column: str) -> str:
    labels = {
        "reference_length": "Reference Length",
        "read_length": "Read Length",
        "coverage": "Coverage",
        "noise_rate": "Noise Rate",
        "genome_mutation_rate": "Genome Mutation Rate",
        "reference_start": "Reference Start",
        "runtime_seconds": "Runtime (seconds)",
        "accuracy": "Accuracy",
        "hamming_distance": "Hamming Distance",
        "edit_distance": "Edit Distance",
        "mutation_recall": "Mutation Recall",
        "peak_memory_mb": "Peak Memory (MB)",
    }
    return labels.get(column, column.replace("_", " ").title())


METRIC_COLUMNS = [
    "accuracy",
    "runtime_seconds",
    "failure_rate",
    "hamming_distance",
    "edit_distance",
    "mutation_recall",
    "variant_count",
    "peak_memory_mb",
]


def _numeric_columns(data: pd.DataFrame) -> pd.DataFrame:
    converted = data.copy()
    for column in FACTOR_COLUMNS + METRIC_COLUMNS:
        if column in converted.columns:
            converted[column] = pd.to_numeric(converted[column], errors="coerce")
    return converted


def _save_lineplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output: Path,
) -> None:
    plt.figure()
    sns.lineplot(data=data, x=x, y=y, hue="algorithm", marker="o", errorbar="sd")
    plt.title(title)
    plt.xlabel(_label(x))
    plt.ylabel(ylabel)
    if y == "accuracy":
        plt.ylim(0, 1.02)
    plt.legend(title="Algorithm", loc="best")
    plt.tight_layout()
    plt.savefig(output, dpi=FIGURE_DPI)
    plt.close()


def _runtime_break(values: pd.Series) -> tuple[float, float] | None:
    positive = values.dropna()
    positive = positive[positive > 0].sort_values()
    if len(positive) < 3:
        return None

    best_low = 0.0
    best_high = 0.0
    best_ratio = 0.0
    for index in range(len(positive) - 1):
        low = float(positive.iloc[index])
        high = float(positive.iloc[index + 1])
        ratio = high / low
        if ratio > best_ratio:
            best_low = low
            best_high = high
            best_ratio = ratio

    if best_low <= 0 or best_ratio < BROKEN_AXIS_RATIO:
        return None
    return best_low * 1.25, best_high * 0.85


def _accuracy_break(values: pd.Series) -> tuple[float, float] | None:
    scores = values.dropna()
    scores = scores[(scores >= 0) & (scores <= 1)].sort_values()
    if len(scores) < 3:
        return None

    best_low = 0.0
    best_high = 0.0
    best_gap = 0.0
    for index in range(len(scores) - 1):
        low = float(scores.iloc[index])
        high = float(scores.iloc[index + 1])
        gap = high - low
        if gap > best_gap:
            best_low = low
            best_high = high
            best_gap = gap

    if best_gap < ACCURACY_BREAK_GAP:
        return None
    return min(best_low + 0.05, 0.95), max(best_high - 0.02, 0.0)


def _axis_break(values: pd.Series, metric: str) -> tuple[float, float] | None:
    if metric in {"runtime_seconds", "peak_memory_mb"}:
        return _runtime_break(values)
    if metric == "accuracy":
        return _accuracy_break(values)
    return None


def _top_ylim(data: pd.DataFrame, y: str, upper_min: float) -> tuple[float, float]:
    if y == "accuracy":
        return upper_min, 1.02
    return upper_min, float(data[y].max()) * 1.08


def _add_break_marks(top_axis, bottom_axis) -> None:
    kwargs = dict(marker=[(-1, -0.5), (1, 0.5)], markersize=11, linestyle="none", color="k", mec="k", mew=1)
    top_axis.plot([0, 1], [0, 0], transform=top_axis.transAxes, clip_on=False, **kwargs)
    bottom_axis.plot([0, 1], [1, 1], transform=bottom_axis.transAxes, clip_on=False, **kwargs)


def _save_broken_barplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output: Path,
) -> None:
    split = _axis_break(data[y], y)
    if split is None:
        _save_barplot(data, x, y, title, ylabel, output)
        return

    lower_max, upper_min = split
    figure, (top_axis, bottom_axis) = plt.subplots(
        2,
        1,
        sharex=True,
        gridspec_kw={"height_ratios": [1, 2], "hspace": 0.05},
        figsize=(10, 6.4),
    )
    sns.barplot(data=data, x=x, y=y, ax=top_axis)
    sns.barplot(data=data, x=x, y=y, ax=bottom_axis)

    top_axis.set_ylim(*_top_ylim(data, y, upper_min))
    bottom_axis.set_ylim(0, lower_max)
    top_axis.set_title(title)
    top_axis.set_xlabel("")
    top_axis.set_ylabel(ylabel)
    bottom_axis.set_xlabel(_label(x))
    bottom_axis.set_ylabel(ylabel)
    top_axis.spines["bottom"].set_visible(False)
    bottom_axis.spines["top"].set_visible(False)
    bottom_axis.tick_params(axis="x", rotation=25)
    for label in bottom_axis.get_xticklabels():
        label.set_ha("right")
    _add_break_marks(top_axis, bottom_axis)
    figure.subplots_adjust(left=0.10, right=0.97, bottom=0.16, top=0.90, hspace=0.06)
    figure.savefig(output, dpi=FIGURE_DPI)
    plt.close(figure)


def _save_broken_lineplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output: Path,
) -> None:
    split = _axis_break(data[y], y)
    if split is None:
        _save_lineplot(data, x, y, title, ylabel, output)
        return

    lower_max, upper_min = split
    figure, (top_axis, bottom_axis) = plt.subplots(
        2,
        1,
        sharex=True,
        gridspec_kw={"height_ratios": [1, 2], "hspace": 0.05},
        figsize=(10, 6.4),
    )
    sns.lineplot(data=data, x=x, y=y, hue="algorithm", marker="o", errorbar="sd", ax=top_axis)
    sns.lineplot(data=data, x=x, y=y, hue="algorithm", marker="o", errorbar="sd", ax=bottom_axis)

    top_axis.set_ylim(*_top_ylim(data, y, upper_min))
    bottom_axis.set_ylim(0, lower_max)
    top_axis.set_title(title)
    top_axis.set_xlabel("")
    top_axis.set_ylabel(ylabel)
    bottom_axis.set_xlabel(_label(x))
    bottom_axis.set_ylabel(ylabel)
    top_axis.spines["bottom"].set_visible(False)
    bottom_axis.spines["top"].set_visible(False)
    top_axis.legend(title="Algorithm", loc="best")
    bottom_axis.legend_.remove()
    _add_break_marks(top_axis, bottom_axis)
    figure.subplots_adjust(left=0.10, right=0.97, bottom=0.16, top=0.90, hspace=0.06)
    figure.savefig(output, dpi=FIGURE_DPI)
    plt.close(figure)


def _save_barplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output: Path,
) -> None:
    plt.figure()
    sns.barplot(data=data, x=x, y=y)
    plt.title(title)
    plt.xlabel(_label(x))
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    if y == "accuracy":
        plt.ylim(0, 1.02)
    plt.tight_layout()
    plt.savefig(output, dpi=FIGURE_DPI)
    plt.close()


def _save_scatter(data: pd.DataFrame, output: Path) -> None:
    plt.figure()
    sns.scatterplot(
        data=data,
        x="runtime_seconds",
        y="accuracy",
        hue="algorithm",
        style="algorithm",
        s=110,
    )
    plt.title("Accuracy vs Runtime")
    plt.xlabel("Runtime (seconds)")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.02)
    plt.legend(title="Algorithm", loc="best")
    plt.tight_layout()
    plt.savefig(output, dpi=FIGURE_DPI)
    plt.close()


def _save_failure_rate(data: pd.DataFrame, output: Path) -> None:
    summary = (
        data.assign(failed=data["status"] != "ok")
        .groupby("algorithm", as_index=False)["failed"]
        .mean()
    )
    summary["failure_rate"] = summary["failed"] * 100
    plt.figure()
    sns.barplot(data=summary, x="algorithm", y="failure_rate")
    plt.title("Failure Rate by Algorithm")
    plt.xlabel("Algorithm")
    plt.ylabel("Failure Rate (%)")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output, dpi=FIGURE_DPI)
    plt.close()


def _varied_factors(data: pd.DataFrame) -> list[str]:
    return [
        column
        for column in FACTOR_COLUMNS
        if column in data.columns and data[column].dropna().nunique() > 1
    ]


def _save_factor_figures(
    ok: pd.DataFrame,
    factor: str,
    figures_dir: Path,
) -> list[FigureSpec]:
    specs: list[FigureSpec] = []
    outputs = [
        (
            "accuracy",
            "Accuracy",
            f"accuracy_by_{factor}.png",
            f"Accuracy by {_label(factor)}",
            f"Shows how reconstruction accuracy changes as {_label(factor).lower()} changes.",
        ),
        (
            "runtime_seconds",
            "Runtime (seconds)",
            f"runtime_by_{factor}.png",
            f"Runtime by {_label(factor)}",
            f"Shows how execution time changes as {_label(factor).lower()} changes.",
        ),
        (
            "peak_memory_mb",
            "Peak Memory (MB)",
            f"memory_by_{factor}.png",
            f"Peak Memory by {_label(factor)}",
            f"Shows how peak memory usage changes as {_label(factor).lower()} changes.",
        ),
    ]
    for y, ylabel, filename, title, description in outputs:
        path = figures_dir / filename
        plot_data = ok.dropna(subset=[factor, y])
        if plot_data.empty:
            continue
        if y in {"accuracy", "runtime_seconds", "peak_memory_mb"}:
            _save_broken_lineplot(plot_data, factor, y, title, ylabel, path)
        else:
            _save_lineplot(plot_data, factor, y, title, ylabel, path)
        specs.append(FigureSpec(path, title, description))
    return specs


def create_figures(results_csv: Path, output_dir: Path) -> list[FigureSpec]:
    _set_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    data = _numeric_columns(pd.read_csv(results_csv))
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    for old_figure in figures_dir.glob("*.png"):
        old_figure.unlink()

    if data.empty:
        return []

    ok = data[data["status"] == "ok"].copy()
    figures: list[FigureSpec] = []

    if not ok.empty:
        summary_aggregations = {
            "accuracy": ("accuracy", "mean"),
            "runtime_seconds": ("runtime_seconds", "mean"),
        }
        if "peak_memory_mb" in ok.columns:
            summary_aggregations["peak_memory_mb"] = ("peak_memory_mb", "mean")
        summary = (
            ok.groupby("algorithm", as_index=False)
            .agg(**summary_aggregations)
            .sort_values(["accuracy", "runtime_seconds"], ascending=[False, True])
        )
        accuracy_summary = figures_dir / "summary_accuracy_by_algorithm.png"
        _save_broken_barplot(
            summary,
            "algorithm",
            "accuracy",
            "Mean Accuracy by Algorithm",
            "Mean Accuracy",
            accuracy_summary,
        )
        figures.append(
            FigureSpec(
                accuracy_summary,
                "Mean Accuracy by Algorithm",
                "Compares average accuracy across all successful runs.",
            )
        )

        runtime_summary = figures_dir / "summary_runtime_by_algorithm.png"
        _save_broken_barplot(
            summary,
            "algorithm",
            "runtime_seconds",
            "Mean Runtime by Algorithm",
            "Mean Runtime (seconds)",
            runtime_summary,
        )
        figures.append(
            FigureSpec(
                runtime_summary,
                "Mean Runtime by Algorithm",
                "Compares average runtime across all successful runs.",
            )
        )

        if "peak_memory_mb" in summary.columns:
            memory_summary_data = summary.dropna(subset=["peak_memory_mb"])
        else:
            memory_summary_data = pd.DataFrame()
        if not memory_summary_data.empty:
            memory_summary = figures_dir / "summary_memory_by_algorithm.png"
            _save_broken_barplot(
                memory_summary_data,
                "algorithm",
                "peak_memory_mb",
                "Mean Peak Memory by Algorithm",
                "Mean Peak Memory (MB)",
                memory_summary,
            )
            figures.append(
                FigureSpec(
                    memory_summary,
                    "Mean Peak Memory by Algorithm",
                    "Compares average peak memory usage across all successful runs.",
                )
            )

        for factor in _varied_factors(ok):
            figures.extend(_save_factor_figures(ok, factor, figures_dir))

        scatter_path = figures_dir / "accuracy_vs_runtime.png"
        _save_scatter(ok, scatter_path)
        figures.append(
            FigureSpec(
                scatter_path,
                "Accuracy vs Runtime",
                "Shows the tradeoff between speed and accuracy for successful runs.",
            )
        )

    failure_path = figures_dir / "failure_rate_by_algorithm.png"
    _save_failure_rate(data, failure_path)
    figures.append(
        FigureSpec(
            failure_path,
            "Failure Rate by Algorithm",
            "Shows the percentage of crash or timeout rows for each algorithm.",
        )
    )
    return figures


def _summary_table(data: pd.DataFrame) -> str:
    if data.empty:
        return "<p>No benchmark rows were recorded.</p>"

    aggregations = {
        "runs": ("algorithm", "size"),
        "ok_runs": ("status", lambda values: int((values == "ok").sum())),
        "mean_accuracy": ("accuracy", "mean"),
        "mean_runtime_seconds": ("runtime_seconds", "mean"),
    }
    for column, alias in (
        ("edit_distance", "mean_edit_distance"),
        ("mutation_recall", "mean_mutation_recall"),
        ("peak_memory_mb", "mean_peak_memory_mb"),
    ):
        if column in data.columns:
            aggregations[alias] = (column, "mean")

    summary = (
        data.groupby("algorithm", as_index=False)
        .agg(**aggregations)
        .sort_values(["mean_accuracy", "mean_runtime_seconds"], ascending=[False, True])
    )
    return summary.to_html(index=False, float_format=lambda value: f"{value:.4f}", border=0)


def _factor_table(data: pd.DataFrame) -> str:
    rows = []
    for column in FACTOR_COLUMNS:
        if column not in data.columns:
            continue
        values = sorted(data[column].dropna().unique())
        rows.append(
            {
                "factor": _label(column),
                "unique_values": len(values),
                "values": ", ".join(str(value) for value in values[:10]),
            }
        )
    if not rows:
        return "<p>No factor columns were recorded.</p>"
    return pd.DataFrame(rows).to_html(index=False, border=0)


def create_html_report(results_csv: Path, output_dir: Path, figures: Iterable[FigureSpec]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = _numeric_columns(pd.read_csv(results_csv))
    figure_html = []
    for figure in figures:
        relative = figure.path.relative_to(output_dir)
        title = html.escape(figure.title)
        description = html.escape(figure.description)
        figure_html.append(
            f'<section class="figure-block"><h2>{title}</h2>'
            f'<p class="note">{description}</p>'
            f'<img src="{relative.as_posix()}" alt="{title}"></section>'
        )

    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DNA Reconstruction Benchmark Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #1f2933; background: #f7f9fb; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px; }}
    h1, h2 {{ color: #102a43; margin-bottom: 8px; }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 20px; margin-top: 28px; }}
    .note {{ color: #52606d; margin-top: 0; }}
    .panel {{ background: #ffffff; border: 1px solid #d9e2ec; padding: 20px; margin: 18px 0; }}
    table {{ border-collapse: collapse; margin: 12px 0 8px; width: 100%; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #d9e2ec; padding: 9px; text-align: right; }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{ background: #edf2f7; }}
    img {{ max-width: 100%; border: 1px solid #d9e2ec; background: white; }}
    .figure-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 18px; }}
    .figure-block {{ background: #ffffff; border: 1px solid #d9e2ec; padding: 16px; }}
  </style>
</head>
<body>
  <main>
    <h1>DNA Reconstruction Benchmark Report</h1>
    <p class="note">Generated from <code>{html.escape(str(results_csv))}</code>.</p>
    <section class="panel">
      <h2>Algorithm Summary</h2>
      {_summary_table(data)}
    </section>
    <section class="panel">
      <h2>Experiment Factors</h2>
      <p class="note">Rows below show which factors were recorded and which values were tested.</p>
      {_factor_table(data)}
    </section>
    <section class="figure-grid">
      {''.join(figure_html)}
    </section>
  </main>
</body>
</html>
"""
    report_path = output_dir / "report.html"
    report_path.write_text(report, encoding="utf-8")
    return report_path


def build_report(results_csv: Path, output_dir: Path) -> Path:
    figures = create_figures(results_csv, output_dir)
    return create_html_report(results_csv, output_dir, figures)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build benchmark figures and HTML report.")
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = build_report(args.results, args.out)
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
