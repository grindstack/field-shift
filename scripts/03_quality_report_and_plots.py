"""
Step 3 - Data quality report + basic exploratory graphs.

Outputs:
  reports/data_quality_report.md
  reports/data_quality_summary.csv
  reports/figures/*.png
"""
import matplotlib
matplotlib.use("Agg")  # save to files; no pop-up windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import helpers as h


# ----------------------------------------------------------------------------
# Markdown helpers
# ----------------------------------------------------------------------------
def fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v).replace("|", "/").replace("\n", " ")


def table(df):
    if df is None or len(df) == 0:
        return "_(none)_\n"
    lines = ["| " + " | ".join(map(str, df.columns)) + " |",
             "| " + " | ".join("---" for _ in df.columns) + " |"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines) + "\n"


def bullets(items):
    return "\n".join(f"- {i}" for i in items) + "\n" if items else "_(none)_\n"


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------
def source_section(rec):
    out = [f"## {rec['source_name']}  ({rec['kind']})\n",
           f"- File: `{rec['file']}`", f"- Status: **{rec['status']}**"]
    if rec["status"] != "ok":
        out.append(f"- Error: `{rec.get('error')}`\n")
        return "\n".join(out)
    out += [f"- Rows raw -> after cleaning: {rec.get('rows_raw')} -> {rec.get('rows_after')}",
            f"- Exact duplicate rows removed: {rec.get('exact_duplicates_removed')}",
            f"- Rows sharing a date, merged: {rec.get('duplicate_dates_merged', 'n/a')}",
            f"- Missing-value codes replaced by NaN: {rec.get('sentinel_counts') or 'none found'}"]
    if rec.get("date_method"):
        out.append(f"- Date detected from: {rec['date_method']}")
        out.append(f"- Date range: {str(rec.get('date_min'))[:10]} to {str(rec.get('date_max'))[:10]}")
        out.append(f"- Expected periods in window: {rec.get('expected_periods')}, "
                   f"present: {rec.get('present_periods')}, absent: {rec.get('missing_periods_count')}")
        if rec.get("missing_periods_sample"):
            out.append(f"- First absent months: {', '.join(rec['missing_periods_sample'])}")
    out.append("\n**Original -> standardized column names**\n")
    out.append(table(pd.DataFrame({"original": list(rec["column_mapping"]),
                                   "standardized": list(rec["column_mapping"].values()),
                                   "raw dtype": [rec["dtypes_raw"].get(k) for k in rec["column_mapping"]]})))
    out.append("**Missing values after cleaning**\n")
    miss = rec.get("missing_after", {})
    out.append(table(pd.DataFrame([{"column": c, **v} for c, v in miss.items()])))
    out.append("**Unit / range checks (values never altered, except the noted extra column)**\n")
    out.append(table(pd.DataFrame(rec["unit_checks"])))
    if rec.get("monthly_aggregation_rules"):
        out.append("**Daily -> monthly rules**\n")
        out.append(table(pd.DataFrame({"monthly column": list(rec["monthly_aggregation_rules"]),
                                       "rule": list(rec["monthly_aggregation_rules"].values())})))
    if rec.get("source_header_lines"):
        out.append("**Source file header (NASA POWER lists parameter units here)**\n")
        out.append("```\n" + "\n".join(rec["source_header_lines"][:60]) + "\n```\n")
    out.append("**Warnings**\n")
    out.append(bullets(rec["warnings"]))
    return "\n".join(out)


def write_report(log, mlog, master):
    parts = ["# Field Shift - Data Quality Report\n",
             f"Generated: {log['run_time']}  |  Window: {log['start_month']} to {log['end_month']}\n",
             "## Overview\n",
             f"- Raw folder: `{log['raw_dir']}`",
             f"- Datasets with NO file found: {log['missing_datasets'] or 'none'}",
             f"- Files ignored (no keyword match): {log['unmatched_files'] or 'none'}\n",
             "## Assumptions\n", bullets(config.ASSUMPTIONS)]

    summary_rows = []
    for rec in log["sources"]:
        parts.append(source_section(rec))
        summary_rows.append({"source": rec["source_name"], "kind": rec["kind"], "status": rec["status"],
                             "rows_raw": rec.get("rows_raw"), "rows_after": rec.get("rows_after"),
                             "duplicates_removed": rec.get("exact_duplicates_removed"),
                             "sentinels_replaced": sum((rec.get("sentinel_counts") or {}).values()),
                             "absent_periods": rec.get("missing_periods_count"),
                             "n_warnings": len(rec["warnings"])})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(config.REPORT_DIR / "data_quality_summary.csv", index=False)

    parts.append("## Master monthly table\n")
    if master is not None:
        parts += [f"- Rows: {mlog['rows']} (expected {mlog['n_months_expected']})",
                  f"- Data columns: {len(mlog['columns'])}",
                  f"- Months where EVERY column has a value: {mlog['complete_months']}\n",
                  "**Missing values per column**\n",
                  table(pd.DataFrame([{"column": c, **v} for c, v in mlog["missing_after"].items()])),
                  "**Per-source coverage**\n",
                  table(pd.DataFrame([{"source": s["source"], "months_with_data": s["months_with_data"],
                                       "months_outside_window_dropped": s["months_outside_window_dropped"],
                                       "months_all_empty": len(s["months_all_empty"])}
                                      for s in mlog["sources"]])),
                  "**Static soil / terrain tables**\n",
                  table(pd.DataFrame(mlog["static"]))]
        num = master[mlog["columns"]].select_dtypes("number")
        if not num.empty:
            parts += ["**Basic statistics (master)**\n", table(num.describe().T.reset_index().rename(columns={"index": "column"}))]
    else:
        parts.append("_Master table was not created._\n")

    parts.append("## What to verify manually\n")
    parts.append(bullets([
        "Units of every column (especially IMERG, soil and LST) against the original data source documentation.",
        "Any WARNING listed above, especially multiple locations averaged per month.",
        "Whether the monthly rainfall rule (sum) matches the units in the NASA POWER header.",
    ]))
    with open(config.REPORT_DIR / "data_quality_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote reports/data_quality_report.md and data_quality_summary.csv")


# ----------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------
def save(fig, name):
    fig.savefig(config.FIGURE_DIR / name, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved figures/{name}")


def series_grid(df, xcol, cols, title, stem, per_fig=6, marker=True):
    for i in range(0, len(cols), per_fig):
        chunk = cols[i:i + per_fig]
        fig, axes = plt.subplots(len(chunk), 1, figsize=(11, 2.3 * len(chunk) + 0.9), sharex=True, squeeze=False)
        for ax, c in zip(axes[:, 0], chunk):
            ax.plot(df[xcol], df[c], lw=1, marker="o" if marker else None, ms=2)
            ax.set_ylabel(c, fontsize=8)
            ax.grid(alpha=0.3)
        fig.suptitle(title + " (gaps = missing data)", fontsize=11)
        save(fig, f"{stem}_{i // per_fig + 1}.png")


def grid_axes(n, ncols=3, h_each=2.6):
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, h_each * nrows + 0.6), squeeze=False)
    flat = axes.ravel()
    for ax in flat[n:]:
        ax.axis("off")
    return fig, flat[:n]


def make_plots(log, mlog):
    # --- daily weather -----------------------------------------------------
    for rec in log["sources"]:
        f = rec.get("outputs", {}).get("daily_file")
        if rec["status"] == "ok" and f:
            d = pd.read_csv(config.PROCESSED_DIR / f, parse_dates=["date"])
            series_grid(d, "date", rec["value_columns"], f"{rec['source_name']} daily",
                        f"daily_{rec['source_name']}", marker=False)

    # --- master ------------------------------------------------------------
    path = config.PROCESSED_DIR / "master_monthly.csv"
    if not path.exists():
        print("master_monthly.csv not found; skipping master plots")
        return
    m = pd.read_csv(path, parse_dates=["month"])
    cols = [c for c in mlog["columns"] if pd.api.types.is_numeric_dtype(m[c])]
    if not cols:
        print("no numeric master columns; skipping master plots")
        return

    series_grid(m, "month", cols, "Master monthly series", "master_timeseries")

    # missing % per column
    pct = m[cols].isna().mean().mul(100).sort_values()
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(cols) + 1.5))
    ax.barh(pct.index, pct.values)
    ax.set_xlabel("% of months missing")
    ax.set_title("Missing values per column (master)")
    ax.set_xlim(0, 100)
    save(fig, "master_missing_percent.png")

    # availability matrix
    fig, ax = plt.subplots(figsize=(12, 0.35 * len(cols) + 1.8))
    ax.imshow(m[cols].notna().T.values.astype(int), aspect="auto", cmap="Greens", vmin=0, vmax=1,
              interpolation="nearest")
    ax.set_yticks(range(len(cols)))
    ax.set_yticklabels(cols, fontsize=7)
    ticks = [i for i, d in enumerate(m["month"]) if d.month == 1]
    ax.set_xticks(ticks)
    ax.set_xticklabels([m["month"].iloc[i].year for i in ticks])
    ax.set_title("Data availability by month (green = has value, white = missing)")
    save(fig, "master_availability.png")

    # seasonal cycle
    fig, axes = grid_axes(len(cols))
    seas = m.groupby("month_of_year")[cols].mean()
    for ax, c in zip(axes, cols):
        ax.plot(seas.index, seas[c], marker="o")
        ax.set_title(c, fontsize=8)
        ax.set_xticks(range(1, 13))
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
    fig.suptitle("Average by calendar month (seasonal cycle)")
    fig.tight_layout()
    save(fig, "master_seasonal_cycle.png")

    # histograms
    fig, axes = grid_axes(len(cols))
    for ax, c in zip(axes, cols):
        ax.hist(m[c].dropna(), bins=20)
        ax.set_title(c, fontsize=8)
        ax.tick_params(labelsize=7)
    fig.suptitle("Distributions (master)")
    fig.tight_layout()
    save(fig, "master_histograms.png")

    # correlation
    if len(cols) >= 2:
        corr = m[cols].corr()
        fig, ax = plt.subplots(figsize=(0.7 * len(cols) + 3, 0.7 * len(cols) + 2.5))
        im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols)))
        ax.set_yticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=90, fontsize=7)
        ax.set_yticklabels(cols, fontsize=7)
        if len(cols) <= 15:
            for i in range(len(cols)):
                for j in range(len(cols)):
                    v = corr.values[i, j]
                    if not np.isnan(v):
                        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6)
        fig.colorbar(im, ax=ax, shrink=0.8)
        ax.set_title("Correlation between columns (pairwise, exploratory only)")
        save(fig, "master_correlation.png")


def main():
    h.ensure_dirs()
    log = h.load_json(config.REPORT_DIR / "cleaning_log.json")
    mpath = config.REPORT_DIR / "master_log.json"
    mlog = h.load_json(mpath) if mpath.exists() else None
    master = None
    if mlog and (config.PROCESSED_DIR / "master_monthly.csv").exists():
        master = pd.read_csv(config.PROCESSED_DIR / "master_monthly.csv", parse_dates=["month"])
    write_report(log, mlog, master)
    if mlog:
        make_plots(log, mlog)
    print("Step 3 finished. Open reports/data_quality_report.md and reports/figures/")


if __name__ == "__main__":
    main()
