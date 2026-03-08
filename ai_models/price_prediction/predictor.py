"""
Live prediction service — loads saved artefacts and returns predicted price
for a given (crop, variety, market, month) query.
Thread-safe singleton that lazy-loads model once.
"""

import os
import json
import threading
import numpy as np
import pandas as pd
import torch
import joblib

from .model import PriceLSTM
from .preprocessing import (
    ARTIFACTS_DIR,
    CSV_PATH,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET,
    VMD_K,
    VMD_ALPHA,
    VMD_TAU,
    VMD_DC,
    VMD_INIT,
    VMD_TOL,
    LOOKBACK,
    build_feature_columns,
    load_dataset,
    add_cyclic_month,
)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

_lock = threading.Lock()
_loaded = {
    "model": None,
    "meta": None,
    "encoders": None,
    "feat_scaler": None,
    "tgt_scaler": None,
    "df": None,
}


def invalidate_cache():
    """
    Signal the predictor to reload artifacts on the next request.
    Called by the auto-retrain pipeline after a new model version is saved.
    Thread-safe: the next call to _ensure_loaded() will re-read from disk.
    """
    with _lock:
        _loaded["model"] = None
        _loaded["meta"] = None
        _loaded["encoders"] = None
        _loaded["feat_scaler"] = None
        _loaded["tgt_scaler"] = None
        _loaded["df"] = None


def _ensure_loaded():
    """Lazy-load all artefacts once (thread-safe)."""
    if _loaded["model"] is not None:
        return
    with _lock:
        if _loaded["model"] is not None:
            return  # another thread loaded while we waited

        meta_path = os.path.join(ARTIFACTS_DIR, "model_meta.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(
                "Model artefacts not found. Run the training pipeline first: "
                "python manage.py train_price_model"
            )

        with open(meta_path) as f:
            meta = json.load(f)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = PriceLSTM(
            input_size=meta["input_size"],
            hidden_size=meta["best_params"]["hidden_size"],
            num_layers=meta["best_params"]["num_layers"],
            dropout=0.0,  # no dropout at inference
        ).to(device)
        model.load_state_dict(
            torch.load(os.path.join(ARTIFACTS_DIR, "lstm_model.pt"), map_location=device, weights_only=True)
        )
        model.eval()

        _loaded["model"] = model
        _loaded["meta"] = meta
        _loaded["encoders"] = joblib.load(os.path.join(ARTIFACTS_DIR, "label_encoders.pkl"))
        _loaded["feat_scaler"] = joblib.load(os.path.join(ARTIFACTS_DIR, "feature_scaler.pkl"))
        _loaded["tgt_scaler"] = joblib.load(os.path.join(ARTIFACTS_DIR, "target_scaler.pkl"))

        # Pre-load processed DataFrame for historical lookback
        df = load_dataset(CSV_PATH)
        df = add_cyclic_month(df)
        _loaded["df"] = df


def get_dropdown_options():
    """
    Return the valid dropdown values from the dataset.
    Uses the raw CSV so it works even before training.
    """
    try:
        df = load_dataset(CSV_PATH)
    except Exception:
        return {"commodities": [], "varieties": {}, "markets": [], "months": []}

    commodities = sorted(df["Commodity"].unique().tolist())
    varieties = {}
    for c in commodities:
        varieties[c] = sorted(df.loc[df["Commodity"] == c, "Variety"].unique().tolist())
    markets = sorted(df["Market"].unique().tolist())
    months = list(range(1, 13))

    return {
        "commodities": commodities,
        "varieties": varieties,
        "markets": markets,
        "months": months,
    }


def predict_price(commodity, variety, market, month):
    """
    Predict next-month Price_per_KG for the given inputs.

    Returns dict:
        {
            "predicted_price": float,
            "price_low": float,
            "price_high": float,
            "advisory": str,
        }
    """
    _ensure_loaded()

    model = _loaded["model"]
    meta = _loaded["meta"]
    encoders = _loaded["encoders"]
    feat_scaler = _loaded["feat_scaler"]
    tgt_scaler = _loaded["tgt_scaler"]
    df_raw = _loaded["df"]

    # Normalise inputs (title-case, underscore)
    commodity = commodity.strip().title()
    variety = variety.strip().title().replace(" ", "_")
    market = market.strip().title()

    # ---- Get latest LOOKBACK rows for this combination ----
    mask = (
        (df_raw["Commodity"] == commodity) &
        (df_raw["Variety"] == variety) &
        (df_raw["Market"] == market)
    )
    group = df_raw.loc[mask].sort_values(["Year", "Month"]).tail(LOOKBACK).copy()

    if len(group) < LOOKBACK:
        raise ValueError(
            f"Not enough historical data for {commodity}/{variety}/{market}. "
            f"Need {LOOKBACK} months, found {len(group)}."
        )

    # ---- Override month to the prediction target ----
    # We set the *last row* month to the requested prediction month
    group.iloc[-1, group.columns.get_loc("Month")] = month
    group["Month_sin"] = np.sin(2 * np.pi * group["Month"] / 12)
    group["Month_cos"] = np.cos(2 * np.pi * group["Month"] / 12)

    # ---- Encode categoricals ----
    for col in CATEGORICAL_FEATURES:
        group[col] = encoders[col].transform(group[col])

    feature_cols = build_feature_columns()
    feat_matrix = feat_scaler.transform(group[feature_cols].values)

    # ---- VMD on the price column (scaled) ----
    price_scaled = tgt_scaler.transform(group[[TARGET]].values).flatten()
    from vmdpy import VMD as _VMD

    if len(price_scaled) >= 10:
        modes, _, _ = _VMD(price_scaled.astype(np.float64),
                           VMD_ALPHA, VMD_TAU, VMD_K, VMD_DC, VMD_INIT, VMD_TOL)
    else:
        modes = np.tile(price_scaled, (VMD_K, 1))

    full_features = np.hstack([feat_matrix, modes.T])  # (LOOKBACK, n_features + VMD_K)

    # ---- Predict ----
    device = next(model.parameters()).device
    x_tensor = torch.tensor(full_features, dtype=torch.float32).unsqueeze(0).to(device)

    with torch.no_grad():
        pred_scaled = model(x_tensor).cpu().numpy().item()

    predicted_price = float(
        tgt_scaler.inverse_transform([[pred_scaled]])[0, 0]
    )

    # ---- Confidence range (simple heuristic based on model MAPE) ----
    mape = meta["metrics"].get("mape_pct", 5.0)
    margin = predicted_price * (mape / 100.0)
    price_low = max(0.0, predicted_price - margin)
    price_high = predicted_price + margin

    # ---- Advisory text ----
    # Compare predicted price with last known price
    last_real_price = float(
        tgt_scaler.inverse_transform([[price_scaled[-1]]])[0, 0]
    )
    if predicted_price > last_real_price * 1.05:
        advisory = "Price is expected to increase. Consider holding stock for better returns."
    elif predicted_price < last_real_price * 0.95:
        advisory = "Price may decrease. Selling earlier could help avoid losses."
    else:
        advisory = "Price is expected to remain stable. Market conditions look steady."

    return {
        "predicted_price": round(predicted_price, 2),
        "price_low": round(price_low, 2),
        "price_high": round(price_high, 2),
        "advisory": advisory,
        "commodity": commodity,
        "variety": variety,
        "market": market,
        "month": month,
    }


def get_price_history(commodity, variety, market, limit=24):
    """
    Return recent monthly prices for the chart.
    Returns list of dicts [{year, month, price}, …].
    """
    try:
        df = load_dataset(CSV_PATH)
    except Exception:
        return []

    commodity = commodity.strip().title()
    variety = variety.strip().title().replace(" ", "_")
    market = market.strip().title()

    mask = (
        (df["Commodity"] == commodity) &
        (df["Variety"] == variety) &
        (df["Market"] == market)
    )
    grp = df.loc[mask].sort_values(["Year", "Month"]).tail(limit)
    return [
        {"year": int(r.Year), "month": int(r.Month), "price": float(r.Price_per_KG)}
        for _, r in grp.iterrows()
    ]
