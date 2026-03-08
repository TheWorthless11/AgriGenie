"""
Automatic retraining pipeline for the VMD-LSTM crop price predictor.

Workflow:
  1. Read CSV → detect latest (year, month)
  2. Compare with pipeline_metadata.json → decide if new data exists
  3. Insert only new rows into MySQL CropPriceData table
  4. Retrain model from full DB dataset with versioned artifact saving
  5. Update metadata and promote new model as active

Safe: the current model keeps serving predictions while retraining runs.
The new model is written to a versioned file and only promoted after success.
"""

import os
import json
import shutil
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger("agrigenie.pipeline")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "price_prediction", "artifacts")
CSV_PATH = os.path.join(BASE_DIR, "combined_agriculture_prices.csv")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "pipeline_metadata.json")

# Column mapping (CSV column → Django model field)
COL_MAP = {
    "Year": "year", "Month": "month", "Market": "market",
    "Commodity": "commodity", "Variety": "variety",
    "Price_per_KG": "price_per_kg",
    "Avg_Temp_C": "avg_temp_c", "Max_Temp_C": "max_temp_c",
    "Min_Temp_C": "min_temp_c", "Rainfall_mm": "rainfall_mm",
    "Cumulative_Rainfall_mm": "cumulative_rainfall_mm",
    "Flood": "flood", "Drought": "drought",
    "Yield_per_Hectare": "yield_per_hectare",
    "Production_tonnes": "production_tonnes",
    "Area_Hectares": "area_hectares",
    "Import_tonnes": "import_tonnes", "Export_tonnes": "export_tonnes",
    "Fertilizer_Cost": "fertilizer_cost", "Seed_Cost": "seed_cost",
    "Labor_Cost": "labor_cost", "Fuel_Cost": "fuel_cost",
    "Inflation": "inflation", "CPI": "cpi",
    "Lag1_Price": "lag1_price", "Lag2_Price": "lag2_price",
}


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------
def load_metadata():
    """Load pipeline metadata. Returns defaults if file missing."""
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH) as f:
            return json.load(f)
    return {
        "last_trained_year": 0,
        "last_trained_month": 0,
        "last_csv_rows": 0,
        "model_version": 0,
        "active_model": "lstm_model.pt",
        "training_history": [],
    }


def save_metadata(meta):
    with open(METADATA_PATH, "w") as f:
        json.dump(meta, f, indent=2)


# ---------------------------------------------------------------------------
# Step 1 — Detect new data in CSV
# ---------------------------------------------------------------------------
def detect_new_data(csv_path=CSV_PATH):
    """
    Compare CSV latest month with metadata.
    Returns (has_new_data: bool, csv_latest_year, csv_latest_month, new_row_count).
    """
    meta = load_metadata()
    df = pd.read_csv(csv_path)

    csv_latest_year = int(df["Year"].max())
    csv_latest_month_for_year = int(
        df.loc[df["Year"] == csv_latest_year, "Month"].max()
    )
    csv_row_count = len(df)

    last_year = meta.get("last_trained_year", 0)
    last_month = meta.get("last_trained_month", 0)

    has_new = (
        (csv_latest_year, csv_latest_month_for_year) > (last_year, last_month)
        or csv_row_count > meta.get("last_csv_rows", 0)
    )

    new_rows = csv_row_count - meta.get("last_csv_rows", 0)
    logger.info(
        "CSV latest: %d/%02d (%d rows) | Metadata: %d/%02d (%d rows) | New: %s (+%d rows)",
        csv_latest_year, csv_latest_month_for_year, csv_row_count,
        last_year, last_month, meta.get("last_csv_rows", 0),
        has_new, max(0, new_rows),
    )
    return has_new, csv_latest_year, csv_latest_month_for_year, max(0, new_rows)


# ---------------------------------------------------------------------------
# Step 2 — Sync new rows from CSV into MySQL
# ---------------------------------------------------------------------------
def sync_csv_to_db(csv_path=CSV_PATH):
    """
    Insert only rows that don't yet exist in MySQL (by unique key).
    Returns (inserted, skipped) counts.
    """
    from farmer.models import CropPriceData

    df = pd.read_csv(csv_path)
    df["Variety"] = df["Variety"].str.strip().str.title().str.replace(" ", "_")
    df = df.fillna(0)

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        fields = {}
        for csv_col, model_field in COL_MAP.items():
            v = row[csv_col]
            fields[model_field] = v.item() if hasattr(v, "item") else v

        lookup = {
            "year": fields["year"],
            "month": fields["month"],
            "market": fields["market"],
            "commodity": fields["commodity"],
            "variety": fields["variety"],
        }
        _, created = CropPriceData.objects.get_or_create(
            **lookup, defaults=fields,
        )
        if created:
            inserted += 1
        else:
            skipped += 1

    logger.info("DB sync: inserted=%d, skipped=%d", inserted, skipped)
    return inserted, skipped


# ---------------------------------------------------------------------------
# Step 3 — Versioned retraining
# ---------------------------------------------------------------------------
def retrain_versioned(ga_pop=8, ga_gen=5, verbose=True):
    """
    Retrain from MySQL with versioned artifact saving.

    1. Trains new model → saves as lstm_model_vN.pt (alongside existing model)
    2. On success, copies versioned files to the active names (lstm_model.pt etc.)
    3. Updates pipeline_metadata.json

    Returns (new_version, metrics_dict) or raises on failure.
    """
    import torch
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    from farmer.models import CropPriceData
    from ai_models.price_prediction.train import train_all

    meta = load_metadata()
    new_version = meta.get("model_version", 0) + 1

    row_count = CropPriceData.objects.count()
    if row_count == 0:
        raise ValueError("CropPriceData table is empty — nothing to train on.")

    # Determine data range for logging
    from django.db.models import Min, Max
    agg = CropPriceData.objects.aggregate(
        y_min=Min("year"), y_max=Max("year"),
        m_min=Min("month"), m_max=Max("month"),
    )
    latest_year = agg["y_max"]
    latest_month = int(
        CropPriceData.objects.filter(year=latest_year)
        .aggregate(m=Max("month"))["m"]
    )

    logger.info(
        "Starting retrain v%d on %d rows (data: %d/%02d → %d/%02d)",
        new_version, row_count,
        agg["y_min"], agg["m_min"], latest_year, latest_month,
    )

    # --- Run training (saves artifacts to ARTIFACTS_DIR) ---
    best_model, train_meta = train_all(
        source="db",
        ga_pop=ga_pop,
        ga_gen=ga_gen,
        verbose=verbose,
    )

    # --- Version the main artifacts ---
    versioned_files = {
        "lstm_model.pt": f"lstm_model_v{new_version}.pt",
        "model_meta.json": f"model_meta_v{new_version}.json",
        "label_encoders.pkl": f"label_encoders_v{new_version}.pkl",
        "feature_scaler.pkl": f"feature_scaler_v{new_version}.pkl",
        "target_scaler.pkl": f"target_scaler_v{new_version}.pkl",
    }
    for active_name, versioned_name in versioned_files.items():
        src = os.path.join(ARTIFACTS_DIR, active_name)
        dst = os.path.join(ARTIFACTS_DIR, versioned_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    # --- Update pipeline metadata ---
    metrics = train_meta["metrics"]
    meta["last_trained_year"] = latest_year
    meta["last_trained_month"] = latest_month
    meta["last_csv_rows"] = row_count
    meta["model_version"] = new_version
    meta["active_model"] = f"lstm_model_v{new_version}.pt"
    meta["training_history"].append({
        "version": new_version,
        "trained_at": datetime.now().isoformat(),
        "data_range": f"{agg['y_min']}-{agg['m_min']:02d} to {latest_year}-{latest_month:02d}",
        "rows": row_count,
        "metrics": metrics,
    })
    save_metadata(meta)

    logger.info(
        "Retrain v%d complete — RMSE=%.5f MAE=%.5f MAPE=%.2f%%",
        new_version, metrics["rmse"], metrics["mae"], metrics["mape_pct"],
    )
    return new_version, metrics


# ---------------------------------------------------------------------------
# Step 4 — Full pipeline (detect → sync → retrain)
# ---------------------------------------------------------------------------
def run_pipeline(csv_path=CSV_PATH, ga_pop=8, ga_gen=5, force=False, verbose=True):
    """
    Complete automatic retraining pipeline.

    1. Detect new data in CSV
    2. Sync new rows to MySQL
    3. Retrain model with versioning
    4. Signal predictor to reload (next request picks up new model)

    Args:
        csv_path: path to the CSV
        ga_pop / ga_gen: GA hyper-parameters
        force: retrain even if no new data detected
        verbose: print progress

    Returns dict with status and details.
    """
    result = {
        "status": "skipped",
        "new_data_detected": False,
        "rows_inserted": 0,
        "model_version": None,
        "metrics": None,
    }

    # Step 1 — detect
    has_new, csv_year, csv_month, new_count = detect_new_data(csv_path)
    result["new_data_detected"] = has_new

    if not has_new and not force:
        logger.info("No new data detected. Skipping retrain.")
        if verbose:
            print("No new data detected. Skipping retrain.")
        return result

    if verbose:
        msg = "Forced retrain." if (not has_new and force) else f"New data detected: up to {csv_year}/{csv_month:02d} (+{new_count} rows)"
        print(msg)

    # Step 2 — sync CSV → MySQL
    if verbose:
        print("Syncing CSV → MySQL …")
    inserted, skipped = sync_csv_to_db(csv_path)
    result["rows_inserted"] = inserted
    if verbose:
        print(f"  Inserted: {inserted},  Skipped (existing): {skipped}")

    # Step 3 — retrain
    if verbose:
        print("Starting versioned retrain …")
    new_version, metrics = retrain_versioned(
        ga_pop=ga_pop, ga_gen=ga_gen, verbose=verbose,
    )
    result["status"] = "retrained"
    result["model_version"] = new_version
    result["metrics"] = metrics

    # Step 4 — signal predictor to reload on next request
    from ai_models.price_prediction.predictor import invalidate_cache
    invalidate_cache()

    if verbose:
        print(f"\nPipeline complete — model v{new_version} is now active.")
        print(f"  RMSE={metrics['rmse']:.5f}  MAE={metrics['mae']:.5f}  MAPE={metrics['mape_pct']:.2f}%")

    return result
