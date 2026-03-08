"""
Dataset handling, feature engineering, and preprocessing for crop price prediction.
Handles: loading, cleaning, encoding, scaling, VMD decomposition, LSTM windowing.
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from vmdpy import VMD
import joblib

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "combined_agriculture_prices.csv")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "price_prediction", "artifacts")

NUMERIC_FEATURES = [
    "Year", "Avg_Temp_C", "Max_Temp_C", "Min_Temp_C",
    "Rainfall_mm", "Cumulative_Rainfall_mm", "Flood", "Drought",
    "Yield_per_Hectare", "Production_tonnes", "Area_Hectares",
    "Import_tonnes", "Export_tonnes", "Fertilizer_Cost", "Seed_Cost",
    "Labor_Cost", "Fuel_Cost", "Inflation", "CPI",
    "Lag1_Price", "Lag2_Price",
]

CATEGORICAL_FEATURES = ["Market", "Commodity", "Variety"]
TARGET = "Price_per_KG"

# VMD parameters
VMD_ALPHA = 2000       # bandwidth constraint
VMD_TAU = 0            # noise tolerance (0 = no noise)
VMD_K = 3              # number of modes (trend, seasonal, noise)
VMD_DC = 0             # no DC part
VMD_INIT = 1           # initialize omegas uniformly
VMD_TOL = 1e-7         # convergence tolerance

LOOKBACK = 6           # months of history fed to LSTM


# ---------------------------------------------------------------------------
# 1. Load and clean
# ---------------------------------------------------------------------------
def load_dataset(csv_path=CSV_PATH):
    """Load CSV, normalise Variety casing, fill missing values."""
    df = pd.read_csv(csv_path)
    return _clean_dataframe(df)


def load_dataset_from_db():
    """
    Load all CropPriceData rows from MySQL via Django ORM.
    Returns a pandas DataFrame with the same columns as the CSV loader.
    """
    from farmer.models import CropPriceData

    qs = CropPriceData.objects.all().values(
        "year", "month", "market", "commodity", "variety",
        "price_per_kg", "avg_temp_c", "max_temp_c", "min_temp_c",
        "rainfall_mm", "cumulative_rainfall_mm", "flood", "drought",
        "yield_per_hectare", "production_tonnes", "area_hectares",
        "import_tonnes", "export_tonnes", "fertilizer_cost", "seed_cost",
        "labor_cost", "fuel_cost", "inflation", "cpi",
        "lag1_price", "lag2_price",
    )
    if not qs.exists():
        raise ValueError("CropPriceData table is empty. Load data first with: python manage.py load_csv_to_db")

    df = pd.DataFrame(list(qs))

    # Rename DB fields back to the column names used everywhere else
    rename_map = {
        "year": "Year", "month": "Month", "market": "Market",
        "commodity": "Commodity", "variety": "Variety",
        "price_per_kg": "Price_per_KG",
        "avg_temp_c": "Avg_Temp_C", "max_temp_c": "Max_Temp_C",
        "min_temp_c": "Min_Temp_C", "rainfall_mm": "Rainfall_mm",
        "cumulative_rainfall_mm": "Cumulative_Rainfall_mm",
        "flood": "Flood", "drought": "Drought",
        "yield_per_hectare": "Yield_per_Hectare",
        "production_tonnes": "Production_tonnes",
        "area_hectares": "Area_Hectares",
        "import_tonnes": "Import_tonnes", "export_tonnes": "Export_tonnes",
        "fertilizer_cost": "Fertilizer_Cost", "seed_cost": "Seed_Cost",
        "labor_cost": "Labor_Cost", "fuel_cost": "Fuel_Cost",
        "inflation": "Inflation", "cpi": "CPI",
        "lag1_price": "Lag1_Price", "lag2_price": "Lag2_Price",
    }
    df.rename(columns=rename_map, inplace=True)
    return _clean_dataframe(df)


def _clean_dataframe(df):
    """Shared cleaning logic for both CSV and DB loaders."""
    df["Variety"] = df["Variety"].astype(str).str.strip().str.title().str.replace(" ", "_")

    df.sort_values(["Commodity", "Variety", "Market", "Year", "Month"], inplace=True)
    df[["CPI", "Lag1_Price", "Lag2_Price"]] = (
        df.groupby(["Commodity", "Variety", "Market"])[["CPI", "Lag1_Price", "Lag2_Price"]]
        .transform(lambda s: s.ffill().bfill())
    )
    df.fillna(df.median(numeric_only=True), inplace=True)
    return df


# ---------------------------------------------------------------------------
# 2. Cyclical month encoding
# ---------------------------------------------------------------------------
def add_cyclic_month(df):
    """Encode Month as sin/cos pair."""
    df = df.copy()
    df["Month_sin"] = np.sin(2 * np.pi * df["Month"] / 12)
    df["Month_cos"] = np.cos(2 * np.pi * df["Month"] / 12)
    return df


# ---------------------------------------------------------------------------
# 3. Categorical encoding
# ---------------------------------------------------------------------------
def fit_label_encoders(df):
    """Fit LabelEncoders on categorical columns; return encoders dict."""
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        le.fit(df[col])
        encoders[col] = le
    return encoders


def apply_label_encoders(df, encoders):
    """Transform categorical columns using fitted encoders."""
    df = df.copy()
    for col, le in encoders.items():
        df[col] = le.transform(df[col])
    return df


# ---------------------------------------------------------------------------
# 4. Feature scaling
# ---------------------------------------------------------------------------
def fit_scalers(df, feature_cols, target_col=TARGET):
    """Fit MinMaxScalers on features and target separately."""
    feat_scaler = MinMaxScaler()
    feat_scaler.fit(df[feature_cols].values)

    tgt_scaler = MinMaxScaler()
    tgt_scaler.fit(df[[target_col]].values)

    return feat_scaler, tgt_scaler


def apply_scalers(df, feature_cols, feat_scaler, tgt_scaler, target_col=TARGET):
    """Scale features and target using fitted scalers."""
    df = df.copy()
    df[feature_cols] = feat_scaler.transform(df[feature_cols].values)
    df[target_col] = tgt_scaler.transform(df[[target_col]].values)
    return df


# ---------------------------------------------------------------------------
# 5. VMD decomposition
# ---------------------------------------------------------------------------
def decompose_vmd(price_series):
    """
    Apply VMD to a 1-D price series.
    Returns K modes as np.ndarray of shape (K, T).
    """
    signal = price_series.values.astype(np.float64)
    # VMD needs at least a few dozen points
    if len(signal) < 20:
        # fallback: return the signal repeated K times
        return np.tile(signal, (VMD_K, 1))

    modes, _, _ = VMD(signal, VMD_ALPHA, VMD_TAU, VMD_K, VMD_DC, VMD_INIT, VMD_TOL)
    return modes  # shape (K, T)


# ---------------------------------------------------------------------------
# 6. LSTM windowing
# ---------------------------------------------------------------------------
def create_sequences(features, target, lookback=LOOKBACK):
    """
    Slide a window of `lookback` steps over feature matrix and target vector.
    Returns X (samples, lookback, n_features), y (samples,).
    """
    X, y = [], []
    for i in range(lookback, len(features)):
        X.append(features[i - lookback: i])
        y.append(target[i])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


# ---------------------------------------------------------------------------
# 7. Full preprocessing pipeline (for training)
# ---------------------------------------------------------------------------
def build_feature_columns():
    """Return the ordered list of feature column names used by the model."""
    return CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["Month_sin", "Month_cos"]


def preprocess_for_training(csv_path=CSV_PATH, source="csv"):
    """
    End-to-end preprocessing. Returns:
      groups : dict  {(commodity, variety, market): (X, y)}  — LSTM-ready data
      encoders, feat_scaler, tgt_scaler — saved artifacts for inference
      df_processed — the fully processed DataFrame

    source: "csv" to load from CSV file, "db" to load from MySQL.
    """
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    if source == "db":
        df = load_dataset_from_db()
    else:
        df = load_dataset(csv_path)
    df = add_cyclic_month(df)

    # Fit & apply label encoders
    encoders = fit_label_encoders(df)
    df = apply_label_encoders(df, encoders)

    feature_cols = build_feature_columns()

    # Fit & apply scalers
    feat_scaler, tgt_scaler = fit_scalers(df, feature_cols)
    df = apply_scalers(df, feature_cols, feat_scaler, tgt_scaler)

    # Build per-group sequences (one series per commodity/variety/market combo)
    groups = {}
    for (comm, var, mkt), grp in df.groupby(["Commodity", "Variety", "Market"]):
        grp = grp.sort_values(["Year", "Month"])
        price_series_raw = grp[TARGET].values

        # VMD decomposition — append modes as extra features
        modes = decompose_vmd(pd.Series(price_series_raw))
        mode_df = pd.DataFrame(modes.T, columns=[f"vmd_{i}" for i in range(modes.shape[0])])
        mode_df.index = grp.index

        # Combine features + VMD modes
        feat_matrix = np.hstack([grp[feature_cols].values, mode_df.values])
        target_vec = grp[TARGET].values

        X, y = create_sequences(feat_matrix, target_vec, LOOKBACK)
        if len(X) > 0:
            groups[(comm, var, mkt)] = (X, y)

    # Persist artifacts
    joblib.dump(encoders, os.path.join(ARTIFACTS_DIR, "label_encoders.pkl"))
    joblib.dump(feat_scaler, os.path.join(ARTIFACTS_DIR, "feature_scaler.pkl"))
    joblib.dump(tgt_scaler, os.path.join(ARTIFACTS_DIR, "target_scaler.pkl"))

    return groups, encoders, feat_scaler, tgt_scaler, df
