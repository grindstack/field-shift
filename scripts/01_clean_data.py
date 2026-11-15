"""
Step 1 - Load and clean every raw CSV in data/raw/.

Outputs (data/processed/):
  <name>_daily_clean.csv     (NASA POWER only)
  <name>_monthly_clean.csv   (power, imerg, ndvi, lst)
  <name>_clean.csv           (soil, srtm - static)
and reports/cleaning_log.json (used later by the report).
"""
from datetime import datetime

import config
import helpers as h


def main():
    h.ensure_dirs()
    assigned, unmatched = h.assign_files()

    print("=" * 70)
    print("FILE MATCHING (by keywords in file names)")
    for key, files in assigned.items():
        print(f"  {key:6s} -> {[p.name for p in files] if files else 'NOT FOUND'}")
    if unmatched:
        print(f"  Unmatched files ignored: {[p.name for p in unmatched]}")
    print("=" * 70)

    log = {"run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "raw_dir": str(config.RAW_DIR),
           "start_month": config.START_MONTH, "end_month": config.END_MONTH,
           "unmatched_files": [p.name for p in unmatched],
           "missing_datasets": [], "sources": []}

    for key, spec in config.DATASETS.items():
        files = assigned[key]
        if not files:
            print(f"\n[WARNING] No file found for '{key}'. Put it in {config.RAW_DIR} "
                  f"(file name should contain one of {spec['keywords']}) or use FILE_OVERRIDES.")
            log["missing_datasets"].append(key)
            continue

        for path in files:
            source_name = key if len(files) == 1 else f"{key}_{h.clean_name(path.stem)}"
            kind = spec["kind"]
            rec = h.new_record(key, source_name, kind, path)
            print(f"\n>>> {source_name} ({kind})  <-  {path.name}")
            try:
                raw, header = h.read_csv_smart(path)
                rec["source_header_lines"] = header
                print(f"   loaded {len(raw)} rows x {raw.shape[1]} columns: {list(raw.columns)}")

                if kind == "daily":
                    daily, vcols = h.process_daily(key, source_name, raw, rec)
                    f_daily = config.PROCESSED_DIR / f"{source_name}_daily_clean.csv"
                    daily.to_csv(f_daily, index=False, date_format="%Y-%m-%d")
                    monthly = h.daily_to_monthly(source_name, daily, vcols, rec)
                    f_month = config.PROCESSED_DIR / f"{source_name}_monthly_clean.csv"
                    monthly.to_csv(f_month, index=False, date_format="%Y-%m-%d")
                    rec["outputs"] = {"daily_file": f_daily.name, "monthly_file": f_month.name}

                elif kind == "monthly":
                    monthly, vcols = h.process_monthly(key, source_name, raw, rec)
                    f_month = config.PROCESSED_DIR / f"{source_name}_monthly_clean.csv"
                    monthly.to_csv(f_month, index=False, date_format="%Y-%m-%d")
                    rec["outputs"] = {"monthly_file": f_month.name}

                else:  # static
                    static = h.process_static(key, source_name, raw, rec)
                    f_static = config.PROCESSED_DIR / f"{source_name}_clean.csv"
                    static.to_csv(f_static, index=False)
                    rec["outputs"] = {"static_file": f_static.name}

                print(f"   saved -> {list(rec['outputs'].values())}")
            except Exception as e:  # keep going with the other files
                rec["status"] = "error"
                rec["error"] = f"{type(e).__name__}: {e}"
                print(f"   [ERROR] {rec['error']}")
            log["sources"].append(rec)

    h.save_json(log, config.REPORT_DIR / "cleaning_log.json")
    print("\nStep 1 finished. Log: reports/cleaning_log.json")


if __name__ == "__main__":
    main()
