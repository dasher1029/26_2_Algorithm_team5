"""Create benchmark figures and HTML reports."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


FIGURE_DPI = 180


def _set_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.figsize": (11, 7),
            "axes.titleweight": "bold",
            "axes.labelsize": 13,
            "axes.titlesize": 15,
            "legend.fontsize": 10,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
        }
    )


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
    plt.xlabel(x.replace("_", " ").title())
    plt.ylabel(ylabel)
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


def create_figures(results_csv: Path, output_dir: Path) -> list[Path]:
    _set_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(results_csv)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if data.empty:
        return []

    ok = data[data["status"] == "ok"].copy()
    figures: list[Path] = []

    if not ok.empty:
        plots = [
            (
                "noise_rate",
                "accuracy",
                "Accuracy vs Sequencing Noise",
                "Accuracy",
                "accuracy_vs_noise.png",
            ),
            (
                "reference_length",
                "runtime_seconds",
                "Runtime vs Reference Length",
                "Runtime (seconds)",
                "runtime_vs_reference_length.png",
            ),
            (
                "read_length",
                "accuracy",
                "Accuracy vs Read Length",
                "Accuracy",
                "accuracy_vs_read_length.png",
            ),
        ]
        for x, y, title, ylabel, filename in plots:
            path = figures_dir / filename
            _save_lineplot(ok, x, y, title, ylabel, path)
            figures.append(path)

        scatter_path = figures_dir / "accuracy_vs_runtime.png"
        _save_scatter(ok, scatter_path)
        figures.append(scatter_path)

    failure_path = figures_dir / "failure_rate_by_algorithm.png"
    _save_failure_rate(data, failure_path)
    figures.append(failure_path)
    return figures


def _summary_table(data: pd.DataFrame) -> str:
    if data.empty:
        return "<p>No benchmark rows were recorded.</p>"

    summary = (
        data.groupby("algorithm", as_index=False)
        .agg(
            runs=("algorithm", "size"),
            ok_runs=("status", lambda values: int((values == "ok").sum())),
            mean_accuracy=("accuracy", "mean"),
            mean_runtime_seconds=("runtime_seconds", "mean"),
        )
        .sort_values(["mean_accuracy", "mean_runtime_seconds"], ascending=[False, True])
    )
    return summary.to_html(index=False, float_format=lambda value: f"{value:.4f}", border=0)


def create_html_report(results_csv: Path, output_dir: Path, figures: Iterable[Path]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(results_csv)
    figure_html = []
    for figure in figures:
        relative = figure.relative_to(output_dir)
        title = html.escape(figure.stem.replace("_", " ").title())
        figure_html.append(f'<section><h2>{title}</h2><img src="{relative.as_posix()}" alt="{title}"></section>')

    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DNA Reconstruction Benchmark Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #102a43; }}
    .note {{ color: #52606d; }}
    table {{ border-collapse: collapse; margin: 16px 0 32px; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d9e2ec; padding: 10px; text-align: right; }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{ background: #f0f4f8; }}
    img {{ max-width: 100%; border: 1px solid #d9e2ec; }}
    section {{ margin-bottom: 36px; }}
  </style>
</head>
<body>
  <h1>DNA Reconstruction Benchmark Report</h1>
  <p class="note">Generated from <code>{html.escape(str(results_csv))}</code>.</p>
  <h2>Algorithm Summary</h2>
  {_summary_table(data)}
  {''.join(figure_html)}
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
