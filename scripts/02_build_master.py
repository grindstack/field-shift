"""
Step 2 - Combine the cleaned MONTHLY datasets into one master table.

Outputs (data/processed/):
  master_monthly.csv              one row per month in the study window
  master_monthly_with_static.csv  same + soil/terrain constants (only if any could be joined)
  static_features_joined.csv      the static values that were joined (for transparency)
Months missing from a dataset stay EMPTY (NaN). Nothing is filled in.
"""
import pandas as pd

import config
import helpers as h


def main():
    h.ensure_dirs()
    log = h.load_json(config.REPORT_DIR / "cleaning_log.json")

    full = pd.date_range(config.START_MONTH + "-01", config.END_MONTH + "-01", freq="MS", name="month")
    master = pd.DataFrame(index=full)
    mlog = {"window": [config.START_MONTH, config.END_MONTH], "n_months_expected": len(full),
            "sources": [], "static": [], "static_columns": []}

    # ---- monthly sources -------------------------------------------------
    for rec in log["sources"]:
        f = rec.get("outputs", {}).get("monthly_file")
        if rec["status"] != "ok" or not f:
            continue
        df = pd.read_csv(config.PROCESSED_DIR / f, parse_dates=["month"]).set_index("month")
        df = df[[c for c in df.columns if not c.endswith("_n_valid_days")]]
        outside = int((~df.index.isin(full)).sum())
        df = df.reindex(full)
        clash = [c for c in df.columns if c in master.columns]
        if clash:
            df = df.rename(columns={c: f"{c}__{rec['source_name']}" for c in clash})
            print(f"[WARNING] column name clash {clash}: renamed with suffix")
        master = master.join(df)
        first_col = df.columns[0]
        info = {"source": rec["source_name"], "columns": list(df.columns),
                "months_with_data": int(df[first_col].notna().sum()),
                "months_outside_window_dropped": outside,
                "months_all_empty": [d.strftime("%Y-%m") for d in df.index[df.isna().all(axis=1)]]}
        mlog["sources"].append(info)
        print(f"joined {rec['source_name']:12s}: {len(df.columns)} columns, "
              f"{info['months_with_data']}/{len(full)} months with data")

    master["year"] = master.index.year
    master["month_of_year"] = master.index.month
    master = master.reset_index()
    master.to_csv(config.PROCESSED_DIR / "master_monthly.csv", index=False, date_format="%Y-%m-%d")

    data_cols = [c for c in master.columns if c not in ("month", "year", "month_of_year")]
    mlog["columns"] = data_cols
    mlog["rows"] = len(master)
    mlog["complete_months"] = int(master[data_cols].notna().all(axis=1).sum()) if data_cols else 0
    mlog["missing_after"] = h.missing_summary(master, data_cols)

    # ---- static sources --------------------------------------------------
    features = {}
    for rec in log["sources"]:
        f = rec.get("outputs", {}).get("static_file")
        if rec["status"] != "ok" or not f:
            continue
        df = pd.read_csv(config.PROCESSED_DIR / f)
        feat, why = h.static_feature_row(rec["source_name"], df, rec["value_columns"])
        mlog["static"].append({"source": rec["source_name"], "rows": len(df), "joined": feat is not None,
                               "explanation": why})
        print(f"static {rec['source_name']:10s}: {why}")
        if feat:
            features.update(feat)

    if features:
        with_static = master.copy()
        for col, val in features.items():
            with_static[col] = val
        with_static.to_csv(config.PROCESSED_DIR / "master_monthly_with_static.csv",
                           index=False, date_format="%Y-%m-%d")
        pd.DataFrame([features]).to_csv(config.PROCESSED_DIR / "static_features_joined.csv", index=False)
        mlog["static_columns"] = list(features)
        print("saved master_monthly_with_static.csv")
    else:
        print("No static table was joined (see messages above). Static tables remain separate.")

    h.save_json(mlog, config.REPORT_DIR / "master_log.json")
    print("Step 2 finished. Master table: data/processed/master_monthly.csv")


if __name__ == "__main__":
    main()
