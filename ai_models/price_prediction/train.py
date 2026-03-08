"""
Full training pipeline for the VMD-LSTM crop price predictor.
Orchestrates: preprocessing → VMD → GA hyper-parameter search → final training → artefact saving.
"""

import os
import json
import numpy as np
import torch
import joblib

from .preprocessing import (
    preprocess_for_training,
    ARTIFACTS_DIR,
    LOOKBACK,
    VMD_K,
    build_feature_columns,
)
from .ga_optimizer import run_ga
from .model import PriceLSTM

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

TRAIN_RATIO = 0.85  # 85 % train, 15 % validation


def _split(X, y, ratio=TRAIN_RATIO):
    n = int(len(X) * ratio)
    return X[:n], y[:n], X[n:], y[n:]


def evaluate_metrics(y_true, y_pred):
    """Return RMSE, MAE, MAPE."""
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    # Avoid division by zero for MAPE
    nonzero = np.abs(y_true) > 1e-8
    if nonzero.sum() > 0:
        mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100)
    else:
        mape = 0.0
    return {"rmse": rmse, "mae": mae, "mape_pct": mape}


def train_all(csv_path=None, source="csv", ga_pop=8, ga_gen=5, verbose=True):
    """
    Main entry point for training.
    Trains one global LSTM on all groups combined.
    Saves: model weights, best hyper-params, evaluation metrics.

    source: "csv" to read from CSV file, "db" to read from MySQL.
    """
    from .preprocessing import CSV_PATH
    csv_path = csv_path or CSV_PATH

    if verbose:
        print(f"[1/4] Preprocessing dataset (source={source}) …")
    groups, encoders, feat_scaler, tgt_scaler, df_processed = preprocess_for_training(
        csv_path=csv_path, source=source,
    )

    # Combine all group data into one large dataset
    all_X, all_y = [], []
    for (X, y) in groups.values():
        all_X.append(X)
        all_y.append(y)
    all_X = np.concatenate(all_X, axis=0)
    all_y = np.concatenate(all_y, axis=0)

    if verbose:
        print(f"   Total sequences: {all_X.shape[0]}  features/step: {all_X.shape[2]}")

    X_train, y_train, X_val, y_val = _split(all_X, all_y)

    if verbose:
        print(f"   Train: {X_train.shape[0]}  Val: {X_val.shape[0]}")

    # --------------- GA hyper-parameter search ---------------
    if verbose:
        print("[2/4] Running Genetic Algorithm hyper-parameter search …")
    best_params, best_model, best_rmse = run_ga(
        X_train, y_train, X_val, y_val,
        population_size=ga_pop,
        generations=ga_gen,
        verbose=verbose,
    )

    # --------------- Final evaluation ---------------
    if verbose:
        print("[3/4] Evaluating best model …")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    best_model.eval()
    with torch.no_grad():
        preds_val = best_model(
            torch.tensor(X_val, dtype=torch.float32).to(device)
        ).cpu().numpy()

    metrics = evaluate_metrics(y_val, preds_val)
    if verbose:
        print(f"   Metrics — RMSE: {metrics['rmse']:.5f}  MAE: {metrics['mae']:.5f}  MAPE: {metrics['mape_pct']:.2f}%")

    # --------------- Save artefacts ---------------
    if verbose:
        print("[4/4] Saving artefacts …")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    torch.save(best_model.state_dict(), os.path.join(ARTIFACTS_DIR, "lstm_model.pt"))

    meta = {
        "best_params": best_params,
        "metrics": metrics,
        "input_size": int(all_X.shape[2]),
        "lookback": LOOKBACK,
        "vmd_k": VMD_K,
        "feature_cols": build_feature_columns(),
    }
    with open(os.path.join(ARTIFACTS_DIR, "model_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    if verbose:
        print("   Done ✓  Artefacts saved to", ARTIFACTS_DIR)

    return best_model, meta
