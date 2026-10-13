"""Generate public EXP001 artifacts from canonical processed data, without Nexus.

Run python -m src.presentation.exp001 [--check]. No raw files or research
outputs are written. --check renders in a temporary directory and compares bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import tempfile
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

EXPERIMENT = "EXP001_SPY_AI_SELECTION"
ASSETS = Path("docs/assets")
COLORS = {"A": "#087f8c", "SPY": "#334e68"}
FAMILIES = {"A": "SMA20/50", "B": "Donchian", "C": "RSI2",
            "D": "MACD + SMA100", "E": "SMA100 + ATR"}


def read_inputs(root: Path):
    processed = root / "data/processed" / EXPERIMENT
    metric_path = processed / "metrics.json"
    manifest_path = root / "experiments" / EXPERIMENT / "manifest.json"
    result = json.loads(metric_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    paths = [metric_path, manifest_path]
    daily = {}
    for run in ("val_A", "val_SPY", "test_A", "test_SPY"):
        path = processed / f"{run}_daily.csv"
        paths.append(path)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        dates = [date.fromisoformat(row["date"]) for row in rows]
        values = [float(row["portfolio_value"]) for row in rows]
        m = result["metrics"][run]
        if (len(rows) != m["daily_row_count"] or dates[0].isoformat() != m["first_date"]
                or dates[-1].isoformat() != m["last_date"]
                or any(a >= b for a, b in zip(dates, dates[1:]))
                or any(not math.isfinite(v) or v <= 0 for v in values)
                or values[-1] != m["ending_value"]):
            raise ValueError(f"Canonical CSV disagrees with metrics: {run}")
        daily[run] = (dates, values)
    for prefix in ("val", "test"):
        if daily[f"{prefix}_A"][0] != daily[f"{prefix}_SPY"][0]:
            raise ValueError(f"Unaligned comparison dates: {prefix}")
    if result["development_selection"]["winner"] != "dev_A":
        raise ValueError("Presentation requires the frozen EXP001 winner")
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths}
    return manifest, result, daily, hashes


def summary_table(metrics: dict, prefix: str) -> str:
    lines = ["| Portfolio | Total return | Ann. volatility | Sharpe (RF=0) | Sortino | Max drawdown |",
             "|---|---:|---:|---:|---:|---:|"]
    for suffix, label in (("A", "Candidate A"), ("SPY", "SPY buy-and-hold")):
        m = metrics[f"{prefix}_{suffix}"]
        lines.append(f"| {label} | {m['total_return']:.2%} | {m['annualized_volatility']:.2%} | "
                     f"{m['sharpe']:.3f} | {m['sortino']:.3f} | {m['maximum_drawdown']:.2%} |")
    return "\n".join(lines)


def readme(manifest: dict, result: dict, registry=None) -> str:
    """Project overview with EXP001 tables rendered from canonical records."""
    template = Path(__file__).with_name("README.template.md").read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[2]
    validation = root / "docs/acceleration/phase4a_validation.json"
    pilot_validation = root / "docs/acceleration/phase4a_procurement_validation.json"
    if pilot_validation.exists():
        validation = pilot_validation
    fda_validation = root / "docs/acceleration/phase4a_fda_validation.json"
    if fda_validation.exists():
        validation = fda_validation
    merger_validation = root / "docs/acceleration/phase4a_merger_validation.json"
    if merger_validation.exists():
        validation = merger_validation
    source_first_validation = root / "docs/acceleration/phase4a_source_first_validation.json"
    if source_first_validation.exists():
        validation = source_first_validation
    integration_validation = root / "docs/acceleration/phase4a_integration_validation.json"
    if integration_validation.exists():
        validation = integration_validation
    closure_validation = root / "docs/acceleration/exp006_closure_validation.json"
    if closure_validation.exists():
        validation = closure_validation
    remedy_validation = root / "docs/acceleration/exp006_remedy_validation.json"
    if remedy_validation.exists():
        validation = remedy_validation
    date_repair_validation = root / "docs/acceleration/exp006_date_repair_validation.json"
    if date_repair_validation.exists():
        validation = date_repair_validation
    population_validation = root / "docs/acceleration/exp006_historical_population_validation.json"
    if population_validation.exists():
        validation = population_validation
    identity_validation = root / "docs/acceleration/exp006_identity_validation.json"
    if identity_validation.exists():
        validation = identity_validation
    cover_validation = root / "docs/acceleration/exp006_cover_identity_validation.json"
    if cover_validation.exists():
        validation = cover_validation
    congress_validation = root / "docs/acceleration/exp007_validation.json"
    if congress_validation.exists():
        validation = congress_validation
    house_validation = root / "docs/acceleration/exp007_house_validation.json"
    if house_validation.exists():
        validation = house_validation
    if validation.exists():
        receipt = json.loads(validation.read_bytes())
        checks = (f"Latest milestone validation: **{receipt['local_tests_passed']} local tests, "
                  f"{receipt['public_tests_passed']} public tests, {receipt['tests_skipped']} skipped**. "
                  f"See [validation receipt](docs/acceleration/{validation.name}).")
    else:
        receipt = json.loads((root / "docs/acceleration/phase3_final_validation.json").read_bytes())
        checks = (f"Final Phase 3 verified baseline: **{receipt['local_tests_passed']} local tests, "
                  f"{receipt['public_tests_passed']} public tests, {receipt['tests_skipped']} skipped**. "
                  "See [validation receipt](docs/acceleration/phase3_final_validation.json).")
    values = {"CHECKS": checks,
              "VALIDATION_TABLE": summary_table(result["metrics"], "val"),
              "TEST_TABLE": summary_table(result["metrics"], "test")}
    extra = []
    for card in registry or []:
        import re
        identifier = card['experiment']
        if not re.fullmatch(r'EXP[0-9]{3,}', identifier) or identifier == 'EXP001':
            raise ValueError('Invalid additional registry identifier')
        clean = lambda text: str(text).replace('|', '/').replace('\n', ' ').replace('<', '').replace('>', '')
        extra.append(f"| [{identifier}](reports/{identifier}_report.md) | {clean(card['stage'])} | {clean(card['finding'])} |")
    values['ADDITIONAL_REGISTRY'] = ("Additional canonical registry cards:\n\n| Experiment | Stage | Finding |\n| --- | --- | --- |\n" + '\n'.join(extra)) if extra else ''
    values.update({key.upper(): f"{manifest[key]['start']} to {manifest[key]['end']}"
                   for key in ("development", "validation", "test")})
    for key, value in values.items():
        marker = "@@" + key + "@@"
        if marker not in template:
            raise ValueError("Missing README template marker: " + key)
        template = template.replace(marker, value)
    if "@@" in template:
        raise ValueError("Unresolved README template marker")
    return template


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#cbd5e1", "axes.labelcolor": "#334155",
                         "text.color": "#172b4d", "xtick.color": "#475569",
                         "ytick.color": "#475569", "figure.facecolor": "white",
                         "axes.facecolor": "white", "savefig.dpi": 160})


def format_dates(ax):
    dates = ax.lines[0].get_xdata()
    ax.set_xlim(dates[0], dates[-1])
    months = [1, 7] if (dates[-1] - dates[0]).days > 1000 else [1, 4, 7, 10]
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=months))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.set_xlabel("New York session date")
    ax.grid(axis="y", color="#e2e8f0", linewidth=.7)
    ax.set_axisbelow(True)


def save(fig, target: Path):
    fig.savefig(target, metadata={"Software": "EXP001 presentation renderer"})
    plt.close(fig)


def charts(output: Path, result: dict, daily: dict):
    style()
    for prefix, title in (("val", "Validation"), ("test", "Held-out Test")):
        fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
        for suffix, label in (("A", "Candidate A · SMA20/50"), ("SPY", "SPY buy-and-hold")):
            dates, values = daily[f"{prefix}_{suffix}"]
            ax.plot(dates, values, color=COLORS[suffix], linewidth=1.6, label=label)
        ax.set_title(f"EXP001 | {title} equity", loc="left", fontweight="bold", pad=15)
        ax.set_ylabel("Portfolio value (USD)")
        # Zero baseline keeps the magnitude of dollar growth in context.
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value/1000:,.0f}k"))
        format_dates(ax)
        ax.legend(frameon=False, loc="upper left")
        save(fig, output / f"exp001_{'validation' if prefix == 'val' else 'test'}_equity.png")
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.8), layout="constrained")
    for ax, prefix, title in zip(axes, ("val", "test"), ("Validation", "Held-out Test")):
        for suffix, label in (("A", "Candidate A"), ("SPY", "SPY buy-and-hold")):
            dates, values = daily[f"{prefix}_{suffix}"]
            peak = values[0]
            losses = []
            for value in values:
                peak = max(peak, value)
                losses.append(value / peak - 1)
            ax.plot(dates, losses, color=COLORS[suffix], linewidth=1.4, label=label)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_ylabel("Drawdown from period peak")
        ax.set_ylim(-.28, .015)
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        format_dates(ax)
        ax.legend(frameon=False, loc="lower left", ncols=2)
    fig.suptitle("EXP001 | Session-close drawdown", x=.07, ha="left", fontweight="bold")
    save(fig, output / "exp001_drawdowns.png")
    fig, ax = plt.subplots(figsize=(8.5, 4.8), layout="constrained")
    for letter in FAMILIES:
        m = result["metrics"][f"dev_{letter}"]
        eligible = result["development_selection"]["candidates"][f"dev_{letter}"]["eligible"]
        color = COLORS["A"] if letter == "A" else (COLORS["SPY"] if eligible else "#b45309")
        ax.scatter(m["annualized_volatility"], m["total_return"], color=color,
                   s=100 if letter == "A" else 60, marker="o" if eligible else "X", zorder=3)
        status = " (selected)" if letter == "A" else (" (ineligible)" if not eligible else "")
        ax.annotate(f"{letter} · {FAMILIES[letter]}" + status,
                    (m["annualized_volatility"], m["total_return"]),
                    xytext=(8, -15 if letter == "D" else 5), textcoords="offset points", fontsize=9)
    ax.set_title("EXP001 | Development risk and return", loc="left", fontweight="bold", pad=15)
    ax.set_xlabel("Annualized volatility (sample daily SD × √252)")
    ax.set_ylabel("Total return · 2015–2021")
    ax.set_xlim(0, .15)
    ax.set_ylim(-.55, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.axhline(0, color="#94a3b8", linewidth=.8)
    ax.grid(color="#e2e8f0", linewidth=.7)
    ax.set_axisbelow(True)
    save(fig, output / "exp001_development_risk_return.png")


def generate(root: Path, destination: Path) -> list[Path]:
    manifest, result, daily, hashes = read_inputs(root)
    registry_path=root/'experiments/registry.json'
    registry=json.loads(registry_path.read_text()) if registry_path.exists() else []
    if registry_path.exists():hashes['experiments/registry.json']=hashlib.sha256(registry_path.read_bytes()).hexdigest()
    output = destination / ASSETS
    output.mkdir(parents=True, exist_ok=True)
    charts(output, result, daily)
    (destination / "README.md").write_text(readme(manifest, result, registry), encoding="utf-8", newline="\n")
    provenance = {"generator": "python -m src.presentation.exp001",
                  "source_sha256": hashes, "matplotlib_version": matplotlib.__version__,
                  "artifacts": [p.name for p in sorted(output.glob("*.png"))]}
    (output / "exp001_sources.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="\n")
    return [Path("README.md"), *[ASSETS / p.name for p in sorted(output.iterdir()) if p.is_file()]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.check:
        with tempfile.TemporaryDirectory(prefix="exp001-presentation-") as directory:
            destination = Path(directory)
            artifacts = generate(root, destination)
            stale = [p.as_posix() for p in artifacts
                     if not (root / p).exists() or (root / p).read_bytes() != (destination / p).read_bytes()]
            if stale:
                raise SystemExit("Stale presentation artifacts: " + ", ".join(stale))
        print(f"Presentation check passed: {len(artifacts)} deterministic artifacts")
    else:
        artifacts = generate(root, root)
        print("Generated: " + ", ".join(p.as_posix() for p in artifacts))


if __name__ == "__main__":
    main()
